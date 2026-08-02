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
        ClientAccountID AS client_account_id,
        AccountAlias AS client_account_alias,
        CurrencyPrimary AS client_account_primary_currency,
        AccountType AS client_account_type,
        IBEntity AS client_account_ib_entity,
        TaxLotMatchingMethod AS client_account_tax_lot_matching_method,
FROM
        {{ source('raw', 'raw_statement_data') }}