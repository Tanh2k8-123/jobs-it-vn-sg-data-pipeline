"""Export a consistent generation so dashboard readers never hold DuckDB locks."""

import json
from uuid import uuid4

import duckdb

from sea_it_jobs.config import Settings
from sea_it_jobs.snapshots import utc_now

MARTS = [
    "mart_daily_overview",
    "mart_daily_country",
    "mart_daily_roles",
    "mart_daily_company",
    "mart_source_health",
    "fct_job_snapshots",
    "bridge_job_country",
]


def export_marts(settings: Settings):
    root = settings.data_dir / "dashboard"
    generation = uuid4().hex
    output = root / generation
    output.mkdir(parents=True)
    with duckdb.connect(str(settings.duckdb_path), read_only=True) as connection:
        for name in MARTS:
            connection.execute(f"select * from analytics.{name}").df().to_csv(
                output / f"{name}.csv", index=False
            )
    metadata = {
        "generation": generation,
        "generated_at": utc_now(),
        "synthetic": settings.data_dir.name == "demo",
        "tables": MARTS,
    }
    temporary = root / f"current.{generation}.tmp"
    temporary.write_text(json.dumps(metadata), encoding="utf-8")
    temporary.replace(root / "current.json")
