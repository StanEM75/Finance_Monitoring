{{
    config(
        materialized='table',
        schema='DTM_FINANCIAL_DATA',
        tags=['datamart', 'stock_data'],
        post_hook=[
                        "COPY (
                                SELECT * FROM {{ this }}
                        ) TO '/Users/stanislas/Projets/Business/financial-api/data/outputs/stock_prices.csv'
                        (
                                FORMAT CSV,
                                HEADER TRUE,
                                DELIMITER ',',
                                USE_TMP_FILE TRUE
                        )"
                  ]
    )
}}

SELECT
        -- Asset identifier
        asset_symbol,
        
        -- Stock prices information
        asset_open_price,
        asset_close_price,
        asset_low_price,
        asset_high_price,

        -- Transform date to keep only the date part as we don't need the time part for our analysis
        record_date
FROM 
        {{ ref('int_stock') }}