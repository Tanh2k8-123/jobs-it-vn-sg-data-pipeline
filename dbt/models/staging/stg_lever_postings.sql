select
    run_id, board_slug, snapshot_date, fetched_at, job_id,
    concat(board_slug, '::', job_id) as job_key,
    {{ json_text('posting_json', '$.text') }} as job_title,
    upper({{ json_text('posting_json', '$.country') }}) as source_country,
    {{ json_text('posting_json', '$.categories.location') }} as primary_location,
    {{ json_string_array('posting_json', '$.categories.allLocations') }} as all_locations,
    {{ json_text('posting_json', '$.categories.department') }} as department,
    {{ json_text('posting_json', '$.categories.team') }} as team,
    {{ json_text('posting_json', '$.hostedUrl') }} as hosted_url,
    case lower({{ json_text('posting_json', '$.workplaceType') }})
        when 'onsite' then 'on-site'
        else lower({{ json_text('posting_json', '$.workplaceType') }})
    end as workplace_type
from {{ source('lever', 'raw_postings') }}
