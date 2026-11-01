{{
    config(
        materialized='table',
        schema='DTM_FINANCIAL_DATA',
        tags=['datamart', 'positions_data'],
        post_hook=[
                        "COPY (
                                SELECT * FROM {{ this }}
                        ) TO '{{ env_var('DBT_OUTPUT_DIR', '../data/outputs') }}/profit_by_stock.csv'
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
    -- Assets trading information
    asset_symbol,

    SUM(realized_profit_and_loss) AS stock_realized_profit_and_loss
FROM
    {{ ref('int_sales') }}
GROUP BY
    asset_symbol
ORDER BY
    stock_realized_profit_and_loss DESC
