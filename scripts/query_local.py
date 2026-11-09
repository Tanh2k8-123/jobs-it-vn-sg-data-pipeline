"""Explore DuckDB data with read-only SQL from the project directory.

Example: uv run python scripts/query_local.py --table countries
       uv run python scripts/query_local.py --sql "select count(*) from raw.raw_postings"
"""

import argparse
import sys
from pathlib import Path

import duckdb

from sea_it_jobs.config import Settings

# Keep preset results narrow; use --sql to inspect other columns.
QUERIES = {
    "overview": (
        "select snapshot_date, tech_postings, successful_boards, expected_boards "
        "from analytics.mart_daily_overview order by snapshot_date desc"
    ),
    "countries": (
        "select snapshot_date, country_code, tech_postings "
        "from analytics.mart_daily_country order by snapshot_date desc, country_code"
    ),
    "roles": (
        "select snapshot_date, country_code, role_category, tech_postings "
        "from analytics.mart_daily_roles order by snapshot_date desc, tech_postings desc"
    ),
    "companies": (
        "select snapshot_date, company_name, tech_postings, snapshot_status "
        "from analytics.mart_daily_company order by snapshot_date desc, company_name"
    ),
    "sources": (
        "select snapshot_date, company_name, snapshot_status, latest_attempt_status "
        "from analytics.mart_source_health order by snapshot_date desc, company_name"
    ),
    "postings": (
        "select snapshot_date, board_slug, job_title, role_category "
        "from analytics.fct_job_snapshots order by snapshot_date desc, board_slug"
    ),
    "runs": (
        "select snapshot_date, board_slug, run_id, status, record_count "
        "from raw.ingestion_runs order by snapshot_date desc, board_slug"
    ),
}


def main():
    parser = argparse.ArgumentParser(description="Inspect local tables or run read-only SQL.")
    query = parser.add_mutually_exclusive_group()
    query.add_argument("--table", choices=QUERIES, help="Select a table by its short name.")
    query.add_argument("--sql", help="SQL query to practice with.")
    parser.add_argument("--demo", action="store_true", help="Read synthetic data from data/demo.")
    parser.add_argument(
        "--limit", type=int, default=20, help="Maximum displayed rows; default: 20."
    )
    args = parser.parse_args()
    if not 1 <= args.limit <= 1000:
        parser.error("--limit must be between 1 and 1000")

    settings = Settings.from_env()
    database = Path("data/demo/warehouse.duckdb") if args.demo else settings.duckdb_path
    if not database.is_file():
        command = "demo" if args.demo else "pipeline --target local"
        print(f"Database not found: {database}", file=sys.stderr)
        print(f"Run first: uv run sea-it-jobs {command}", file=sys.stderr)
        return 1

    sql = args.sql or QUERIES[args.table or "overview"]
    try:
        # Read-only mode lets learners explore without changing loaded tables.
        with duckdb.connect(str(database), read_only=True) as connection:
            result = connection.sql(sql).limit(args.limit).df()
        print(f"Database: {database}")
        print(f"SQL: {sql}\n")
        display = result.astype(object).where(result.notna(), "NULL")
        if "snapshot_date" in display:
            display["snapshot_date"] = display["snapshot_date"].astype(str).str[:10]
        print(display.to_string(index=False) if not result.empty else "No matching rows.")
        print(f"\nShowing at most {args.limit} rows. NULL means no value is available.")
        return 0
    except duckdb.Error as error:
        print(f"Could not read data: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
