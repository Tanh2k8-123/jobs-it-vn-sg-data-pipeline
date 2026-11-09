"""Public postings only. Offset pagination cannot provide source-side snapshot isolation."""

from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from sea_it_jobs.config import safe_token


class ExtractionError(RuntimeError):
    def __init__(self, message: str, partial: list | None = None, pages: int = 0):
        super().__init__(message)
        self.partial = partial or []
        self.pages = pages


@dataclass
class Extraction:
    postings: list[dict]
    page_count: int


def validate_postings(data: object) -> list[dict]:
    if not isinstance(data, list):
        raise ValueError("Expected a JSON list")
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Posting must be an object")
        if not isinstance(item.get("id"), str) or not item["id"].strip():
            raise ValueError("Missing posting id")
        if item.get("categories") is not None and not isinstance(item["categories"], dict):
            raise ValueError("categories must be an object or null")
        locations = (item.get("categories") or {}).get("allLocations")
        if locations is not None and (
            not isinstance(locations, list) or any(not isinstance(x, str) for x in locations)
        ):
            raise ValueError("allLocations must be a string array or null")
    return data


class LeverClient:
    def __init__(self, page_size: int = 100, max_pages: int = 1000):
        if page_size < 1 or max_pages < 1:
            raise ValueError("page_size and max_pages must be positive")
        self.page_size = page_size
        self.max_pages = max_pages
        self.session = requests.Session()
        retry = Retry(
            total=4,
            connect=4,
            read=4,
            status=4,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            respect_retry_after_header=True,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.headers.update({"User-Agent": "tech-jobs-analytics/0.1 (education)"})

    def close(self):
        self.session.close()

    def fetch(self, board_slug: str) -> Extraction:
        """Collect postings page by page until the API returns an empty list."""
        url = f"https://api.lever.co/v0/postings/{safe_token(board_slug)}"
        collected: list[dict] = []
        # A set makes it cheap to detect IDs already seen on earlier pages.
        seen: set[str] = set()
        pages = 0
        skip = 0
        try:
            for _ in range(self.max_pages):
                response = self.session.get(
                    url,
                    params={"mode": "json", "skip": skip, "limit": self.page_size},
                    timeout=(10, 40),
                )
                response.raise_for_status()
                page = validate_postings(response.json())
                pages += 1
                # An empty terminal page also works if the API caps requested page size.
                if not page:
                    return Extraction(collected, pages)
                for posting in page:
                    if posting["id"] in seen:
                        raise ValueError(f"Duplicate id across pages: {posting['id']}")
                    seen.add(posting["id"])
                    collected.append(posting)
                # Advance by the actual count; the API may cap the requested page size.
                skip += len(page)
            raise ValueError("Pagination exceeded max_pages; snapshot is incomplete")
        except (requests.RequestException, ValueError) as error:
            raise ExtractionError(str(error), collected, pages) from error
