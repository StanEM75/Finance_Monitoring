{{
    config(
        materialized='table',
        schema='DTM_FINANCIAL_DATA',
        tags=['datamart', 'stock_data'],
    )
}}

SELECT
        date,
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
        {{ ref('int_stock') }}