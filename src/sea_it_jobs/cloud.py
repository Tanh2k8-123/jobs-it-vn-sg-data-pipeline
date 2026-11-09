"""Lazy cloud imports allow a complete local run without GCP credentials."""

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from sea_it_jobs.config import Settings
from sea_it_jobs.snapshots import RUN_FIELDS, raw_rows, read_snapshot
from sea_it_jobs.warehouse import RAW_FIELDS


def validate_cloud(settings: Settings):
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", settings.project):
        raise ValueError("Set a valid GCP_PROJECT_ID")
    if not settings.bucket:
        raise ValueError("Set GCS_BUCKET")


def upload_snapshot(folder: Path, settings: Settings) -> str:
    from google.api_core.exceptions import PreconditionFailed
    from google.cloud import storage

    validate_cloud(settings)
    manifest, _ = read_snapshot(folder)
    prefix = (
        f"lever/{manifest['board_slug']}/snapshot_date={manifest['snapshot_date']}/"
        f"run_id={manifest['run_id']}"
    )
    bucket = storage.Client(project=settings.project).bucket(settings.bucket)
    for filename in ["postings.json", "manifest.json"]:
        data = (folder / filename).read_bytes()
        blob = bucket.blob(f"{prefix}/{filename}")
        try:
            blob.upload_from_string(data, content_type="application/json", if_generation_match=0)
        except PreconditionFailed:
            if blob.download_as_bytes() != data:
                raise ValueError(f"Immutable GCS snapshot differs: {blob.name}") from None
    return f"gs://{settings.bucket}/{prefix}"


def load_bigquery(folder: Path, settings: Settings):
    from google.cloud import bigquery

    validate_cloud(settings)
    manifest, postings = read_snapshot(folder)
    client = bigquery.Client(project=settings.project, location=settings.location)
    dataset = f"{settings.project}.{settings.raw_dataset}"
    type_map = {
        "snapshot_date": "DATE",
        "fetched_at": "TIMESTAMP",
        "started_at": "TIMESTAMP",
        "completed_at": "TIMESTAMP",
        "record_count": "INTEGER",
        "page_count": "INTEGER",
    }
    staging = {}
    try:
        for name, fields, rows in [
            ("raw_postings", RAW_FIELDS, raw_rows(manifest, postings)),
            ("ingestion_runs", RUN_FIELDS, [{k: manifest[k] for k in RUN_FIELDS}]),
        ]:
            table_id = f"{dataset}._load_{name}_{uuid4().hex}"
            staging[name] = table_id
            schema = [bigquery.SchemaField(k, type_map.get(k, "STRING")) for k in fields]
            table = bigquery.Table(table_id, schema=schema)
            table.expires = datetime.now(timezone.utc) + timedelta(hours=1)
            client.create_table(table)
            if rows:
                client.load_table_from_json(
                    rows, table_id, job_config=bigquery.LoadJobConfig(schema=schema)
                ).result()
        sql = f"""
        ASSERT NOT EXISTS (
          SELECT 1 FROM `{dataset}.ingestion_runs`
          WHERE board_slug=@board AND run_id=@run
            AND (sha256 != @checksum OR snapshot_date != @day OR status != @status)
        ) AS 'Run id already exists with different content';
        BEGIN TRANSACTION;
        DELETE FROM `{dataset}.raw_postings` WHERE board_slug=@board AND run_id=@run
          AND snapshot_date=@day;
        INSERT INTO `{dataset}.raw_postings` ({", ".join(RAW_FIELDS)})
          SELECT {", ".join(RAW_FIELDS)} FROM `{staging["raw_postings"]}`;
        DELETE FROM `{dataset}.ingestion_runs` WHERE board_slug=@board AND run_id=@run
          AND snapshot_date=@day;
        INSERT INTO `{dataset}.ingestion_runs` ({", ".join(RUN_FIELDS)})
          SELECT {", ".join(RUN_FIELDS)} FROM `{staging["ingestion_runs"]}`;
        COMMIT TRANSACTION;
        """
        config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("board", "STRING", manifest["board_slug"]),
                bigquery.ScalarQueryParameter("run", "STRING", manifest["run_id"]),
                bigquery.ScalarQueryParameter("day", "DATE", manifest["snapshot_date"]),
                bigquery.ScalarQueryParameter("checksum", "STRING", manifest["sha256"]),
                bigquery.ScalarQueryParameter("status", "STRING", manifest["status"]),
            ]
        )
        client.query(sql, job_config=config).result()
    finally:
        for table in staging.values():
            client.delete_table(table, not_found_ok=True)
    return manifest


def download_snapshot(uri: str, root: Path, settings: Settings) -> Path:
    from google.cloud import storage

    match = re.fullmatch(
        r"gs://([^/]+)/(lever/[^/]+/snapshot_date=\d{4}-\d{2}-\d{2}/run_id=[^/]+)", uri
    )
    if not match:
        raise ValueError("Expected a gs://bucket/lever/board/snapshot_date=.../run_id=... URI")
    bucket_name, prefix = match.groups()
    bucket = storage.Client(project=settings.project).bucket(bucket_name)
    # Use an isolated download directory; validate manifest identifiers before loading.
    destination = root / "replay" / uuid4().hex
    destination.mkdir(parents=True)
    for filename in ["postings.json", "manifest.json"]:
        (destination / filename).write_bytes(
            bucket.blob(f"{prefix}/{filename}").download_as_bytes()
        )
    read_snapshot(destination)
    return destination
