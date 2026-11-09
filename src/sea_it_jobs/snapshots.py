import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from sea_it_jobs.config import Board, safe_token
from sea_it_jobs.lever import ExtractionError, LeverClient, validate_postings


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def collect_snapshot(client: LeverClient, board: Board, root: Path, run_id: str, day: str):
    """Save postings and a manifest recording their source, date and run."""
    folder = root / "lever" / board.board_slug / f"snapshot_date={day}" / f"run_id={run_id}"
    folder.mkdir(parents=True, exist_ok=False)
    started = utc_now()
    error_message = None
    try:
        result = client.fetch(board.board_slug)
        postings, pages, status = result.postings, result.page_count, "success"
    except ExtractionError as error:
        postings, pages, status = error.partial, error.pages, "failed"
        error_message = str(error)
    raw = json_bytes(postings)
    (folder / "postings.json").write_bytes(raw)
    manifest = {
        "schema_version": 1,
        "run_id": safe_token(run_id),
        "board_slug": board.board_slug,
        "company_name": board.company_name,
        "snapshot_date": day,
        "started_at": started,
        "completed_at": utc_now(),
        "fetched_at": utc_now(),
        "status": status,
        "extraction_status": "complete" if status == "success" else "incomplete",
        "record_count": len(postings),
        "page_count": pages,
        "error_message": error_message,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_url": f"https://api.lever.co/v0/postings/{board.board_slug}?mode=json",
    }
    # Manifest is the completion marker and is always written last.
    (folder / "manifest.json").write_bytes(json_bytes(manifest))
    return folder, manifest


def read_snapshot(folder: Path):
    """Validate saved content against the manifest before loading it."""
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported manifest schema version")
    safe_token(manifest["run_id"])
    safe_token(manifest["board_slug"])
    datetime.strptime(manifest["snapshot_date"], "%Y-%m-%d")
    for field in ["started_at", "completed_at", "fetched_at"]:
        if datetime.fromisoformat(manifest[field]).tzinfo is None:
            raise ValueError(f"{field} requires an explicit timezone")
    for field in ["record_count", "page_count"]:
        if type(manifest[field]) is not int or manifest[field] < 0:
            raise ValueError(f"{field} must be a nonnegative integer")
    if manifest["status"] not in {"success", "failed"}:
        raise ValueError("Invalid snapshot status")
    raw = (folder / "postings.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest["sha256"]:
        raise ValueError("Snapshot checksum mismatch")
    postings = json.loads(raw)
    if not isinstance(postings, list):
        raise ValueError("Snapshot postings must be a JSON list")
    if len(postings) != manifest["record_count"]:
        raise ValueError("Snapshot count mismatch")
    if manifest["status"] == "success":
        if manifest["extraction_status"] != "complete":
            raise ValueError("Successful snapshot must be complete")
        validate_postings(postings)
        if len({p["id"] for p in postings}) != len(postings):
            raise ValueError("Duplicate posting ids in snapshot")
    return manifest, postings


def raw_rows(manifest: dict, postings: list):
    if manifest["status"] != "success":
        return []
    return [
        {
            "run_id": manifest["run_id"],
            "board_slug": manifest["board_slug"],
            "snapshot_date": manifest["snapshot_date"],
            "fetched_at": manifest["fetched_at"],
            "job_id": posting["id"],
            "posting_json": json.dumps(posting, ensure_ascii=False),
        }
        for posting in postings
    ]


RUN_FIELDS = [
    "run_id",
    "board_slug",
    "snapshot_date",
    "started_at",
    "completed_at",
    "fetched_at",
    "status",
    "extraction_status",
    "record_count",
    "page_count",
    "error_message",
    "sha256",
]
