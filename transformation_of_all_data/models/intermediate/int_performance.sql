{{
    config(
        materialized='view',
        schema='INT_FINANCIAL_DATA',
        tags=['staging', 'performance_data'],
    )
}}

-- ===============================================================================================================
-- Select only the relevant columns: 
-- 1. Exclude client information, which is useless for the analysis (only 1 client=me).
-- 2. Exclude all identifiers except asset_symbol because the other ones would be useful only if two stock can
-- share the same symbol, which is not the case in our dataset.
-- 3. Exclude all asset trading information, which is useless for the analysis.
-- 4. Exclude asset_transferred_profit_and_loss because it is always equal to 0 in the dataset.
-- 5. Exclude row_record_date because it is only useful for freshness test.
-- ===============================================================================================================

SELECT 
        -- Asset identifier
        asset_symbol,

        -- Asset performance information
        asset_total_realized_profit_and_loss,
        asset_total_unrealized_profit_and_loss,
        asset_total_fifo_method_profit_and_loss
FROM
        {{ ref('stg_performance') }}
