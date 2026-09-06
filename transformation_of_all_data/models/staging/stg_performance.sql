{{
    config(
        materialized='view',
        schema='STG_FINANCIAL_DATA',
        tags=['staging', 'performance_data'],
    )
}}

-- ===================================================================================================================================================
-- Import data from the raw_performance_data table to check profit and loss for assets sold in the past and for assets still held in the portfolio
-- ===================================================================================================================================================

SELECT
    -- Client information
    CLIENTACCOUNTID AS CLIENT_ACCOUNT_ID,

    -- Asset identifiers
    CONID AS ASSET_CONTRACT_ID,
    ISIN AS ASSET_INTERNATIONAL_SECURITY_IDENTIFICATION_NUMBER,
    ASSETCLASS AS ASSET_CLASS,
    SYMBOL AS ASSET_SYMBOL,
    DESCRIPTION AS ASSET_FULL_NAME,

    -- Asset trading information
    LISTINGEXCHANGE AS ASSET_TRADING_PLACE,
    MULTIPLIER AS ASSET_MULTIPLIER,
    COSTADJUSTMENT AS ASSET_COST_ADJUSTMENT,

    -- Asset performance information
    TOTALREALIZEDPNL AS ASSET_TOTAL_REALIZED_PROFIT_AND_LOSS,
    TOTALUNREALIZEDPNL AS ASSET_TOTAL_UNREALIZED_PROFIT_AND_LOSS,
    TOTALFIFOPNL AS ASSET_TOTAL_FIFO_METHOD_PROFIT_AND_LOSS,
    TRANSFERREDPNL AS ASSET_TRANSFERRED_PROFIT_AND_LOSS,

    -- Date of the record in the source table
    REPORTDATE AS ROW_RECORD_DATE
FROM
    {{ source('raw', 'raw_performance_data') }}
WHERE
    SYMBOL IS NOT NULL
