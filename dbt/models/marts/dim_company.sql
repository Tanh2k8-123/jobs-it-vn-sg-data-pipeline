select board_slug, company_name, enabled, target_markets from {{ ref('companies') }}
