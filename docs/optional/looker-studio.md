# Build the Looker Studio report

This guide is for the optional GCP path. For Databricks, use the [AI/BI dashboard guide](../deployment/dashboard.md).

The repository supplies BigQuery views and a complete chart mapping. A hosted report is an
account-owned Google artifact and must be created after the cloud pipeline has run successfully.

## Connect

1. Open https://lookerstudio.google.com/ and create a blank report.
2. Add the BigQuery connector. Select your billing project, `tech_jobs_analytics` dataset and
   `looker_current_overview` view. Add the remaining sources listed below.
3. Use the `looker_current_*` views for current scorecards and charts. These views return only
   the latest observed date, preventing accidental summation across daily snapshots.
4. Use `mart_daily_country` for the time chart and expose the date range control there.
5. Set `snapshot_date` to a Date field; counts to Number; `coverage_ratio` to Percent.

## Chart mapping

| Tile | Source | Dimension | Metric / aggregation |
|---|---|---|---|
| Observation date | `looker_current_overview` | — | MAX(snapshot_date) |
| Distinct target tech postings | `looker_current_overview` | — | SUM(tech_postings) |
| Recruiting companies | `looker_current_overview` | — | SUM(recruiting_companies) |
| Source coverage | `looker_current_overview` | — | MAX(coverage_ratio), percent |
| Postings by country, bar | `looker_current_country` | country_code | SUM(tech_postings) |
| Roles by country, grouped bar | `looker_current_roles` | role_category; breakdown country_code | SUM(tech_postings) |
| Company table | `looker_current_company` | company_name, snapshot_status | SUM(tech_postings) |
| Daily country trend, line | `mart_daily_country` | snapshot_date; breakdown country_code | SUM(tech_postings) |
| Coverage over time, line | `mart_daily_overview` | snapshot_date | MAX(coverage_ratio) |
| Source health table | `looker_current_source_health` | company_name, snapshot_status, latest_attempt_status, last_success_at | record_count |

The overall scorecard uses `looker_current_overview`, never the sum of VN and SG bars.
Some postings are linked to both countries. Roles-by-country bars also count each country
association separately; label the chart accordingly. Keep source coverage and observation date
visible at the top. Null values on unavailable days must remain gaps, not be replaced with zero.

## Suggested layout

```text
Tech Jobs Analytics — Vietnam & Singapore
Observation date                       Source coverage
[Distinct postings] [Recruiting companies] [Multi-country postings]
[Country distribution]                 [Role distribution by country]
[Daily trend including coverage]
[Company table]                        [Source status]
```

Use teal `#187e78` for VN and orange `#d66a38` for SG, matching the local dashboard.
Add chart titles, counting definitions and this scope statement:

> Public technology postings observed at selected companies in VN/SG. Counts do not represent
> the whole market or the number of vacancies. Coverage changes affect daily comparisons.

## Share and capture evidence

Choose report sharing and data credential settings that let reviewers view the charts without
access to your Cloud Console. Restrict any underlying project permissions appropriately; do not
publish credentials. Test the report in a signed-out/private browser before submission.
Save the report URL in README and screenshots under `dashboard/screenshots/`. Export a PDF if
reviewers also need a static fallback. Never use synthetic demo charts as evidence of real history.

## Reference query

```sql
SELECT snapshot_date, country_code, tech_postings, coverage_ratio
FROM `YOUR_PROJECT_ID.tech_jobs_analytics.mart_daily_country`
WHERE snapshot_date >= DATE_SUB(CURRENT_DATE('Asia/Ho_Chi_Minh'), INTERVAL 30 DAY)
ORDER BY snapshot_date, country_code;
```

Use date filters to benefit from partition pruning. Data freshness depends on pipeline execution
and the report connector's refresh settings. There is no historical series before first collection.
