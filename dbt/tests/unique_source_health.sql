select snapshot_date, board_slug from {{ ref('mart_source_health') }}
group by snapshot_date, board_slug having count(*) > 1
