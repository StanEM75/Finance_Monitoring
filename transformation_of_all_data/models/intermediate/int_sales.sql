{{ config(materialized='view', schema='INT_FINANCIAL_DATA', tags=['transactions', 'sales']) }}

SELECT
    asset_symbol,
    trade_date,
    buy_sell,
    quantity,
    realized_profit_and_loss
FROM
    {{ ref('int_transactions') }}
WHERE
    buy_sell = 'SELL'
