{{ daily_table(['board_slug', 'role_category']) }}
with geography as (
    select board_slug, job_id, snapshot_date, count(*) as target_country_count
    from {{ ref('int_job_country') }} group by board_slug, job_id, snapshot_date
)
select
    concat(p.job_key, '::', cast(p.snapshot_date as {{ dbt.type_string() }})) as snapshot_key,
    p.run_id, p.board_slug, p.snapshot_date, p.fetched_at, p.job_id, p.job_key,
    p.job_title, p.source_country, p.primary_location, p.department, p.team,
    p.hosted_url, p.workplace_type, r.role_category, r.is_tech_role,
    coalesce(g.target_country_count, 0) as target_country_count,
    coalesce(g.target_country_count, 0) > 0 as is_target_market
from {{ ref('int_daily_postings') }} p
join {{ ref('int_job_role') }} r
  on p.board_slug=r.board_slug and p.job_id=r.job_id and p.snapshot_date=r.snapshot_date
left join geography g
  on p.board_slug=g.board_slug and p.job_id=g.job_id and p.snapshot_date=g.snapshot_date
