import io
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import sqlglot

from sea_it_jobs.config import Board
from sea_it_jobs.databricks_runtime import (
    Lakehouse,
    compiled_models,
    copy_snapshot,
    envelope_row,
    identifier,
    quality_queries,
    render_sql,
)
from sea_it_jobs.databricks_upload import upload_run
from sea_it_jobs.lever import Extraction
from sea_it_jobs.snapshots import collect_snapshot


@pytest.fixture
def local_snapshot(tmp_path):
    folder, manifest = collect_snapshot(
        SimpleNamespace(fetch=lambda _: Extraction([{"id": "a", "text": "Data Engineer"}], 2)),
        Board("test", "Test", True, "VN"),
        tmp_path,
        "run1",
        "2026-11-04",
    )
    return tmp_path, folder, manifest


def test_all_shared_models_and_checks_render_as_databricks_sql():
    lake = Lakehouse(Path.cwd())
    models = compiled_models(lake)
    assert len(models) == 19
    assert len(quality_queries(lake)) == 18
    for _, sql in models:
        sqlglot.parse_one(sql, read="databricks")
    for sql in quality_queries(lake).values():
        sqlglot.parse_one(sql, read="databricks")
    order = [name for name, _ in models]
    assert order.index("stg_ingestion_runs") < order.index("int_daily_runs")
    assert order.index("fct_job_snapshots") < order.index("mart_daily_overview")
    assert order.index("mart_daily_overview") < order.index("looker_current_country")


def test_json_and_multi_location_sql_use_spark_functions():
    lake = Lakehouse(Path.cwd())
    staged, _ = render_sql(
        lake, (Path("dbt/models/staging/stg_lever_postings.sql")).read_text(encoding="utf-8")
    )
    country, _ = render_sql(
        lake, (Path("dbt/models/intermediate/int_job_country.sql")).read_text(encoding="utf-8")
    )
    assert "get_json_object" in staged and "ARRAY<STRING>" in staged
    assert "lateral view explode" in country and "regexp_like" in country
    assert "json_extract_string" not in staged


def test_envelope_contains_manifest_and_postings_atomically(local_snapshot):
    _, _, manifest = local_snapshot
    row = envelope_row(manifest, [{"id": "a"}])
    assert row["snapshot_date"] == date(2026, 11, 4)
    assert row["started_at"].tzinfo is not None
    assert row["postings"][0]["job_id"] == "a"
    failed = {**manifest, "status": "failed", "extraction_status": "incomplete"}
    assert envelope_row(failed, [{"id": "partial"}])["postings"] == []


def test_copy_to_volume_is_idempotent_and_preserves_manifest(local_snapshot, tmp_path):
    _, folder, _ = local_snapshot
    lake = SimpleNamespace(volume_path=tmp_path / "volume")
    destination = copy_snapshot(folder, lake)
    copy_snapshot(folder, lake)
    assert (destination / "postings.json").read_bytes() == (folder / "postings.json").read_bytes()
    (destination / "postings.json").write_bytes(b"changed")
    with pytest.raises(ValueError, match="differs"):
        copy_snapshot(folder, lake)


def test_workspace_upload_orders_manifest_last(local_snapshot):
    pytest.importorskip("databricks.sdk")
    root, _, _ = local_snapshot
    client = MagicMock()
    upload_run(client, root, "/Volumes/workspace/tech_jobs_bronze/raw_snapshots", "run1")
    calls = client.files.upload.call_args_list
    assert calls[0].args[0].endswith("postings.json")
    assert calls[1].args[0].endswith("manifest.json")
    assert calls[0].kwargs["overwrite"] is False


def test_workspace_upload_rejects_different_existing_file(local_snapshot):
    pytest.importorskip("databricks.sdk")
    from databricks.sdk.errors import AlreadyExists

    root, _, _ = local_snapshot
    client = MagicMock()
    client.files.upload.side_effect = AlreadyExists("exists")
    client.files.download.return_value.contents = io.BytesIO(b"different")
    with pytest.raises(ValueError, match="Immutable remote"):
        upload_run(client, root, "/Volumes/workspace/tech_jobs_bronze/raw_snapshots", "run1")


@pytest.mark.parametrize("value", ["a;drop", "../x", "a.b", "", "a`b"])
def test_sql_identifiers_reject_path_or_sql_fragments(value):
    with pytest.raises(ValueError):
        identifier(value)
