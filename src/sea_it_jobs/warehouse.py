"""A run is visible to dbt only after its postings and run metadata commit together."""

from pathlib import Path

import duckdb

from sea_it_jobs.snapshots import RUN_FIELDS, raw_rows, read_snapshot

RAW_FIELDS = ["run_id", "board_slug", "snapshot_date", "fetched_at", "job_id", "posting_json"]


def init_local(connection):
    connection.execute("create schema if not exists raw")
    connection.execute("""
        create table if not exists raw.raw_postings (
            run_id varchar, board_slug varchar, snapshot_date date, fetched_at timestamptz,
            job_id varchar, posting_json varchar,
            primary key (board_slug, run_id, job_id)
        )
    """)
    connection.execute("""
        create table if not exists raw.ingestion_runs (
            run_id varchar, board_slug varchar, snapshot_date date,
            started_at timestamptz, completed_at timestamptz, fetched_at timestamptz,
            status varchar, extraction_status varchar, record_count bigint, page_count bigint,
            error_message varchar, sha256 varchar, primary key (board_slug, run_id)
        )
    """)


def load_local(folder: Path, db_path: Path):
    """Load a snapshot into DuckDB without duplicating a previously loaded run."""
    manifest, postings = read_snapshot(folder)
    rows = raw_rows(manifest, postings)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as connection:
        init_local(connection)
        # Commit postings and run status together in one transaction.
        connection.begin()
        try:
            key = [manifest["board_slug"], manifest["run_id"]]
            existing = connection.execute(
                "select sha256, snapshot_date, status from raw.ingestion_runs "
                "where board_slug=? and run_id=?",
                key,
            ).fetchone()
            if existing and (
                existing[0] != manifest["sha256"]
                or str(existing[1]) != manifest["snapshot_date"]
                or existing[2] != manifest["status"]
            ):
                raise ValueError("Run id already exists with different content")
            connection.execute("delete from raw.raw_postings where board_slug=? and run_id=?", key)
            if rows:
                connection.executemany(
                    "insert into raw.raw_postings values (?, ?, ?, ?, ?, ?)",
                    [[row[k] for k in RAW_FIELDS] for row in rows],
                )
            connection.execute(
                "delete from raw.ingestion_runs where board_slug=? and run_id=?", key
            )
            connection.execute(
                "insert into raw.ingestion_runs values (" + ",".join(["?"] * len(RUN_FIELDS)) + ")",
                [manifest[k] for k in RUN_FIELDS],
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    return manifest
