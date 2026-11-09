import json
import re
from pathlib import Path

import sqlglot
import yaml
from sqlglot import exp


def test_bundle_keeps_schema_names_consistent_with_notebook_parameters():
    bundle = yaml.safe_load(Path("databricks.yml").read_text(encoding="utf-8"))
    for target in bundle["targets"].values():
        # Development mode silently prefixes schemas, unlike the notebook's prefix widget.
        if target.get("mode") == "development":
            assert target.get("presets", {}).get("skip_name_prefix_for_schema") is True
    for layer in ["bronze", "silver", "gold"]:
        assert bundle["resources"]["schemas"][layer]["name"] == "${var.prefix}_" + layer


def test_bundle_manages_dashboard_and_refreshes_only_after_quality_checks():
    bundle = yaml.safe_load(Path("databricks.yml").read_text(encoding="utf-8"))
    tasks = bundle["resources"]["jobs"]["tech_jobs_daily"]["tasks"]
    refresh = next(task for task in tasks if "dashboard_task" in task)
    assert refresh["depends_on"] == [{"task_key": "quality_checks"}]
    reference = refresh["dashboard_task"]["dashboard_id"]
    resource_name = re.fullmatch(r"\$\{resources\.dashboards\.(\w+)\.id\}", reference)[1]
    resource = bundle["resources"]["dashboards"][resource_name]
    assert Path(resource["file_path"]).is_file()
    assert resource["embed_credentials"] is False


def test_dashboard_uses_gold_models_and_provides_category_and_time_charts():
    asset = Path("databricks/dashboards/tech_jobs.lvdash.json")
    dashboard = json.loads(asset.read_text(encoding="utf-8"))
    models = {path.stem for path in Path("dbt/models/marts").glob("*.sql")}
    datasets = {dataset["name"] for dataset in dashboard["datasets"]}
    for dataset in dashboard["datasets"]:
        query = sqlglot.parse_one("\n".join(dataset["queryLines"]), read="databricks")
        assert isinstance(query, exp.Select)
        assert all(table.name in models for table in query.find_all(exp.Table))
    widgets = [item["widget"] for page in dashboard["pages"] for item in page["layout"]]
    chart_types = {widget.get("spec", {}).get("widgetType") for widget in widgets}
    assert {"bar", "line"} <= chart_types
    for widget in widgets:
        for query in widget.get("queries", []):
            assert query["query"]["datasetName"] in datasets
