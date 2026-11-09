"""Synthetic data is isolated from real observations; never use it as market history."""

from sea_it_jobs.config import Settings, read_boards
from sea_it_jobs.lever import Extraction, ExtractionError
from sea_it_jobs.snapshots import collect_snapshot
from sea_it_jobs.warehouse import load_local


def posting(job_id, title, country, locations):
    return {
        "id": job_id,
        "text": title,
        "country": country,
        "categories": {"location": locations[0], "allLocations": locations},
        "workplaceType": "hybrid",
        "hostedUrl": "https://example.com/demo/" + job_id,
    }


def create_demo(settings: Settings):
    class FixtureClient:
        def __init__(self, day):
            self.day = day

        def fetch(self, board):
            if board == "gradion" and self.day == "2026-01-02":
                raise ExtractionError("Synthetic outage for coverage demonstration")
            data = {
                "shopback-2": [
                    posting("demo-data", "Senior Data Engineer", "VN", ["Ho Chi Minh, Vietnam"]),
                    posting(
                        "demo-multi", "Fullstack Developer", "SG", ["Singapore", "Hanoi, Vietnam"]
                    ),
                    posting("demo-finance", "Finance Manager", "MY", ["Kuala Lumpur, Malaysia"]),
                ],
                "portcast": [posting("demo-ml", "Machine Learning Engineer", "SG", ["Singapore"])],
                "gradion": [
                    posting("demo-qa", "QA Automation Engineer", "VN", ["Da Nang, Vietnam"])
                ],
                "GoToGroup": [],
            }[board]
            if self.day == "2026-01-02" and board == "shopback-2":
                data.append(posting("demo-new", "Site Reliability Engineer", "SG", ["Singapore"]))
            return Extraction(data, 2 if data else 1)

    for day in ["2026-01-01", "2026-01-02"]:
        for board in read_boards(settings.boards_path):
            run_id = f"synthetic_{day.replace('-', '')}"
            folder = (
                settings.data_dir
                / "lever"
                / board.board_slug
                / f"snapshot_date={day}"
                / f"run_id={run_id}"
            )
            if not (folder / "manifest.json").exists():
                collect_snapshot(FixtureClient(day), board, settings.data_dir, run_id, day)
            load_local(folder, settings.duckdb_path)
