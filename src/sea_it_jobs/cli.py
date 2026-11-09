import argparse
import json
import logging
import os
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from sea_it_jobs.audit import audit_sources
from sea_it_jobs.config import Settings, read_boards, safe_token
from sea_it_jobs.lever import LeverClient
from sea_it_jobs.snapshots import collect_snapshot, read_snapshot
from sea_it_jobs.warehouse import load_local

LOGGER = logging.getLogger(__name__)


def transform(settings: Settings, target: str):
    """Build and test dbt models; local runs also publish dashboard CSVs."""
    if not Path("dbt/dbt_project.yml").is_file():
        raise ValueError("Run this command from the repository root")
    env = dict(os.environ)
    env["DUCKDB_PATH"] = str(settings.duckdb_path.resolve())
    env["GCP_PROJECT_ID"] = settings.project or "local-project"
    env["GCP_LOCATION"] = settings.location
    env["BQ_RAW_DATASET"] = settings.raw_dataset
    env["BQ_ANALYTICS_DATASET"] = settings.analytics_dataset
    env["BOARDS_CONFIG"] = str(settings.boards_path.resolve())
    # The monitored-company seed always comes from the ingestion configuration.
    seed = Path("dbt/seeds/companies.csv")
    seed.write_bytes(settings.boards_path.read_bytes())
    subprocess.run(
        [
            "dbt",
            "build",
            "--project-dir",
            "dbt",
            "--profiles-dir",
            "dbt",
            "--target",
            "bigquery" if target == "cloud" else "local",
        ],
        check=True,
        env=env,
    )
    if target == "local":
        from sea_it_jobs.exports import export_marts

        export_marts(settings)


def snapshot_folders(settings: Settings, run_id: str) -> list[Path]:
    safe_token(run_id)
    folders = sorted(settings.data_dir.glob(f"lever/*/snapshot_date=*/run_id={run_id}"))
    if not folders:
        raise ValueError(f"No snapshots found for run_id={run_id}")
    return folders


def load_all(settings: Settings, run_id: str, target: str):
    """Load a saved run's snapshots into the local or cloud warehouse."""
    for folder in snapshot_folders(settings, run_id):
        if target == "cloud":
            from sea_it_jobs.cloud import download_snapshot, load_bigquery, upload_snapshot

            uri = upload_snapshot(folder, settings)
            print(uri)
            lake_snapshot = download_snapshot(uri, settings.data_dir, settings)
            manifest = load_bigquery(lake_snapshot, settings)
        else:
            manifest = load_local(folder, settings.duckdb_path)
        print(f"Loaded {manifest['board_slug']}: {manifest['status']}")


def extract(settings: Settings, run_id: str, page_size: int, board_filter: str | None):
    """Read the board configuration and collect snapshots for enabled sources."""
    boards = [b for b in read_boards(settings.boards_path) if b.enabled]
    if board_filter:
        requested = set(board_filter.split(","))
        if requested - {b.board_slug for b in boards}:
            raise ValueError("--boards contains unknown or disabled boards")
        boards = [b for b in boards if b.board_slug in requested]
    if not boards:
        raise ValueError("No enabled boards")
    day = datetime.now(ZoneInfo(settings.timezone)).date().isoformat()
    client = LeverClient(page_size=page_size)
    results = []
    try:
        for board in boards:
            folder = (
                settings.data_dir
                / "lever"
                / board.board_slug
                / f"snapshot_date={day}"
                / f"run_id={run_id}"
            )
            if (folder / "manifest.json").exists():
                manifest, _ = read_snapshot(folder)
            else:
                _, manifest = collect_snapshot(client, board, settings.data_dir, run_id, day)
            print(json.dumps(manifest, ensure_ascii=False))
            results.append(manifest)
    finally:
        client.close()
    return results


def parser():
    root = argparse.ArgumentParser(description="Daily Lever snapshots and analytics")
    commands = root.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("audit", help="Audit configured public boards")
    audit.add_argument("--output", type=Path, default=Path("data/local/audit"))
    audit.add_argument("--page-size", type=int, default=100)
    for name in ["extract", "pipeline"]:
        command = commands.add_parser(name)
        command.add_argument("--run-id")
        command.add_argument("--boards", help="Comma-separated subset of enabled boards")
        command.add_argument("--page-size", type=int, default=100)
        if name == "extract":
            command.add_argument(
                "--allow-partial",
                action="store_true",
                help="Let downstream tasks publish source failures before check-run",
            )
        else:
            command.add_argument("--target", choices=["local", "cloud"], default="local")
    load = commands.add_parser("load")
    load.add_argument("--run-id", required=True)
    load.add_argument("--target", choices=["local", "cloud"], default="local")
    build = commands.add_parser("transform")
    build.add_argument("--target", choices=["local", "cloud"], default="local")
    check = commands.add_parser("check-run")
    check.add_argument("--run-id", required=True)
    replay = commands.add_parser("replay")
    replay.add_argument("snapshot", help="Local snapshot folder or gs:// snapshot prefix")
    replay.add_argument("--target", choices=["local", "cloud"], default="local")
    commands.add_parser("demo", help="Build isolated, explicitly synthetic demonstration data")
    return root


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parser().parse_args()
    settings = Settings.from_env()
    try:
        if args.command == "audit":
            client = LeverClient(args.page_size)
            try:
                results = audit_sources(read_boards(settings.boards_path), args.output, client)
            finally:
                client.close()
            return int(any(r["status"] != "success" for r in results))
        if args.command in {"extract", "pipeline"}:
            run_id = safe_token(
                args.run_id
                or (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + uuid4().hex[:8])
            )
            print(f"run_id={run_id}", flush=True)
            # Step 1: fetch API records and save JSON with run metadata.
            results = extract(settings, run_id, args.page_size, args.boards)
            failed = any(m["status"] != "success" for m in results)
            if args.command == "pipeline":
                # Step 2: load snapshots into raw tables.
                load_all(settings, run_id, args.target)
                # Step 3: build/test SQL models and publish local dashboard exports.
                transform(settings, args.target)
            elif args.allow_partial:
                return 0
            return int(failed)
        if args.command == "load":
            load_all(settings, args.run_id, args.target)
        elif args.command == "transform":
            transform(settings, args.target)
        elif args.command == "check-run":
            manifests = [read_snapshot(f)[0] for f in snapshot_folders(settings, args.run_id)]
            failed = [m["board_slug"] for m in manifests if m["status"] != "success"]
            if failed:
                raise ValueError(f"Failed source extractions: {', '.join(failed)}")
        elif args.command == "replay":
            folder = Path(args.snapshot)
            if args.snapshot.startswith("gs://"):
                from sea_it_jobs.cloud import download_snapshot

                folder = download_snapshot(args.snapshot, settings.data_dir, settings)
            if args.target == "cloud":
                from sea_it_jobs.cloud import load_bigquery, upload_snapshot

                upload_snapshot(folder, settings)
                load_bigquery(folder, settings)
            else:
                load_local(folder, settings.duckdb_path)
        elif args.command == "demo":
            from sea_it_jobs.demo import create_demo

            demo_settings = replace(
                settings, data_dir=Path("data/demo"), duckdb_path=Path("data/demo/warehouse.duckdb")
            )
            create_demo(demo_settings)
            transform(demo_settings, "local")
            print("Synthetic demo ready. Set DATA_DIR=data/demo for the dashboard.")
        return 0
    except (Exception, KeyboardInterrupt) as error:
        LOGGER.error("%s", error)
        return 130 if isinstance(error, KeyboardInterrupt) else 1


if __name__ == "__main__":
    sys.exit(main())
