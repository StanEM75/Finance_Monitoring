{{
    config(
        materialized='view',
        schema='STG_FINANCIAL_DATA',
        tags=['staging', 'stock_data'],
    )
}}

--================================================================================================================
-- Import data from the raw_stock_data table to keep only the stocks prices later on
-- ===============================================================================================================

SELECT 
        date,
        symbol,
        name AS company_name,
        asset_type,
        price_currency,
        open AS open_price,
        high AS high_price,
        low AS low_price,
        close AS close_price,
        volume AS nb_shares_traded_during_the_day,
        adj_open AS adjusted_open_price,
        adj_high AS adjusted_high_price,
        adj_low AS adjusted_low_price,
        adj_close AS adjusted_close_price,
        adj_volume AS adjusted_nb_shares_traded_during_the_day,
        dividend AS dividend_amount,
        split_factor,
        exchange AS stock_exchange_name,
        exchange_code AS stock_exchange_code
FROM 
        {{ source('raw', 'raw_stock_data') }}  
