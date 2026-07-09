{{
    config(
        materialized='view',
        schema='INT_FINANCIAL_DATA',
        tags=['staging', 'positions_data'],
    )
}}

--================================================================================================================
-- Select only the relevant columns: 
-- 1. Exclude data_discriminator that is always equal to 'Summary'
-- 2. Exclude multiplier because we don't need to track the split history of a stock
-- 3. Exclude asset_code that is always null
-- ===============================================================================================================

SELECT 
        CASE 
            WHEN asset_category = 'Actions' THEN 'STOCKS'
            WHEN asset_category = 'Fonds' THEN 'FUNDS'
            WHEN asset_category = 'ETF' THEN 'ETFS'
            WHEN asset_category = 'Obligations' THEN 'BONDS'
            WHEN asset_category = 'Options' THEN 'OPTIONS'
            WHEN asset_category = 'Futures' THEN 'FUTURES'
            ELSE asset_category
        END AS asset_category,
        currency_used_for_purchasing_the_asset,
        asset_symbol,
        quantity_of_assets_held,
        avg_cost_of_an_unit_of_the_asset,
        latest_closing_price_of_an_unit_of_the_asset,
        total_cost_for_all_units_of_the_asset,
        market_value_for_all_units_of_the_asset,
        unrealized_profit_or_loss_for_all_units_of_the_asset
FROM 
        {{ ref('int_open_positions') }}