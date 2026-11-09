{{ daily_table(['board_slug']) }}
with counts as (
    select snapshot_date, board_slug,
        sum(case when is_tech_role and is_target_market then 1 else 0 end) as tech_postings
    from {{ ref('fct_job_snapshots') }} group by snapshot_date, board_slug
)
select h.snapshot_date, h.board_slug, h.company_name, h.snapshot_status,
    case when h.snapshot_status='complete' then coalesce(c.tech_postings,0) end as tech_postings
from {{ ref('mart_source_health') }} h
left join counts c on h.board_slug=c.board_slug and h.snapshot_date=c.snapshot_date
