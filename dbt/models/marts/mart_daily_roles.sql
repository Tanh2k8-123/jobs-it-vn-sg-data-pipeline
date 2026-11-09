{{ daily_table(['role_category', 'country_code']) }}
select f.snapshot_date, b.country_code, f.role_category,
    count(distinct f.job_key) as tech_postings
from {{ ref('fct_job_snapshots') }} f
join {{ ref('bridge_job_country') }} b
  on f.board_slug=b.board_slug and f.job_id=b.job_id and f.snapshot_date=b.snapshot_date
where f.is_tech_role group by f.snapshot_date, b.country_code, f.role_category
