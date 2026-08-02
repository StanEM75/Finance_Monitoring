{{
    config(
        severity='warn',
        store_failures=true,
        schema='DBT_TESTS',
        alias='int_stock_open_price_vs_previous_close'
    )
}}

-- ================================================================================================================
-- Check that the opening price does not differ by more than 10% from the previous trading day's closing price.
-- This test helps detect potential data quality issues such as missing stock split adjustments,
-- incorrect prices, or erroneous records returned by the data provider.
-- ================================================================================================================

WITH stock_with_previous_close AS 
(
    SELECT
            record_date,
            asset_symbol,
            asset_open_price,
            asset_close_price,
            LAG(asset_close_price) OVER (
                PARTITION BY asset_symbol
                ORDER BY record_date
            ) AS previous_close_price

    FROM 
            {{ ref('int_stock') }}

),

invalid_rows AS 
(
    SELECT 
            *
    FROM 
            stock_with_previous_close
    WHERE 
            previous_close_price IS NOT NULL
            AND ABS(asset_open_price - previous_close_price) > 0.10 * previous_close_price
)

SELECT 
        *
FROM 
        invalid_rows