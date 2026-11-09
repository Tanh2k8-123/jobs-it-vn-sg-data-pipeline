import os
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import duckdb
from streamlit.testing.v1 import AppTest

from sea_it_jobs.cli import transform
from sea_it_jobs.config import Settings, read_boards
from sea_it_jobs.demo import create_demo
from sea_it_jobs.lever import Extraction, ExtractionError
from sea_it_jobs.snapshots import collect_snapshot
from sea_it_jobs.warehouse import load_local


def test_models_multicountry_coverage_replay_and_latest_run(tmp_path):
    settings = replace(
        Settings.from_env(), data_dir=tmp_path / "demo", duckdb_path=tmp_path / "warehouse.duckdb"
    )
    create_demo(settings)
    create_demo(settings)  # A second ingestion must not double any observation.
    boards = {b.board_slug: b for b in read_boards(Path("config/boards.csv"))}

    def all_fail(_):
        raise ExtractionError("All sources unavailable")

    for board in boards.values():
        folder, _ = collect_snapshot(
            SimpleNamespace(fetch=all_fail),
            board,
            settings.data_dir,
            "all_failed",
            "2026-01-03",
        )
        load_local(folder, settings.duckdb_path)
    transform(settings, "local")
    with duckdb.connect(str(settings.duckdb_path)) as connection:
        assert connection.execute("""
            select tech_postings, successful_boards from analytics.mart_daily_overview
            order by snapshot_date
        """).fetchall() == [(4, 4), (4, 3), (None, 0)]
        assert connection.execute("""
            select country_code, tech_postings from analytics.mart_daily_country
            where snapshot_date='2026-01-01' order by country_code
        """).fetchall() == [("SG", 2), ("VN", 3)]
        assert (
            connection.execute("""
            select role_category from analytics.fct_job_snapshots
            where job_id='demo-finance' limit 1
        """).fetchone()[0]
            == "Unclassified"
        )
        assert connection.execute("""
            select distinct role_category from analytics.fct_job_snapshots
            where job_id='demo-multi'
        """).fetchall() == [("Software Engineering",)]
    # A newer successful empty snapshot replaces the previous nonempty snapshot.
    boards = {b.board_slug: b for b in read_boards(Path("config/boards.csv"))}
    folder, _ = collect_snapshot(
        SimpleNamespace(fetch=lambda _: Extraction([], 1)),
        boards["shopback-2"],
        settings.data_dir,
        "new_empty_success",
        "2026-01-02",
    )
    load_local(folder, settings.duckdb_path)

    def fail(_):
        raise ExtractionError("Later failure must not remove earlier successful Portcast data")

    folder, _ = collect_snapshot(
        SimpleNamespace(fetch=fail),
        boards["portcast"],
        settings.data_dir,
        "later_failure",
        "2026-01-02",
    )
    load_local(folder, settings.duckdb_path)
    transform(settings, "local")
    with duckdb.connect(str(settings.duckdb_path)) as connection:
        assert (
            connection.execute("""
            select tech_postings from analytics.mart_daily_overview
            where snapshot_date='2026-01-02'
        """).fetchone()[0]
            == 1
        )
        assert connection.execute("""
            select snapshot_status, latest_attempt_status from analytics.mart_source_health
            where snapshot_date='2026-01-02' and board_slug='portcast'
        """).fetchone() == ("complete", "failed")
    assert (settings.data_dir / "dashboard/current.json").exists()
    with patch.dict(os.environ, {"DATA_DIR": str(settings.data_dir)}):
        app = AppTest.from_file(str(Path("dashboard/app.py").resolve())).run(timeout=45)
        assert not app.exception
        assert app.metric[0].value == "Unavailable"
