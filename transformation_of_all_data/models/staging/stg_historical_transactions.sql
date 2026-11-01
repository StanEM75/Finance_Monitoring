{{ config(materialized='view', schema='STG_FINANCIAL_DATA', tags=['transactions']) }}

SELECT
    'activity_statement_order' AS data_source,
    CAST(clientaccountid AS VARCHAR) AS client_account_id,
    CAST(transactionid AS VARCHAR) AS transaction_id,
    CAST(tradeid AS VARCHAR) AS trade_id,
    CAST(conid AS VARCHAR) AS asset_contract_id,
    symbol AS asset_symbol,
    description AS asset_full_name,
    assetclass AS asset_class,
    currencyprimary AS currency,
    CAST(datetime AS VARCHAR) AS trade_datetime,
    "Buy/Sell" AS buy_sell,
    "Open/CloseIndicator" AS open_close_indicator,
    CAST(quantity AS DOUBLE) AS quantity,
    CAST(tradeprice AS DOUBLE) AS trade_price,
    CAST(proceeds AS DOUBLE) AS proceeds,
    CAST(taxes AS DOUBLE) AS taxes,
    CAST(ibcommission AS DOUBLE) AS commission,
    ibcommissioncurrency AS commission_currency,
    CAST(netcash AS DOUBLE) AS net_cash,
    CAST(costbasis AS DOUBLE) AS cost_basis,
    CAST(fifopnlrealized AS DOUBLE) AS realized_profit_and_loss,
    CAST(STRPTIME(CAST(tradedate AS VARCHAR), '%Y%m%d') AS DATE) AS trade_date
FROM {{ source('raw', 'raw_historical_transactions_data') }}
