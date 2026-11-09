# Databricks notebook source
# MAGIC %md
# MAGIC # Step 2: build Silver and Gold
# MAGIC Use the local version's SQL rules to select daily snapshots, classify and count postings.
# MAGIC Spark executes the SQL; no notebook installation of dbt or PySpark is needed.

# COMMAND ----------
import sys
from pathlib import Path

dbutils.widgets.text("repo_root", "")
dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("prefix", "tech_jobs")
root = Path(dbutils.widgets.get("repo_root"))
sys.path.insert(0, str(root / "src"))

from sea_it_jobs.databricks_runtime import Lakehouse, transform

lake = Lakehouse(root, dbutils.widgets.get("catalog"), dbutils.widgets.get("prefix"))
transform(spark, lake)
display(spark.sql(f"SELECT * FROM {lake.table('mart_daily_overview')} ORDER BY snapshot_date DESC"))
