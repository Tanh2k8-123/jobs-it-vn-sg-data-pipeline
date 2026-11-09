"""Optional UI verification: uv run --with playwright python scripts/capture_dashboard.py.

Uses installed Microsoft Edge by default. Set --channel chromium after `playwright install chromium`
on Linux. Start Streamlit first. Requires no cloud credentials.
"""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:8501")
parser.add_argument("--channel", default="msedge")
parser.add_argument("--output", type=Path, default=Path("dashboard/screenshots/local-overview.png"))
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel=args.channel, headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1050}, device_scale_factor=1)
    page.goto(args.url)
    page.get_by_role("heading", name="Where tech teams are hiring").wait_for(timeout=30000)
    page.get_by_text("Company view", exact=True).wait_for(timeout=30000)
    page.wait_for_function(
        "document.querySelectorAll('.js-plotly-plot .main-svg').length >= 2", timeout=45000
    )
    page.evaluate("document.fonts.ready")
    page.screenshot(path=str(args.output), full_page=True)
    print(f"Saved {args.output}")
    browser.close()
