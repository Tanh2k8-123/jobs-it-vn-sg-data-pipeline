select r.board_slug, r.run_id, r.record_count, count(p.job_id) as loaded_count
from {{ ref('stg_ingestion_runs') }} r
left join {{ ref('stg_lever_postings') }} p
  on r.board_slug=p.board_slug and r.run_id=p.run_id and r.snapshot_date=p.snapshot_date
where r.status='success'
group by r.board_slug, r.run_id, r.record_count
having count(p.job_id) != r.record_count
