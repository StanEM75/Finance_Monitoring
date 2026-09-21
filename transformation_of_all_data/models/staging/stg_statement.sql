{{
    config(
        materialized='view',
        schema='STG_FINANCIAL_DATA',
        tags=['staging', 'statement_data'],
    )
}}

--================================================================================================================
-- Import data from the raw_statement_data table to keep only the document_generation_timestamp later on
-- ================================================================================================================

SELECT
    -- Client information
    CLIENTACCOUNTID AS CLIENT_ACCOUNT_ID,
    ACCOUNTALIAS AS CLIENT_ACCOUNT_ALIAS,
    CURRENCYPRIMARY AS CLIENT_ACCOUNT_PRIMARY_CURRENCY,
    ACCOUNTTYPE AS CLIENT_ACCOUNT_TYPE,
    IBENTITY AS CLIENT_ACCOUNT_IB_ENTITY,
    TAXLOTMATCHINGMETHOD AS CLIENT_ACCOUNT_TAX_LOT_MATCHING_METHOD
FROM
    {{ source('raw', 'raw_statement_data') }}
