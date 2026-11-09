{{ daily_table() }}
with coverage as (
    select snapshot_date, count(*) as expected_boards,
        sum(case when snapshot_status='complete' then 1 else 0 end) as successful_boards,
        sum(case when latest_attempt_status='failed' then 1 else 0 end) as failed_latest_boards
    from {{ ref('mart_source_health') }} group by snapshot_date
), totals as (
    select snapshot_date, count(*) as all_board_postings,
        sum(case when is_tech_role and is_target_market then 1 else 0 end) as tech_postings,
        sum(case when is_tech_role and target_country_count>1 then 1 else 0 end)
            as multi_country_tech_postings,
        sum(case when is_tech_role and not is_target_market then 1 else 0 end)
            as tech_postings_outside_or_unmapped,
        count(distinct case when is_tech_role and is_target_market then board_slug end)
            as recruiting_companies
    from {{ ref('fct_job_snapshots') }} group by snapshot_date
)
select c.snapshot_date, c.expected_boards, c.successful_boards, c.failed_latest_boards,
    c.successful_boards * 1.0 / nullif(c.expected_boards, 0) as coverage_ratio,
    c.successful_boards = c.expected_boards as is_complete_coverage,
    case when c.successful_boards>0 then coalesce(t.all_board_postings,0) end as all_board_postings,
    case when c.successful_boards>0 then coalesce(t.tech_postings,0) end as tech_postings,
    case when c.successful_boards>0 then coalesce(t.recruiting_companies,0) end
        as recruiting_companies,
    case when c.successful_boards>0 then coalesce(t.multi_country_tech_postings,0) end
        as multi_country_tech_postings,
    case when c.successful_boards>0 then coalesce(t.tech_postings_outside_or_unmapped,0) end
        as tech_postings_outside_or_unmapped
from coverage c left join totals t on c.snapshot_date=t.snapshot_date
