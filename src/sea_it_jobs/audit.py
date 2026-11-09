import json
from collections import Counter
from pathlib import Path

from sea_it_jobs.config import Board
from sea_it_jobs.lever import ExtractionError, LeverClient
from sea_it_jobs.snapshots import json_bytes, utc_now


def audit_sources(boards: list[Board], output: Path, client: LeverClient):
    output.mkdir(parents=True, exist_ok=True)
    reports = []
    for board in boards:
        try:
            result = client.fetch(board.board_slug)
            countries = Counter(str(p.get("country") or "UNKNOWN") for p in result.postings)
            locations = Counter(
                str((p.get("categories") or {}).get("location") or "UNKNOWN")
                for p in result.postings
            )
            report = {
                "board_slug": board.board_slug,
                "company_name": board.company_name,
                "status": "success",
                "audited_at": utc_now(),
                "record_count": len(result.postings),
                "page_count": result.page_count,
                "countries": dict(countries),
                "locations": dict(locations),
                "fields": sorted({key for p in result.postings for key in p}),
                "missing_title_count": sum(not p.get("text") for p in result.postings),
                "multi_location_count": sum(
                    len((p.get("categories") or {}).get("allLocations") or []) > 1
                    for p in result.postings
                ),
            }
            (output / f"{board.board_slug}.json").write_bytes(json_bytes(result.postings))
        except ExtractionError as error:
            report = {
                "board_slug": board.board_slug,
                "company_name": board.company_name,
                "status": "failed",
                "audited_at": utc_now(),
                "error": str(error),
            }
        reports.append(report)
        print(json.dumps(report, ensure_ascii=False))
    (output / "audit.json").write_bytes(json_bytes(reports))
    lines = [
        "# Live source audit",
        "",
        "Generated from real API calls; counts change over time.",
        "",
        "| Board | Status | Postings | Primary country counts |",
        "|---|---|---:|---|",
    ]
    for row in reports:
        lines.append(
            f"| {row['board_slug']} | {row['status']} | {row.get('record_count', '—')} | "
            f"{json.dumps(row.get('countries', {}))} |"
        )
    lines += [
        "",
        f"Audit completed at {utc_now()}.",
        "",
        "Primary-country counts exclude additional countries inferred from allLocations.",
        "Reachability is a technical check, not a guarantee of long-term availability.",
    ]
    (output / "audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return reports
