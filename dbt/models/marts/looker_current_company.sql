{{ config(materialized='view') }}
select * from {{ ref('mart_daily_company') }}
where snapshot_date = (select max(snapshot_date) from {{ ref('mart_daily_overview') }})
