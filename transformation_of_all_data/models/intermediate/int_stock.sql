{{
    config(
        materialized='view',
        schema='INT_FINANCIAL_DATA',
        tags=['intermediate', 'stock_data'],
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
        -- Transform date to keep only the date part as we don't need the time part for our analysis
        DATE(date) as date,
        symbol,
        company_name,
        asset_type,
        price_currency,
        open_price,
        close_price,
        low_price,
        high_price,
        stock_exchange_code
FROM 
        {{ ref('stg_stock') }}