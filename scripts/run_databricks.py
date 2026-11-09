"""Local API collection → upload Volume → optional remote Job, without GCP credentials.

uv run python scripts/run_databricks.py --run-id RUN
uv run python scripts/run_databricks.py --collect --job-id 123
"""

import argparse
from datetime import datetime, timezone
from uuid import uuid4

from databricks.sdk import WorkspaceClient

from sea_it_jobs.cli import extract
from sea_it_jobs.config import Settings, safe_token
from sea_it_jobs.databricks_upload import upload_run


def main():
    parser = argparse.ArgumentParser(
        description="Collect API data locally and upload snapshots to Databricks."
    )
    parser.add_argument("--profile", default="tech-jobs-free")
    parser.add_argument("--run-id", help="Saved snapshot run ID; optional with --collect.")
    parser.add_argument("--collect", action="store_true", help="Collect fresh data before upload.")
    parser.add_argument("--job-id", type=int, help="Deployed Job ID to run after upload.")
    parser.add_argument(
        "--volume-path", default="/Volumes/workspace/tech_jobs_bronze/raw_snapshots"
    )
    args = parser.parse_args()
    if not args.collect and not args.run_id:
        parser.error("Use --run-id RUN or --collect")
    settings = Settings.from_env()
    try:
        # The CLI/SDK manages OAuth; keep tokens and passwords out of source code.
        client = WorkspaceClient(profile=args.profile)
        client.files.get_directory_metadata(args.volume_path)
        run_id = safe_token(
            args.run_id
            or (
                "upload_"
                + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
                + "_"
                + uuid4().hex[:8]
            )
        )
        failed = False
        if args.collect:
            manifests = extract(settings, run_id, page_size=100, board_filter=None)
            failed = any(m["status"] != "success" for m in manifests)
        upload_run(client, settings.data_dir, args.volume_path, run_id)
        print(f"run_id={run_id}")
        if args.job_id is not None:
            run = client.jobs.run_now_and_wait(
                job_id=args.job_id,
                job_parameters={"source_mode": "volume", "require_fresh": "true"},
            )
            print(f"Databricks run: {run.run_page_url}")
        elif failed:
            print("Some sources failed. Snapshots and failure metadata were uploaded for review.")
        return int(failed)
    except Exception as error:
        print(f"Databricks: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
