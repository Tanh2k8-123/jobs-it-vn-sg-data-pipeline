"""Render Databricks SQL for offline inspection without signing in to a workspace."""

import argparse
from pathlib import Path

from sea_it_jobs.databricks_runtime import Lakehouse, compiled_models, quality_queries

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, default=Path("data/local/databricks_sql"))
args = parser.parse_args()
lake = Lakehouse(Path.cwd())
args.output.mkdir(parents=True, exist_ok=True)
for index, (name, sql) in enumerate(compiled_models(lake), start=1):
    (args.output / f"{index:02}_{name}.sql").write_text(sql + ";\n", encoding="utf-8")
checks = quality_queries(lake)
(args.output / "quality_checks.sql").write_text(
    "\n\n".join(f"-- {name}\n{sql};" for name, sql in checks.items()) + "\n", encoding="utf-8"
)
print(f"Rendered 19 models and {len(checks)} checks to {args.output}")
