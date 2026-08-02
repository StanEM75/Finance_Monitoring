{{
    config(
        materialized='view',
        schema='INT_FINANCIAL_DATA',
        tags=['intermediate', 'stock_data'],
    )
}}

-- ===============================================================================================================
-- Select only the relevant columns: 
-- 1. Exclude all identifiers except asset_symbol because the other ones would be useful only if two stock can
-- share the same symbol, which is not the case in our dataset.
-- 2. Exclude all adjusted prices as they seem inconsistent sometimes (e.g. adj_open = 785 and adj_close = 156 for NOW)
-- 3. Exclude volume as it is not relevant for our analysis
-- 4. Exclude dividend as we don't need to want to track the dividend history of a stock
-- 5. Exclude split_factor as we don't need to track the split history of a stock
-- ===============================================================================================================

SELECT
        -- Asset identifier
        asset_symbol,
        
        -- Stock prices information
        asset_open_price,
        asset_close_price,
        asset_low_price,
        asset_high_price,

        -- Transform date to keep only the date part as we don't need the time part for our analysis
        DATE(record_date) as record_date
FROM 
        {{ ref('stg_stock') }}