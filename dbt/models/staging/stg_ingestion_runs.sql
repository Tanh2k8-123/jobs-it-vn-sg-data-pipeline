select
    run_id, board_slug, snapshot_date, started_at, completed_at, fetched_at,
    status, extraction_status, record_count, page_count, error_message, sha256
from {{ source('lever', 'ingestion_runs') }}
