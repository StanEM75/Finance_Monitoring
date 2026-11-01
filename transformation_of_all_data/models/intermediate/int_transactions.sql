{{ config(materialized='view', schema='INT_FINANCIAL_DATA', tags=['transactions']) }}

-- Statements aggregate by order. Prefer one source per covered account/date.
WITH combined_transactions AS (
    SELECT
        flex.data_source,
        flex.client_account_id,
        flex.transaction_id,
        flex.trade_id,
        flex.asset_contract_id,
        flex.asset_symbol,
        flex.asset_full_name,
        flex.asset_class,
        flex.currency,
        flex.trade_datetime,
        flex.buy_sell,
        flex.open_close_indicator,
        flex.quantity,
        flex.trade_price,
        flex.proceeds,
        flex.taxes,
        flex.commission,
        flex.commission_currency,
        flex.net_cash,
        flex.cost_basis,
        flex.realized_profit_and_loss,
        flex.trade_date
    FROM {{ ref('stg_transactions') }} AS flex
    WHERE
        NOT EXISTS (
            SELECT 1 FROM {{ source('raw', 'ibkr_history_coverage') }} AS coverage
            WHERE
                flex.client_account_id = coverage.client_account_id
                AND flex.trade_date BETWEEN coverage.start_date AND coverage.end_date
        )
    UNION ALL
    SELECT
        data_source,
        client_account_id,
        transaction_id,
        trade_id,
        asset_contract_id,
        asset_symbol,
        asset_full_name,
        asset_class,
        currency,
        trade_datetime,
        buy_sell,
        open_close_indicator,
        quantity,
        trade_price,
        proceeds,
        taxes,
        commission,
        commission_currency,
        net_cash,
        cost_basis,
        realized_profit_and_loss,
        trade_date
    FROM {{ ref('stg_historical_transactions') }}
)

SELECT
    data_source,
    client_account_id,
    transaction_id,
    trade_id,
    asset_contract_id,
    asset_symbol,
    asset_full_name,
    asset_class,
    currency,
    trade_datetime,
    buy_sell,
    open_close_indicator,
    quantity,
    trade_price,
    proceeds,
    taxes,
    commission,
    commission_currency,
    net_cash,
    cost_basis,
    realized_profit_and_loss,
    trade_date
FROM
    combined_transactions
WHERE
    asset_class IN ('STK', 'WAR')
    AND currency = 'USD'
