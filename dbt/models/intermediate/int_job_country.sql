with locations as (
    select board_slug, job_id, snapshot_date, primary_location as location_value
    from {{ ref('int_daily_postings') }}
    union all
    select p.board_slug, p.job_id, p.snapshot_date, location_value
    from {{ ref('int_daily_postings') }} p
    {{ unnest_locations('p.all_locations') }}
), mapped as (
    select l.board_slug, l.job_id, l.snapshot_date, rules.country_code
    from locations l
    join {{ ref('country_location_rules') }} rules
      on {{ matches("lower(coalesce(l.location_value, ''))", 'rules.location_pattern') }}
    union all
    select board_slug, job_id, snapshot_date, source_country as country_code
    from {{ ref('int_daily_postings') }} where source_country in ('VN', 'SG')
)
select distinct board_slug, job_id, snapshot_date, country_code
from mapped
