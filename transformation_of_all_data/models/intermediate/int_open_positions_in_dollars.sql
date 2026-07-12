{{
    config(
        materialized='ephemeral',
        schema='INT_FINANCIAL_DATA',
        tags=['intermediate', 'positions_data'],
    )
}}

SELECT 
        asset_category,
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
WHERE 
        currency_used_for_purchasing_the_asset = 'USD'