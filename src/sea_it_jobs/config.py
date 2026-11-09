import csv
import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

SAFE_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


def safe_token(value: str) -> str:
    if not SAFE_TOKEN.fullmatch(value):
        raise ValueError(f"Invalid identifier: {value!r}")
    return value


@dataclass(frozen=True)
class Board:
    board_slug: str
    company_name: str
    enabled: bool
    target_markets: str


def read_boards(path: Path) -> list[Board]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    boards = []
    for row in rows:
        slug = safe_token(row["board_slug"].strip())
        enabled = row["enabled"].strip().lower()
        if enabled not in {"true", "false"}:
            raise ValueError(f"Invalid enabled value for {slug}")
        boards.append(Board(slug, row["company_name"], enabled == "true", row["target_markets"]))
    if len({b.board_slug for b in boards}) != len(boards):
        raise ValueError("Duplicate board slugs")
    if not boards:
        raise ValueError("Boards configuration is empty")
    return boards


@dataclass(frozen=True)
class Settings:
    boards_path: Path
    data_dir: Path
    duckdb_path: Path
    timezone: str
    project: str
    bucket: str
    location: str
    raw_dataset: str
    analytics_dataset: str

    @classmethod
    def from_env(cls):
        load_dotenv()
        return cls(
            Path(os.getenv("BOARDS_CONFIG", "config/boards.csv")),
            Path(os.getenv("DATA_DIR", "data/local")),
            Path(os.getenv("DUCKDB_PATH", "data/local/warehouse.duckdb")),
            os.getenv("SNAPSHOT_TIMEZONE", "Asia/Ho_Chi_Minh"),
            os.getenv("GCP_PROJECT_ID", ""),
            os.getenv("GCS_BUCKET", ""),
            os.getenv("GCP_LOCATION", "asia-southeast1"),
            safe_token(os.getenv("BQ_RAW_DATASET", "tech_jobs_raw")),
            safe_token(os.getenv("BQ_ANALYTICS_DATASET", "tech_jobs_analytics")),
        )
