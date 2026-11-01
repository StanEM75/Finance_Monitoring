{{
    config(
        materialized='table',
        schema='DTM_FINANCIAL_DATA',
        tags=['datamart', 'positions_data'],
        post_hook=[
                        "COPY (
                                SELECT * FROM {{ this }}
                        ) TO '{{ env_var('DBT_OUTPUT_DIR', '../data/outputs') }}/profit_by_month.csv'
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
    -- Time information
    MONTHNAME(trade_date) AS trade_month,
    YEAR(trade_date) AS trade_year,

    -- Assets trading information
    SUM(realized_profit_and_loss) AS monthly_realized_profit_and_loss
FROM
    {{ ref('int_sales') }}
GROUP BY
    trade_year,
    trade_month
ORDER BY
    trade_year,
    MONTHNAME(trade_date)
