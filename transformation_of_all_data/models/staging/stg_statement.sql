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
        BrokerName AS broker_name,
        BrokerAddress AS broker_address,
        Title AS document_title,
        Period AS period_covered,
        WhenGenerated AS document_generation_timestamp
FROM 
        {{ source('raw', 'raw_statement_data') }}