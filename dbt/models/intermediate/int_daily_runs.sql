with ranked as (
    select r.*, row_number() over (
        partition by r.board_slug, r.snapshot_date order by r.completed_at desc, r.run_id desc
    ) as run_rank
    from {{ ref('stg_ingestion_runs') }} r
    join {{ ref('companies') }} c on r.board_slug=c.board_slug
    where r.status = 'success' and r.extraction_status = 'complete' and c.enabled = true
)
select run_id, board_slug, snapshot_date, completed_at, record_count
from ranked where run_rank = 1
