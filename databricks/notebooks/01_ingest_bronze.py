# Databricks notebook source
# MAGIC %md
# MAGIC # Step 1: load snapshots into Bronze
# MAGIC `volume`: read snapshots uploaded from your machine.
# MAGIC `api`: collect from Lever directly, if workspace network access allows it.
# MAGIC Bronze commits postings and metadata in one Delta row to avoid partial loads.

# COMMAND ----------
import sys
from pathlib import Path

dbutils.widgets.text("repo_root", "")
dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("prefix", "tech_jobs")
dbutils.widgets.dropdown("source_mode", "volume", ["volume", "api"])
dbutils.widgets.text("run_id", "")
root = Path(dbutils.widgets.get("repo_root"))
sys.path.insert(0, str(root / "src"))

from sea_it_jobs.databricks_runtime import Lakehouse, extract_to_volume, load_bronze

lake = Lakehouse(root, dbutils.widgets.get("catalog"), dbutils.widgets.get("prefix"))
mode = dbutils.widgets.get("source_mode")
if mode == "api":
    extract_to_volume(lake, dbutils.widgets.get("run_id"))
elif mode != "volume":
    raise ValueError("source_mode must be volume or api")
load_bronze(spark, lake)
display(spark.sql(f"SELECT board_slug, snapshot_date, status, record_count "
                  f"FROM {lake.table('ingestion_runs', 'bronze')} ORDER BY completed_at DESC"))
