select p.*
from {{ ref('stg_lever_postings') }} p
join {{ ref('int_daily_runs') }} r
  on p.board_slug = r.board_slug and p.run_id = r.run_id and p.snapshot_date = r.snapshot_date
