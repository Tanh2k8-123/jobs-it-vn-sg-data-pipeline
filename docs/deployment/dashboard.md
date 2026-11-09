# Build the Databricks dashboard

The bundle deploys the dashboard from `databricks/dashboards/tech_jobs.lvdash.json`. The Job's final task refreshes it only after the Gold tables pass quality checks. Use the existing dashboard instead of creating a duplicate.

To publish the deployed asset after an update, use `databricks lakeview publish DASHBOARD_ID --profile tech-jobs-free`. Viewer credentials remain required (`embed_credentials: false`); deployment does not expand sharing permissions. Update the JSON asset if you change catalog/schema names in its queries.

The dataset mapping below also supports manual recreation through **Dashboards → Create dashboard** using the serverless SQL warehouse. UI labels can vary.

## Datasets and tiles

| Tile | Query | Chart settings |
|---|---|---|
| Current metrics | `select * from workspace.tech_jobs_gold.looker_current_overview` | Counters: `tech_postings`, `recruiting_companies`, `coverage_ratio`; display `snapshot_date` |
| Postings by country | `select * from workspace.tech_jobs_gold.looker_current_country` | Bar: country code vs tech postings |
| Postings by role | `select * from workspace.tech_jobs_gold.looker_current_roles` | Bar: role category vs tech postings, colored by country |
| Source status | `select * from workspace.tech_jobs_gold.looker_current_source_health` | Table: company, snapshot status, latest attempt status/error |

The `looker_current_*` names are shared model names, not a requirement to use Looker. Format coverage as a percentage.

For the time-series tile:

```sql
select snapshot_date, country_code, tech_postings, coverage_ratio
from workspace.tech_jobs_gold.mart_daily_country
order by snapshot_date, country_code;
```

Use a line chart: date on X, postings on Y, country as the series. Collect at least two **real** observation dates before claiming a trend. Preserve gaps for unavailable values; do not replace them with zero.

## Minimum submission dashboard

Include at least one categorical bar chart and one time-series chart, with descriptive titles and visible dates. Show source coverage beside counts. Add this explanation:

> Public technology postings observed at selected companies in Vietnam and Singapore. A posting linked to both countries counts in each country but once overall. Counts are not total vacancies or completed hires.

## Share and verify

Publish the dashboard and test access using a reviewer-equivalent account. A workspace URL alone does not prove outside users can open it. See [dashboard sharing](https://docs.databricks.com/aws/en/dashboards/share/share).

Add the actual dashboard URL and screenshots to README once available. Keep a static export as supporting evidence; it does not replace interactive access when peer review requires it. The local Streamlit dashboard remains a reproducible alternative for inspecting data. Never present the synthetic demo as real historical observations.
