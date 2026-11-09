.PHONY: install test audit local demo dashboard build kestra
install:
	uv sync --frozen --extra cloud --extra dev --extra databricks
test:
	uv run ruff check src tests dashboard scripts
	uv run pytest -q
audit:
	uv run sea-it-jobs audit
local:
	uv run sea-it-jobs pipeline --target local
demo:
	uv run sea-it-jobs demo
dashboard:
	uv run streamlit run dashboard/app.py --browser.gatherUsageStats=false
build:
	docker compose build
kestra:
	docker compose --profile orchestration up -d --build postgres kestra
