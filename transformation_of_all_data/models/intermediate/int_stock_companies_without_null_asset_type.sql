{{
    config(
        materialized='ephemeral',
        schema='INT_FINANCIAL_DATA',
        tags=['intermediate', 'stock_data'],
    )
}}

WITH rows_with_null_asset_type AS 
(
    SELECT 
        date,
        symbol,
        asset_type
    FROM 
        {{ ref('int_stock') }}
    WHERE 
        asset_type IS  NULL
)

SELECT 
        DISTINCT
                int_stock.symbol,
                int_stock.asset_type
FROM 
        {{ ref('int_stock') }} int_stock
INNER JOIN
        rows_with_null_asset_type AS rows_with_null_asset_type
        ON int_stock.symbol = rows_with_null_asset_type.symbol
WHERE 
        int_stock.asset_type IS NOT NULL