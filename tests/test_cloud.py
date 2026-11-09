from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from google.api_core.exceptions import PreconditionFailed

from sea_it_jobs.cloud import load_bigquery, upload_snapshot
from sea_it_jobs.config import Board, Settings
from sea_it_jobs.lever import Extraction
from sea_it_jobs.snapshots import collect_snapshot


@pytest.fixture
def cloud_snapshot(tmp_path):
    settings = Settings(
        tmp_path / "boards.csv",
        tmp_path,
        tmp_path / "warehouse.duckdb",
        "Asia/Ho_Chi_Minh",
        "example-project",
        "example-bucket",
        "asia-southeast1",
        "jobs_raw",
        "jobs_analytics",
    )
    folder, _ = collect_snapshot(
        SimpleNamespace(fetch=lambda _: Extraction([{"id": "one"}], 2)),
        Board("example", "Example", True, "VN"),
        tmp_path,
        "one_run",
        "2026-11-04",
    )
    return folder, settings


def test_upload_publishes_manifest_last(cloud_snapshot):
    folder, settings = cloud_snapshot
    with patch("google.cloud.storage.Client") as factory:
        bucket = factory.return_value.bucket.return_value
        upload_snapshot(folder, settings)
        names = [call.args[0] for call in bucket.blob.call_args_list]
        assert names[0].endswith("postings.json")
        assert names[1].endswith("manifest.json")
        blob = bucket.blob.return_value
        assert blob.upload_from_string.call_args.kwargs["if_generation_match"] == 0


def test_different_existing_object_is_rejected(cloud_snapshot):
    folder, settings = cloud_snapshot
    with patch("google.cloud.storage.Client") as factory:
        blob = factory.return_value.bucket.return_value.blob.return_value
        blob.upload_from_string.side_effect = PreconditionFailed("exists")
        blob.download_as_bytes.return_value = b"different"
        with pytest.raises(ValueError, match="Immutable"):
            upload_snapshot(folder, settings)


def test_bigquery_load_stages_then_commits_and_cleans_up(cloud_snapshot):
    folder, settings = cloud_snapshot
    with patch("google.cloud.bigquery.Client") as factory:
        client = factory.return_value
        client.load_table_from_json.return_value = MagicMock()
        load_bigquery(folder, settings)
        sql = client.query.call_args.args[0]
        assert "BEGIN TRANSACTION" in sql and "COMMIT TRANSACTION" in sql
        assert "ASSERT NOT EXISTS" in sql
        assert client.load_table_from_json.call_count == 2
        assert client.delete_table.call_count == 2
