{{
    config(
        materialized='table',
        schema='DTM_FINANCIAL_DATA',
        tags=['datamart', 'stock_data'],
        post_hook=[
                        "COPY (
                                SELECT * FROM {{ this }}
                        ) TO '/Users/stanislas/Projets/Business/financial-api/data/outputs/stocks_to_pick.csv'
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
        DISTINCT
                asset_symbol
FROM
        {{ ref('fct_open_positions') }}
WHERE
        asset_unrealized_profit_and_loss > 0
        AND asset_symbol IS NOT NULL

