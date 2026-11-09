# Databricks notebook source
# MAGIC %md
# MAGIC # Step 3: check data before reporting
# MAGIC Check duplicate IDs, missing values, row counts, source health and observation dates.
# MAGIC `require_fresh=true` detects Jobs that only reprocess old snapshots.

# COMMAND ----------
import sys
from pathlib import Path

dbutils.widgets.text("repo_root", "")
dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("prefix", "tech_jobs")
dbutils.widgets.dropdown("require_fresh", "true", ["true", "false"])
root = Path(dbutils.widgets.get("repo_root"))
sys.path.insert(0, str(root / "src"))

from sea_it_jobs.databricks_runtime import Lakehouse, check_quality

lake = Lakehouse(root, dbutils.widgets.get("catalog"), dbutils.widgets.get("prefix"))
check_quality(spark, lake, require_fresh=dbutils.widgets.get("require_fresh") == "true")
display(spark.sql(f"SELECT * FROM {lake.table('mart_source_health')} ORDER BY snapshot_date DESC"))
