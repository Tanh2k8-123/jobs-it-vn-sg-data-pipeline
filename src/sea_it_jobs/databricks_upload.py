"""Upload local snapshots through the workspace Files API when Lever egress is restricted."""

import io
from pathlib import Path

from sea_it_jobs.config import safe_token
from sea_it_jobs.snapshots import read_snapshot


def upload_run(client, data_dir: Path, volume_path: str, run_id: str):
    from databricks.sdk.errors import AlreadyExists, ResourceAlreadyExists

    safe_token(run_id)
    parts = volume_path.strip("/").split("/")
    if len(parts) != 4 or parts[0] != "Volumes":
        raise ValueError("Use /Volumes/<catalog>/<schema>/<volume> for --volume-path")
    from sea_it_jobs.databricks_runtime import identifier

    for part in parts[1:]:
        identifier(part)
    folders = sorted(data_dir.glob(f"lever/*/snapshot_date=*/run_id={run_id}"))
    if not folders:
        raise ValueError(f"No local snapshots found for run {run_id}")
    uploaded = []
    for folder in folders:
        manifest, _ = read_snapshot(folder)
        destination = (
            f"/{'/'.join(parts)}/lever/{manifest['board_slug']}/"
            f"snapshot_date={manifest['snapshot_date']}/run_id={manifest['run_id']}"
        )
        client.files.create_directory(destination)
        for filename in ["postings.json", "manifest.json"]:
            contents = (folder / filename).read_bytes()
            path = f"{destination}/{filename}"
            try:
                client.files.upload(path, io.BytesIO(contents), overwrite=False, use_parallel=False)
            except (AlreadyExists, ResourceAlreadyExists):
                response = client.files.download(path)
                if response.contents is None:
                    raise ValueError(f"Cannot verify existing snapshot: {path}") from None
                with response.contents as existing:
                    if existing.read() != contents:
                        raise ValueError(f"Immutable remote snapshot differs: {path}") from None
        uploaded.append(destination)
        print(f"Uploaded {manifest['board_slug']}: {manifest['status']}")
    return uploaded
