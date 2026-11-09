{{ daily_table(['country_code', 'board_slug']) }}
select
    concat(board_slug, '::', job_id, '::', cast(snapshot_date as {{ dbt.type_string() }}),
           '::', country_code) as bridge_key,
    board_slug, job_id, snapshot_date, country_code
from {{ ref('int_job_country') }}
