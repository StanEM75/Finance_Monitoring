{{
    config(
        materialized='table',
        schema='DTM_FINANCIAL_DATA',
        tags=['datamart', 'stock_data'],
    )
}}

WITH positive_positions AS (
    SELECT 
            asset_symbol
    FROM
            {{ ref('fct_open_positions') }}
    WHERE
            unrealized_profit_or_loss_for_all_units_of_the_asset > 0
)

SELECT
        fct_stock_prices.symbol
FROM 
        {{ ref('fct_stock_prices') }} fct_stock_prices
INNER JOIN
        positive_positions
        ON fct_stock_prices.symbol = positive_positions.asset_symbol
