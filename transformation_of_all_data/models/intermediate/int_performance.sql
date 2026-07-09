{{
    config(
        materialized='view',
        schema='INT_FINANCIAL_DATA',
        tags=['staging', 'performance_data'],
    )
}}

-- ===============================================================================================================
-- Select only the relevant columns: 
-- 1. Exclude adjusted_cost_of_the_asset that is always equal to 0 for all assets in the portfolio
-- 2. Exclude all short and long term profit and loss columns as we only need the total
-- 3. Exclude asset_code that is always null
-- ===============================================================================================================

SELECT 
        asset_category,
        asset_symbol,
        total_realized_profit_or_loss_for_sale_of_the_asset,
        total_unrealized_profit_or_loss_for_sale_of_the_asset,
        total_profit_or_loss_for_sale_of_the_asset
FROM
        {{ ref('stg_performance') }}
