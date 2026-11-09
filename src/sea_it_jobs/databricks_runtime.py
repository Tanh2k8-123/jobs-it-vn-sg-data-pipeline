"""Databricks Free Edition: Volume -> Delta Bronze -> shared SQL -> Gold.

Run inside a notebook with the Spark session provided by Databricks.
Do not install PySpark or create a separate SparkSession on serverless compute.
"""

import csv
import json
import re
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from graphlib import TopologicalSorter
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import yaml
from jinja2 import Environment, StrictUndefined

from sea_it_jobs.config import read_boards, safe_token
from sea_it_jobs.lever import LeverClient
from sea_it_jobs.snapshots import RUN_FIELDS, collect_snapshot, read_snapshot


def identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", value):
        raise ValueError(f"Use letters, numbers and underscores for identifiers: {value!r}")
    return value


@dataclass(frozen=True)
class Lakehouse:
    repo_root: Path
    catalog: str = "workspace"
    prefix: str = "tech_jobs"
    volume: str = "raw_snapshots"

    def __post_init__(self):
        for value in [self.catalog, self.prefix, self.volume]:
            identifier(value)
        if not (self.repo_root / "config/boards.csv").is_file():
            raise ValueError("repo_root must contain config/boards.csv and the project source")

    def schema(self, layer):
        return f"{self.prefix}_{layer}"

    def table(self, name, layer="gold"):
        return f"`{self.catalog}`.`{self.schema(layer)}`.`{identifier(name)}`"

    @property
    def volume_path(self):
        return Path(f"/Volumes/{self.catalog}/{self.schema('bronze')}/{self.volume}")


TYPES = {
    "snapshot_date": "DATE",
    "started_at": "TIMESTAMP",
    "completed_at": "TIMESTAMP",
    "fetched_at": "TIMESTAMP",
    "record_count": "BIGINT",
    "page_count": "BIGINT",
}
ENVELOPE_SCHEMA = ", ".join(f"{field} {TYPES.get(field, 'STRING')}" for field in RUN_FIELDS)
ENVELOPE_SCHEMA += ", postings ARRAY<STRUCT<job_id: STRING, posting_json: STRING>>"


def setup(spark, lake: Lakehouse):
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    for layer in ["bronze", "silver", "gold"]:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{lake.catalog}`.`{lake.schema(layer)}`")
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {lake.table(lake.volume, 'bronze')}")
    envelopes = lake.table("snapshot_envelopes", "bronze")
    # One row holds metadata and postings so one MERGE commits both atomically.
    spark.sql(f"""CREATE TABLE IF NOT EXISTS {envelopes} ({ENVELOPE_SCHEMA})
        USING DELTA CLUSTER BY (snapshot_date, board_slug)""")
    fields = ", ".join(RUN_FIELDS)
    spark.sql(
        f"CREATE OR REPLACE VIEW {lake.table('ingestion_runs', 'bronze')} "
        f"AS SELECT {fields} FROM {envelopes}"
    )
    spark.sql(f"""CREATE OR REPLACE VIEW {lake.table("raw_postings", "bronze")} AS
        SELECT e.run_id, e.board_slug, e.snapshot_date, e.fetched_at,
               p.job_id, p.posting_json
        FROM {envelopes} e LATERAL VIEW explode(e.postings) items AS p
        WHERE e.status='success' AND e.extraction_status='complete'""")


def copy_snapshot(folder: Path, lake: Lakehouse):
    manifest, _ = read_snapshot(folder)
    destination = (
        lake.volume_path
        / "lever"
        / manifest["board_slug"]
        / f"snapshot_date={manifest['snapshot_date']}"
        / f"run_id={manifest['run_id']}"
    )
    destination.mkdir(parents=True, exist_ok=True)
    for name in ["postings.json", "manifest.json"]:
        data = (folder / name).read_bytes()
        output = destination / name
        if output.exists():
            if output.read_bytes() != data:
                raise ValueError(f"Existing snapshot differs: {output}")
        else:
            output.write_bytes(data)
    return destination


def extract_to_volume(lake: Lakehouse, run_id: str):
    safe_token(run_id)
    day = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date().isoformat()
    client = LeverClient()
    try:
        with tempfile.TemporaryDirectory() as directory:
            for board in read_boards(lake.repo_root / "config/boards.csv"):
                if board.enabled:
                    folder, manifest = collect_snapshot(client, board, Path(directory), run_id, day)
                    copy_snapshot(folder, lake)
                    print(board.board_slug, manifest["status"], manifest["record_count"])
    finally:
        client.close()


def envelope_row(manifest: dict, postings: list):
    row = {field: manifest[field] for field in RUN_FIELDS}
    row["snapshot_date"] = date.fromisoformat(row["snapshot_date"])
    for field in ["started_at", "completed_at", "fetched_at"]:
        row[field] = datetime.fromisoformat(row[field])
    row["postings"] = (
        [{"job_id": p["id"], "posting_json": json.dumps(p, ensure_ascii=False)} for p in postings]
        if manifest["status"] == "success"
        else []
    )
    # Serverless limits row size; the monitored boards currently have small payloads.
    if sum(len(p["posting_json"].encode()) for p in row["postings"]) > 100_000_000:
        raise ValueError("Snapshot exceeds the 100 MB per-board guard; use chunked ingestion")
    return row


def load_bronze(spark, lake: Lakehouse):
    manifests = sorted(lake.volume_path.glob("lever/*/snapshot_date=*/run_id=*/manifest.json"))
    if not manifests:
        raise ValueError("No snapshots in Volume. Upload local snapshots or select source_mode=api")
    table = lake.table("snapshot_envelopes", "bronze")
    existing = {
        (r["board_slug"], r["run_id"]): (r["sha256"], r["snapshot_date"], r["status"])
        for r in spark.sql(
            f"SELECT board_slug, run_id, sha256, snapshot_date, status FROM {table}"
        ).collect()
    }
    loaded = 0
    for path in manifests:
        manifest, postings = read_snapshot(path.parent)
        row = envelope_row(manifest, postings)
        key = row["board_slug"], row["run_id"]
        signature = row["sha256"], row["snapshot_date"], row["status"]
        if key in existing:
            if existing[key] != signature:
                raise ValueError(f"Immutable Delta run differs: {key}")
            continue
        spark.createDataFrame([row], schema=ENVELOPE_SCHEMA).createOrReplaceTempView(
            "tech_jobs_incoming_snapshot"
        )
        spark.sql(f"""MERGE INTO {table} t USING tech_jobs_incoming_snapshot s
            ON t.board_slug=s.board_slug AND t.run_id=s.run_id
            WHEN NOT MATCHED THEN INSERT *""")
        existing[key] = signature
        loaded += 1
    print(f"Loaded {loaded} new snapshot envelopes; existing runs remain unchanged.")
    return loaded


def load_seeds(spark, lake: Lakehouse):
    boards = read_boards(lake.repo_root / "config/boards.csv")
    seeds = {
        "companies": (
            [
                {
                    "board_slug": b.board_slug,
                    "company_name": b.company_name,
                    "enabled": b.enabled,
                    "target_markets": b.target_markets,
                }
                for b in boards
            ],
            "board_slug STRING, company_name STRING, enabled BOOLEAN, target_markets STRING",
        ),
    }
    for name, schema in [
        ("country_location_rules", "country_code STRING, location_pattern STRING"),
        ("role_rules", "priority BIGINT, role_category STRING, title_pattern STRING"),
    ]:
        with (lake.repo_root / f"dbt/seeds/{name}.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            rows = list(csv.DictReader(stream))
        if name == "role_rules":
            for row in rows:
                row["priority"] = int(row["priority"])
        seeds[name] = rows, schema
    for name, (rows, schema) in seeds.items():
        spark.createDataFrame(rows, schema=schema).createOrReplaceTempView("tech_jobs_seed")
        spark.sql(
            f"CREATE OR REPLACE TABLE {lake.table(name, 'silver')} USING DELTA "
            "AS SELECT * FROM tech_jobs_seed"
        )


def model_files(lake: Lakehouse):
    return {path.stem: path for path in (lake.repo_root / "dbt/models").rglob("*.sql")}


def model_relation(lake: Lakehouse, name: str):
    files = model_files(lake)
    layer = "gold" if name in files and files[name].parent.name == "marts" else "silver"
    return lake.table(name, layer)


def render_sql(lake: Lakehouse, text: str):
    options = {}

    def config(**kwargs):
        options.update(kwargs)
        return ""

    context = {
        "target": SimpleNamespace(type="databricks"),
        "config": config,
        "ref": lambda name: model_relation(lake, name),
        "source": lambda source, name: lake.table(name, "bronze"),
        "dbt": SimpleNamespace(type_string=lambda: "string"),
    }
    environment = Environment(undefined=StrictUndefined)
    macros = environment.from_string(
        (lake.repo_root / "dbt/macros/portable.sql").read_text(encoding="utf-8")
    ).make_module(context)
    for name in ["json_text", "json_string_array", "unnest_locations", "matches", "daily_table"]:
        context[name] = getattr(macros, name)
    return environment.from_string(text).render(context).strip(), options


def compiled_models(lake: Lakehouse):
    files = model_files(lake)
    dependencies = {
        name: set(re.findall(r"ref\(['\"]([^'\"]+)['\"]\)", path.read_text(encoding="utf-8")))
        & set(files)
        for name, path in files.items()
    }
    result = []
    for name in TopologicalSorter(dependencies).static_order():
        path = files[name]
        sql, options = render_sql(lake, path.read_text(encoding="utf-8"))
        materialized = options.get(
            "materialized", "table" if path.parent.name == "marts" else "view"
        )
        relation = model_relation(lake, name)
        if materialized == "table":
            cluster = " CLUSTER BY (snapshot_date)" if name != "dim_company" else ""
            ddl = f"CREATE OR REPLACE TABLE {relation} USING DELTA{cluster} AS {sql}"
        else:
            ddl = f"CREATE OR REPLACE VIEW {relation} AS {sql}"
        result.append((name, ddl))
    return result


def transform(spark, lake: Lakehouse):
    load_seeds(spark, lake)
    for name, sql in compiled_models(lake):
        print(f"Building {name}")
        spark.sql(sql)


def quality_queries(lake: Lakehouse):
    checks = {}
    schema = yaml.safe_load((lake.repo_root / "dbt/models/schema.yml").read_text(encoding="utf-8"))
    for model in schema["models"]:
        relation = model_relation(lake, model["name"])
        for column in model["columns"]:
            col = identifier(column["name"])
            for test in column.get("tests", []):
                name = test if isinstance(test, str) else next(iter(test))
                args = {} if isinstance(test, str) else test[name].get("arguments", {})
                if name == "unique":
                    sql = (
                        f"SELECT {col} FROM {relation} WHERE {col} IS NOT NULL "
                        f"GROUP BY {col} HAVING count(*)>1"
                    )
                elif name == "not_null":
                    sql = f"SELECT {col} FROM {relation} WHERE {col} IS NULL"
                elif name == "accepted_values":
                    values = ",".join("'" + str(v).replace("'", "''") + "'" for v in args["values"])
                    sql = f"SELECT {col} FROM {relation} WHERE {col} NOT IN ({values})"
                elif name == "relationships":
                    match = re.fullmatch(r"ref\('([^']+)'\)", args["to"])
                    if not match:
                        raise ValueError("Unsupported relationship reference")
                    parent = model_relation(lake, match[1])
                    field = identifier(args["field"])
                    sql = (
                        f"SELECT c.{col} FROM {relation} c LEFT JOIN {parent} p "
                        f"ON c.{col}=p.{field} WHERE c.{col} IS NOT NULL AND p.{field} IS NULL"
                    )
                else:
                    raise ValueError(f"Unsupported data test: {name}")
                checks[f"{model['name']}.{col}.{name}"] = sql
    for path in (lake.repo_root / "dbt/tests").glob("*.sql"):
        checks[path.stem] = render_sql(lake, path.read_text(encoding="utf-8"))[0]
    return checks


def check_quality(spark, lake: Lakehouse, require_fresh: bool = True):
    failed = []
    for name, sql in quality_queries(lake).items():
        bad_rows = spark.sql(sql).limit(1).collect()
        print(name, "FAIL" if bad_rows else "PASS")
        if bad_rows:
            failed.append(name)
    latest = spark.sql(
        f"SELECT max(snapshot_date) AS day FROM {lake.table('mart_daily_overview')}"
    ).first()["day"]
    today = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()
    if require_fresh and latest != today:
        failed.append(f"Freshness: latest observation {latest}, expected {today}")
    unavailable = spark.sql(f"""SELECT company_name FROM {lake.table("mart_source_health")}
        WHERE snapshot_date=(SELECT max(snapshot_date) FROM {lake.table("mart_source_health")})
          AND (snapshot_status != 'complete' OR latest_attempt_status != 'success')""").collect()
    failed.extend(f"Source failed/missing: {row['company_name']}" for row in unavailable)
    if failed:
        raise RuntimeError("; ".join(failed))
    print("All data checks, source coverage and freshness checks passed.")
