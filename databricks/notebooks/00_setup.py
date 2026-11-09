# Databricks notebook source
# MAGIC %md
# MAGIC # Step 0: prepare storage
# MAGIC Bronze preserves raw data, Silver standardizes it, and Gold serves dashboards.
# MAGIC The Job supplies `repo_root`, `catalog` and `prefix`; set widgets for a manual run.

# COMMAND ----------
import sys
from pathlib import Path

dbutils.widgets.text("repo_root", "")
dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("prefix", "tech_jobs")
root = Path(dbutils.widgets.get("repo_root"))
sys.path.insert(0, str(root / "src"))

from sea_it_jobs.databricks_runtime import Lakehouse, setup

lake = Lakehouse(root, dbutils.widgets.get("catalog"), dbutils.widgets.get("prefix"))
setup(spark, lake)
print(f"Raw snapshots: {lake.volume_path}")
display(spark.sql(f"SHOW TABLES IN `{lake.catalog}`.`{lake.schema('bronze')}`"))
