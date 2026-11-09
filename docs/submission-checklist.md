# Submission checklist

Use the supplied rubric and your cohort's final instructions. Code and local success alone do not prove cloud deployment or course completion.

## Before publishing

- [ ] Check cohort registration, project deadlines and peer-review requirements. The supplied brief requires three peer reviews and describes extra points separately.
- [x] Create a dedicated repository whose root contains `pyproject.toml`, `databricks.yml` and README.
- [ ] Review the code and explain pagination, daily snapshot selection and counting yourself. Follow the course's originality rules; generated code still needs your understanding.
- [x] Keep `.env`, credentials, raw data, virtual environments and Terraform state out of Git.
- [ ] Run tests, lint, SQL rendering and setup from a fresh source checkout.
- [ ] Run the source audit and review real titles and locations.

## Prove the cloud pipeline

- [x] Deploy the Databricks bundle, or the optional GCP infrastructure.
- [x] Save sanitized evidence of schemas, storage and Job resources created from code.
- [x] Run a complete fresh-data pipeline: API → lake files → Bronze/raw → transformed tables → quality checks.
- [x] Show actual warehouse layout and explain date/source filters. Databricks liquid clustering is an alternative to static partitioning; do not claim both.
- [x] Demonstrate daily ingestion automation. The verified API-mode schedule is active; Volume mode would need a scheduled collector/upload/Job command.
- [x] Document recovery after API, upload and transformation failures.

## Prove the dashboard

- [x] Collect at least two real observation dates. Six dates were verified; replay does not create new dates.
- [x] Include at least two meaningful tiles: a categorical chart and a time-series chart.
- [x] Include titles, observation dates, source coverage and counting definitions in the dashboard asset.
- [x] Explain country overlap and unavailable values. Keep synthetic demo evidence separate.
- [x] Publish the dashboard and add its actual URL and architecture to README.
- [ ] Verify access with a reviewer-equivalent account.
- [x] Add original Databricks dashboard and successful Job screenshots for submission evidence. A screenshot alone may not satisfy interactive-access requirements.
- [ ] Add a separate Bronze/Silver/Gold schema screenshot if required by the submission format.

## Submit

- [ ] Check README commands against committed paths and try a clean clone.
- [ ] Submit the repository/dashboard links on the official cohort platform.
- [ ] Complete required peer reviews before the deadline.

See [project review](project-review.md) for criterion-by-criterion evidence and [validation](validation.md) for checks already recorded.

Official references: [project guide](https://github.com/DataTalksClub/data-engineering-zoomcamp/blob/main/projects/README.md), [2027 cohort](https://github.com/DataTalksClub/data-engineering-zoomcamp/blob/main/cohorts/2027/README.md), [certification](https://datatalks.club/docs/courses/zoomcamp-logistics/certification/). The cohort guide was recorded as draft on 2026-11-04; recheck it rather than treating that historical status as current.
