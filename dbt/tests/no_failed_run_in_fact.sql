select f.snapshot_key
from {{ ref('fct_job_snapshots') }} f
join {{ ref('stg_ingestion_runs') }} r on f.board_slug=r.board_slug and f.run_id=r.run_id
where r.status != 'success' or r.extraction_status != 'complete'
