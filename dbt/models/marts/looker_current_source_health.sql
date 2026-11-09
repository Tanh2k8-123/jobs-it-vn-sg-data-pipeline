{{ config(materialized='view') }}
select * from {{ ref('mart_source_health') }}
where snapshot_date = (select max(snapshot_date) from {{ ref('mart_daily_overview') }})
