# Project review

Reviewed on **2026-11-09 (Vietnam time)** against the seven criteria in the project brief supplied with this review. Each criterion allows up to four points, for **28 technical points**. Required peer reviews and their extra points are separate. This is an engineering assessment, not an official grade.

## Assessment

The project is a suitable batch data-engineering capstone with strong data-integrity design. It solves a clear problem, preserves source evidence and handles failed/empty/multi-country observations carefully. The main remaining submission gap is demonstrated cloud operation and accessible reporting, rather than a missing transformation layer.

| Criterion | Max | Evidence in the project | What is needed for full credit |
|---|---:|---|---|
| Problem description | 4 | README explains the users' questions, source scope and metrics | Keep the scope and chart definitions visible |
| Cloud + IaC | 4 | Bundle defines schemas, a Volume and Job; optional GCP Terraform | Deploy on a real account and retain resource evidence |
| Batch orchestration | 4 | Four-task Databricks Job; uploader collects, uploads and triggers it; optional Kestra DAG | Show a successful complete collection-to-Gold run and working schedule |
| Warehouse | 4 | Delta tables and date/source liquid-clustering design; optional partitioned/clustered BigQuery | Show actual tables/queries; explain the layout and reviewer interpretation |
| Transformations | 4 | 19 shared models, three seeds, local dbt and Spark SQL execution path | Demonstrate the real cloud build; explain model dependencies |
| Dashboard | 4 | Streamlit category/time charts; Databricks datasets and chart instructions | Provide real multi-day data and reviewer-accessible charts |
| Reproducibility | 4 | Locked dependencies, local/demo paths, Docker, CI and setup/recovery docs; fresh source-only demo passed | Verify a dedicated Git checkout and account-specific deployment |

No final total is assigned: resource definitions, mocked cloud tests and a local screenshot do not establish deployed cloud resources or reviewer access. A maximum score cannot be promised before those checks.

## Strengths

- Public non-taxi data with an explicit daily batch use case.
- Original JSON, manifests and checksums make observations auditable.
- Pagination continues to an empty page; malformed/incomplete results fail validation.
- Failure metadata remains visible without turning outages into zero-posting observations.
- Daily selection, multi-country deduplication and source coverage are explicit and tested.
- A local path and isolated synthetic demo let beginners learn without cloud credentials.
- Tests, CI, Docker and infrastructure definitions support portfolio quality; the supplied rubric treats tests/CI/Make as optional extras, not additional scored categories.

## Findings addressed in this revision

| Finding | Change |
|---|---|
| Mixed English/Vietnamese docs, CLI text and notebook explanations | Converted authored project text to English |
| Personal machine paths and a fixed workspace host made setup less portable | Use project-relative instructions and CLI-selected workspace profiles |
| Local/GCP architecture dominated an outdated English README | Make Databricks the primary cloud path; retain GCP as an optional guide |
| Repeated concepts made beginner docs long | Give each guide one purpose; centralize model/metric rules in architecture |
| Unclear distinction between generated configuration and runtime evidence | Separate implementation, historical validation and pending cloud evidence |
| Makefile, README and CI linted different scripts | Use one complete `ruff check src tests dashboard scripts` command |

## Remaining priorities

1. **Cloud evidence:** sign in, validate/deploy the bundle and retain a successful real Job run. Confirm catalog permissions and outbound network behavior in the actual Free Edition account.
2. **Complete ingestion automation:** in Volume mode schedule the collector/upload/trigger command. Scheduling only a Volume-reading Job is partial automation.
3. **Dashboard evidence:** collect on at least two real dates, publish a categorical chart and time chart, and test access with a reviewer-equivalent account. Synthetic fixtures must stay labeled.
4. **Dedicated repository:** use the directory containing `pyproject.toml` as the repository root. The documentation layout separates operational guides from ignored personal study materials; validate reproduction from the published Git repository.
5. **Warehouse scoring:** Databricks uses liquid clustering rather than static partitioning plus clustering. The supplied rubric's wording may need reviewer interpretation. Do not claim both are implemented or change the layout merely to match terminology.

The initial dataset is small. Full model rebuilds and a per-board snapshot envelope are reasonable for this scope. If it grows, add incremental manifest discovery, chunked Bronze ingestion, historical source membership and a retention policy before claiming large-scale readiness.

## References

- [Supplied rubric's upstream project guide](https://github.com/DataTalksClub/data-engineering-zoomcamp/blob/main/projects/README.md): recheck the applicable cohort's deadlines and final rules before submission.
- [Databricks Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations): serverless/network constraints depend on actual account capability.
- [Liquid clustering](https://docs.databricks.com/aws/en/tables/clustering): explains the alternative to static partitions and ZORDER.
- [Executed checks and limitations](validation.md), [submission checklist](submission-checklist.md).
