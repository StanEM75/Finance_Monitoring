{{
    config(
        materialized='view',
        schema='STG_FINANCIAL_DATA',
        tags=['staging', 'positions_data'],
    )
}}

-- ================================================================================================================
-- Import data from the raw_open_positions_data table to monitor positions currently held in the portfolio
-- ================================================================================================================

SELECT
    -- Client information
    CLIENTACCOUNTID AS CLIENT_ACCOUNT_ID,

    -- Asset identifiers
    CONID AS ASSET_CONTRACT_ID,
    ASSETCLASS AS ASSET_CLASS,
    SYMBOL AS ASSET_SYMBOL,
    DESCRIPTION AS ASSET_FULL_NAME,

    -- Asset trading information
    LISTINGEXCHANGE AS ASSET_TRADING_PLACE,
    CURRENCYPRIMARY AS ASSET_CURRENCY_USED_FOR_TRADING,
    MULTIPLIER AS ASSET_MULTIPLIER,
    QUANTITY AS ASSET_QUANTITY_HELD,

    -- Asset performance information
    MARKPRICE AS ASSET_CURRENT_VALUE_OF_ONE_UNIT,
    POSITIONVALUE AS ASSET_CURRENT_POSITION_VALUE,
    COSTBASISPRICE AS ASSET_COST_OF_ONE_UNIT,
    COSTBASISMONEY AS ASSET_TOTAL_COST_OF_THE_POSITION,
    FIFOPNLUNREALIZED AS ASSET_UNREALIZED_PROFIT_AND_LOSS,

    -- Date of the record in the source table
    SIDE AS ASSET_POSITION_TYPE
FROM
    {{ source('raw', 'raw_open_positions_data') }}
