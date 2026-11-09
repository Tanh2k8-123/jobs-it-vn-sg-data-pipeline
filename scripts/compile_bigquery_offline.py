"""Compile the BigQuery SQL without real credentials or executing remote queries.

Uses anonymous credentials only inside the compiler, and rejects any attempted query.
This checks template rendering, not BigQuery execution, permissions or service availability.
Run: uv run python scripts/compile_bigquery_offline.py
"""

import os
from unittest.mock import patch

from dbt.cli.main import dbtRunner
from google.auth.credentials import AnonymousCredentials

os.environ["GCP_PROJECT_ID"] = "offline-validation-project"
with (
    patch(
        "google.auth.default", return_value=(AnonymousCredentials(), "offline-validation-project")
    ),
    patch("google.cloud.bigquery.Client.query", side_effect=RuntimeError("Remote query forbidden")),
):
    result = dbtRunner().invoke(
        [
            "compile",
            "--project-dir",
            "dbt",
            "--profiles-dir",
            "dbt",
            "--target",
            "bigquery",
            "--no-introspect",
            "--no-populate-cache",
            "--target-path",
            "target-bigquery",
        ]
    )
if not result.success:
    raise SystemExit(str(result.exception or "Offline compilation failed"))
print("BigQuery templates compiled offline. No remote queries were allowed.")
