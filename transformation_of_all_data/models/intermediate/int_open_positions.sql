{{
    config(
        materialized='view',
        schema='INT_FINANCIAL_DATA',
        tags=['intermediate', 'positions_data'],
    )
}}

-- ===============================================================================================================
-- Select only the relevant columns: 
-- 1. Exclude client information, which is useless for the analysis (only 1 client=me).
-- 2. Exclude all identifiers except asset_symbol because the other ones would be useful only if two stock can
-- share the same symbol, which is not the case in our dataset.
-- 3. Exclude all asset trading information, which is useless for the analysis.
-- 4. Exclude asset_position_type because it is always equal to Long.
-- 5. Split value information at the unit and position levels to make it easier to compute the profit and loss later on.
-- ===============================================================================================================

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
        {{ ref('stg_open_positions') }}