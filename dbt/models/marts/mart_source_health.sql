{{ daily_table(['board_slug']) }}
with dates as (
    select distinct snapshot_date from {{ ref('stg_ingestion_runs') }}
), attempts as (
    select *, row_number() over (
        partition by board_slug, snapshot_date order by completed_at desc, run_id desc
    ) as attempt_rank
    from {{ ref('stg_ingestion_runs') }}
)
select d.snapshot_date, c.board_slug, c.company_name,
    case when r.run_id is not null then 'complete' else 'unavailable' end as snapshot_status,
    r.run_id as selected_run_id, r.record_count, r.completed_at as last_success_at,
    coalesce(a.status, 'missing') as latest_attempt_status,
    a.error_message as latest_error
from dates d cross join {{ ref('dim_company') }} c
left join {{ ref('int_daily_runs') }} r
  on d.snapshot_date=r.snapshot_date and c.board_slug=r.board_slug
left join attempts a
  on d.snapshot_date=a.snapshot_date and c.board_slug=a.board_slug and a.attempt_rank=1
where c.enabled = true
