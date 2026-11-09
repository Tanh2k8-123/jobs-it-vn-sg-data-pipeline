# Architecture and data rules

## Execution paths

| Path | Flow |
|---|---|
| Databricks (selected cloud target) | Python → JSON/manifest → Unity Catalog Volume → Bronze Delta → Spark SQL Silver/Gold → AI/BI dashboard |
| Local | Python → JSON/manifest → DuckDB raw tables → dbt → published CSV generation → Streamlit |
| GCP (optional) | Python → GCS → validate lake snapshot → BigQuery transactional load → dbt → Looker Studio |

**Bronze** preserves original data. **Silver** standardizes it. **Gold** contains reporting metrics. A **mart** is a table prepared for an analytical question; a **view** is a named SQL query.

Local/GCP runs use `dbt build`. Databricks renders the same 19 SQL model files and executes them with Spark, then runs 18 shared integrity queries. It does **not** run `dbt build` in the notebook. Three seeds provide company, location and title rules.

The default Databricks path collects locally because Free Edition can restrict outbound network access. `source_mode=api` works only if the workspace can reach Lever. See [Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations).

## Source contract

`config/boards.csv` is the source of truth. Board identifiers are case-sensitive: `shopback-2`, `portcast`, `gradion` and `GoToGroup`. Before enabling a board, run `uv run sea-it-jobs audit` and review reachability, IDs, geographic coverage, field quality and applicable usage conditions. Samples and summaries are written under `data/local/audit/`; the committed [audit](source-audit.md) is a dated reference.

Requests use public GET endpoints from the [Lever Postings API](https://github.com/lever/postings-api). The pipeline collects no applicant data, bypasses no authentication and sends no application POST requests. JSON contracts are documented in `config/schemas/`.

## Snapshots and loading

Each board/run produces two files:

```text
lever/<board>/snapshot_date=YYYY-MM-DD/run_id=RUN/
    postings.json   # API records; partial records retained for inspection
    manifest.json   # Source, run, dates, status, counts and SHA-256 checksum
```

`snapshot_date` is the collection date in `Asia/Ho_Chi_Minh` by default; event timestamps are UTC. Replay preserves the original date. No historical date can be supplied to extraction.

A run ID identifies an extraction attempt. Loading the same board/run again does not duplicate observations. Extraction reuses a saved same-day run; use a **new** ID to retry a failed API collection. Loading validates the checksum, IDs and record count.

- **Databricks:** one `snapshot_envelopes` row holds manifest fields and the postings array. One Delta `MERGE` commits both together. Bronze views expose postings and run history. Replays skip matching signatures and reject conflicts. A 100 MB posting-payload guard per board limits this small-data design.
- **DuckDB:** raw rows and metadata for the selected board/run are replaced in one transaction. Failure rolls back both changes.
- **GCP:** GCS writes are create-only; identical objects are accepted, conflicting content rejected. The manifest is uploaded last. BigQuery stages data, then replaces raw rows and run metadata in one transaction. Staging tables expire after one hour and are cleaned up after loading.
- **Dashboard:** a completed CSV generation is published only after `dbt build` succeeds. Streamlit reads exports rather than holding warehouse connections open.

## Data model

**Grain** means what one row represents. Local/GCP raw relations use the `raw` schema/dataset; local models use `analytics`. Databricks uses `tech_jobs_bronze`, `tech_jobs_silver` and `tech_jobs_gold` under the configured catalog.

| Relation | Grain / purpose |
|---|---|
| `raw_postings` | Board + run + posting ID; original JSON |
| `ingestion_runs` | Board + run; includes failures and valid empty results |
| `stg_lever_postings`, `stg_ingestion_runs` | Extract and standardize raw fields |
| `int_daily_runs` | Latest complete successful run per board/date |
| `int_daily_postings` | Postings from selected daily runs |
| `int_job_country`, `int_job_role` | Country links and ordered title classification |
| `fct_job_snapshots` | Board + posting ID + observed date; all roles/countries |
| `bridge_job_country` | Posting observation + target country, deduplicated |
| `dim_company` | Configured company and enabled status |
| `mart_source_health` | Date + enabled board, including missing/failed sources |
| `mart_daily_overview` | Date; distinct target tech postings and source coverage |
| `mart_daily_country` | Date + VN/SG; country-linked tech postings |
| `mart_daily_roles` | Date + country + classified tech role |
| `mart_daily_company` | Date + monitored company; unavailable counts stay NULL |
| `looker_current_*` | Latest-date overview/country/role/company/source-health views |

The `looker_current_*` names are shared across platforms; Databricks dashboards use them too.

## Counting rules

1. Posting identity combines board and posting ID. Daily facts add the observation date.
2. Each board/date uses its latest complete successful run. A later failure leaves an earlier same-day success usable and exposes the failure. A later successful empty run replaces an earlier nonempty run.
3. No successful source on a date means NULL/unavailable. Partial coverage counts only successful sources. No observations carry forward from previous days.
4. A posting linked to both countries counts once overall and once in each country. Country totals can exceed the distinct overall total.
5. `dbt/seeds/role_rules.csv` classifies titles by priority; descriptions are not used. Unclassified postings remain in facts but are excluded from technology metrics.
6. Countries come from `country`, `categories.location` and `categories.allLocations`, using explicit VN/SG aliases. Unknown, remote-only and ambiguous locations stay outside target metrics.
7. `config/boards.csv` controls ingestion and the company seed. Coverage uses the current enabled roster for every date. Keep it fixed during comparisons or disclose membership changes.

## Storage layout

Databricks Bronze uses liquid clustering on `(snapshot_date, board_slug)`; daily analytical Delta tables use `snapshot_date`. Dashboards filter by date; source helps inspect ingestion. Static partitions are not used: [liquid clustering replaces partitioning and ZORDER](https://docs.databricks.com/aws/en/tables/clustering). Credit under a literal partition-and-cluster rubric is therefore not guaranteed.

BigQuery raw/daily tables are partitioned by `snapshot_date`. Raw data is clustered by board/job ID; facts by board/role; country marts by country. Date filters allow partition pruning. Initial volume is small, so no measured speed improvement is claimed. Marts are rebuilt rather than incrementally updated.

## Known limitations

- Offset pagination has no snapshot isolation. Checks catch duplicate IDs and missing terminal pages, but changes during requests can still cause undetected omissions.
- Title/location rules are conservative heuristics and need review against real postings.
- Current-roster coverage does not model historical source membership.
- Posting disappearance does not establish a hire or an exact closure time.
- Databricks scans saved manifests and uses one envelope row per board/run. Larger workloads need incremental discovery and chunked ingestion.
- Local CSV generations accumulate. Remove old generations under a retention policy after stopping readers.
- Cloud permissions, network access and dashboard sharing need account-specific validation. See [validation](validation.md).
