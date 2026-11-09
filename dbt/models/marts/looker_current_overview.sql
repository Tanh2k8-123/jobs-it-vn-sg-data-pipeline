{{ config(materialized='view') }}
select * from {{ ref('mart_daily_overview') }}
where snapshot_date = (select max(snapshot_date) from {{ ref('mart_daily_overview') }})
