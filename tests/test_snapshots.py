import json
from types import SimpleNamespace

import duckdb
import pytest

from sea_it_jobs.config import Board, safe_token
from sea_it_jobs.lever import Extraction, ExtractionError
from sea_it_jobs.snapshots import collect_snapshot, read_snapshot
from sea_it_jobs.warehouse import load_local


def snapshot(tmp_path, postings=None, failure=False, run="test_run"):
    def fetch(_):
        if failure:
            raise ExtractionError("Synthetic failure", [{"id": "partial"}], 1)
        return Extraction(postings if postings is not None else [{"id": "job1"}], 2)

    return collect_snapshot(
        SimpleNamespace(fetch=fetch),
        Board("testboard", "Test", True, "VN"),
        tmp_path,
        run,
        "2026-11-04",
    )


def test_replay_is_idempotent(tmp_path):
    folder, _ = snapshot(tmp_path)
    db = tmp_path / "test.duckdb"
    load_local(folder, db)
    load_local(folder, db)
    with duckdb.connect(str(db)) as connection:
        assert connection.execute("select count(*) from raw.raw_postings").fetchone()[0] == 1
        assert connection.execute("select count(*) from raw.ingestion_runs").fetchone()[0] == 1


def test_failed_partial_extraction_is_recorded_but_not_loaded(tmp_path):
    folder, manifest = snapshot(tmp_path, failure=True)
    assert manifest["status"] == "failed"
    assert manifest["record_count"] == 1
    db = tmp_path / "test.duckdb"
    load_local(folder, db)
    with duckdb.connect(str(db)) as connection:
        assert connection.execute("select count(*) from raw.raw_postings").fetchone()[0] == 0
        assert connection.execute("select status from raw.ingestion_runs").fetchone()[0] == "failed"


def test_empty_success_has_a_run_record(tmp_path):
    folder, _ = snapshot(tmp_path, postings=[])
    db = tmp_path / "test.duckdb"
    load_local(folder, db)
    with duckdb.connect(str(db)) as connection:
        assert connection.execute(
            "select status, record_count from raw.ingestion_runs"
        ).fetchone() == ("success", 0)


def test_modified_data_is_rejected_before_loading(tmp_path):
    folder, _ = snapshot(tmp_path)
    (folder / "postings.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        read_snapshot(folder)


def test_existing_run_cannot_change_day(tmp_path):
    folder, manifest = snapshot(tmp_path)
    db = tmp_path / "test.duckdb"
    load_local(folder, db)
    manifest["snapshot_date"] = "2026-11-05"
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="different content"):
        load_local(folder, db)


@pytest.mark.parametrize("token", ["../other", "a/b", "x;drop", "", "a b"])
def test_identifiers_cannot_escape_paths(token):
    with pytest.raises(ValueError):
        safe_token(token)
