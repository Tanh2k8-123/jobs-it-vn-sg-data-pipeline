select snapshot_date from {{ ref('mart_daily_overview') }}
where coverage_ratio < 0 or coverage_ratio > 1
   or successful_boards > expected_boards or tech_postings < 0
   or (successful_boards=0 and tech_postings is not null)
