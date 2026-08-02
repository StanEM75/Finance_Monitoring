{{
    config(
        materialized='ephemeral',
        schema='INT_FINANCIAL_DATA',
        tags=['intermediate', 'positions_data'],
    )
}}

SELECT 
        -- Asset identifier
        asset_symbol,

        -- Asset trading information
        asset_currency_used_for_trading,
        asset_quantity_held,

        -- Asset performance information at the unit level
        asset_current_value_of_one_unit,
        asset_cost_of_one_unit,

        -- Asset performance information at the position level
        asset_current_position_value,
        asset_total_cost_of_the_position,
        asset_unrealized_profit_and_loss
FROM 
        {{ ref('int_open_positions') }}
WHERE
        asset_currency_used_for_trading = 'USD'