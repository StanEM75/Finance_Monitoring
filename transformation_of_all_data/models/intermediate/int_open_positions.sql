{{
    config(
        materialized='view',
        schema='INT_FINANCIAL_DATA',
        tags=['staging', 'positions_data'],
    )
}}

--================================================================================================================
-- Select only the relevant columns: 
-- 1. Exclude all adjusted prices as they seem inconsistent sometimes (e.g. adj_open = 785 and adj_close = 156 for NOW)
-- 2. Exclude volume as it is not relevant for our analysis
-- 3. Exclude dividend as we don't need to want to track the dividend history of a stock
-- 4. Exclude split_factor as we don't need to track the split history of a
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