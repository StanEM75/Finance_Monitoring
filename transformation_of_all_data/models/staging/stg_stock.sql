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
        -- Asset identifiers
        asset_type,
        symbol AS asset_symbol,
        name AS asset_name,

        -- Asset trading information
        exchange_code AS asset_trading_place_code,
        exchange AS asset_exchange_name,
        price_currency AS asset_currency_used_for_trading,

        -- Stock prices information
        open AS asset_open_price,
        high AS asset_high_price,
        low AS asset_low_price,
        close AS asset_close_price,
        volume AS asset_nb_shares_traded_during_the_day,
        adj_open AS asset_adjusted_open_price,
        adj_high AS asset_adjusted_high_price,
        adj_low AS asset_adjusted_low_price,
        adj_close AS asset_adjusted_close_price,
        adj_volume AS asset_adjusted_nb_shares_traded_during_the_day,
        dividend AS asset_dividend_amount,
        split_factor AS asset_split_factor,

        -- Date of the record in the source table
        date AS record_date,

FROM 
        {{ source('raw', 'raw_stock_data') }}  
