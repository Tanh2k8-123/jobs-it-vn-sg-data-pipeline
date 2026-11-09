# Project review

Reviewed on **2026-11-09 (Vietnam time)** against the seven criteria in the project brief supplied with this review. Each criterion allows up to four points, for **28 technical points**. Required peer reviews and their extra points are separate. This is an engineering assessment, not an official grade.

## Assessment

The project runs on Databricks Free Edition with direct API ingestion, Delta tables, a daily schedule and a published dashboard. It preserves source evidence and handles failed/empty/multi-country observations carefully. Remaining submission checks concern reviewer access and cohort requirements rather than cloud implementation.

| Criterion | Max | Evidence in the project | What is needed for full credit |
|---|---:|---|---|
| Problem description | 4 | README explains the users' questions, source scope and metrics | Keep the scope and chart definitions visible |
| Cloud + IaC | 4 | Authenticated bundle deployment manages three schemas, a Volume, Job and dashboard | Retain sanitized deployment evidence |
| Batch orchestration | 4 | Five-task API-to-dashboard Job; active daily 07:00 Vietnam-time schedule and successful scheduled runs | Monitor future runs and quota availability |
| Warehouse | 4 | Real Bronze/Silver/Gold tables, daily history and liquid clustering | Explain the layout and reviewer interpretation |
| Transformations | 4 | 19 shared models, three seeds and successful Spark SQL builds | Explain dependencies and counting rules |
| Dashboard | 4 | Published Databricks dashboard with categories, time series and source health; six observed dates | Verify access with a reviewer-equivalent account |
| Reproducibility | 4 | Dedicated GitHub repo, locked dependencies, CI, clean checkout checks and live deployment | Other accounts still need their own OAuth and warehouse configuration |

No official total is assigned. Cloud resources and scheduled operation are now verified; dashboard access outside the current account and interpretation of the warehouse-layout criterion still need peer-review confirmation.

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
| Local bundle omitted the live dashboard and enabled incompatible schema prefixes | Track the dashboard JSON/refresh task and preserve canonical resource names |

## Remaining priorities

1. **Reviewer access:** test the published dashboard using the account/access conditions required by the cohort. Deployment preserves existing sharing permissions and does not embed owner credentials.
2. **Operation:** monitor future scheduled API collections and Free Edition quotas. If API access becomes restricted, configure and schedule the Volume-mode collector/upload/trigger fallback.
3. **Warehouse scoring:** explain liquid clustering as an alternative to static partitioning plus clustering; the rubric's wording may require reviewer interpretation.
4. **Submission:** check the final cohort dates, complete the originality review and required peer reviews. Cloud deployment does not complete those course steps.

The initial dataset is small. Full model rebuilds and a per-board snapshot envelope are reasonable for this scope. If it grows, add incremental manifest discovery, chunked Bronze ingestion, historical source membership and a retention policy before claiming large-scale readiness.

## References

- [Supplied rubric's upstream project guide](https://github.com/DataTalksClub/data-engineering-zoomcamp/blob/main/projects/README.md): recheck the applicable cohort's deadlines and final rules before submission.
- [Databricks Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations): serverless/network constraints depend on actual account capability.
- [Liquid clustering](https://docs.databricks.com/aws/en/tables/clustering): explains the alternative to static partitions and ZORDER.
- [Executed checks and limitations](validation.md), [submission checklist](submission-checklist.md).
