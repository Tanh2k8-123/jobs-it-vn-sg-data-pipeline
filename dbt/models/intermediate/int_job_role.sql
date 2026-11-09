with candidates as (
    select p.board_slug, p.job_id, p.snapshot_date, r.role_category,
        row_number() over (
            partition by p.board_slug, p.job_id, p.snapshot_date order by r.priority
        ) as role_rank
    from {{ ref('int_daily_postings') }} p
    left join {{ ref('role_rules') }} r
      on {{ matches("lower(coalesce(p.job_title, ''))", 'r.title_pattern') }}
)
select board_slug, job_id, snapshot_date,
    coalesce(role_category, 'Unclassified') as role_category,
    role_category is not null as is_tech_role
from candidates where role_rank = 1
