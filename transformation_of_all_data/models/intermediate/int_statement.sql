{{
    config(
        materialized='view',
        schema='INT_FINANCIAL_DATA',
        tags=['staging', 'statement_data'],
    )
}}

-- ===============================================================================================================
-- Only keep document_generation_timestamp as it is the only information we want for our DAG
-- ===============================================================================================================

SELECT 
        document_generation_timestamp
FROM
        {{ ref('stg_statement') }}