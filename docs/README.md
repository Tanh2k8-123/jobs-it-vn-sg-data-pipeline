# Documentation

Start with the project [README](../README.md) for the problem, architecture diagram and quick start. All commands run from the repository root, where `pyproject.toml` lives.

## Main guides

| Guide | Use it to |
|---|---|
| [Architecture](architecture.md) | Understand the data flow, models, counting rules and storage layout |
| [Runbook](runbook.md) | Run stages, replay snapshots and recover from failures |
| [Source audit](source-audit.md) | Inspect the recorded source coverage and field quality |
| [Validation](validation.md) | Check executed tests and the limits of available evidence |
| [Project review](project-review.md) | Compare implementation evidence with the capstone rubric |
| [Submission checklist](submission-checklist.md) | Prepare deployment, dashboard and peer-review evidence |

## Deploy and visualize

Use the selected Databricks path:

1. [Databricks deployment](deployment/databricks.md): tools, OAuth login, bundle deployment, collection and scheduling.
2. [Databricks dashboard](deployment/dashboard.md): queries, chart configuration and reviewer access.

For the optional GCP implementation, follow [GCP setup](optional/gcp.md), [Kestra operations](optional/kestra.md) and [Looker Studio](optional/looker-studio.md).

## File layout

```text
docs/
├── README.md
├── architecture.md
├── runbook.md
├── validation.md
├── source-audit.md
├── source-audit.json
├── project-review.md
├── submission-checklist.md
├── deployment/
│   ├── databricks.md
│   └── dashboard.md
└── optional/
    ├── gcp.md
    ├── kestra.md
    └── looker-studio.md
```

Deployment guides state prerequisites, runnable steps, expected output and recovery actions. Shared metric definitions live in architecture rather than being repeated in each guide.
