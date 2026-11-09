{{ daily_table(['country_code']) }}
with countries as (
    select distinct country_code from {{ ref('country_location_rules') }}
), counts as (
    select f.snapshot_date, b.country_code, count(distinct f.job_key) as tech_postings,
        count(distinct f.board_slug) as recruiting_companies
    from {{ ref('fct_job_snapshots') }} f
    join {{ ref('bridge_job_country') }} b
      on f.board_slug=b.board_slug and f.job_id=b.job_id and f.snapshot_date=b.snapshot_date
    where f.is_tech_role group by f.snapshot_date, b.country_code
)
select o.snapshot_date, c.country_code,
    case when o.successful_boards>0 then coalesce(n.tech_postings,0) end as tech_postings,
    case when o.successful_boards>0 then coalesce(n.recruiting_companies,0) end
        as recruiting_companies,
    o.coverage_ratio, o.is_complete_coverage
from {{ ref('mart_daily_overview') }} o cross join countries c
left join counts n on o.snapshot_date=n.snapshot_date and c.country_code=n.country_code
