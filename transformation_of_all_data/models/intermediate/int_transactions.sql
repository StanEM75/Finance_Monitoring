{{ config(materialized='view', schema='INT_FINANCIAL_DATA', tags=['transactions']) }}

-- Statements aggregate by order. Prefer one source per covered account/date.
WITH combined_transactions AS (
    SELECT flex.* FROM {{ ref('stg_transactions') }} AS flex
    WHERE
        NOT EXISTS (
            SELECT 1 FROM {{ source('raw', 'ibkr_history_coverage') }} AS coverage
            WHERE
                flex.client_account_id = coverage.client_account_id
                AND flex.trade_date BETWEEN coverage.start_date AND coverage.end_date
        )
    UNION ALL
    SELECT * FROM {{ ref('stg_historical_transactions') }}
)

SELECT *
FROM
    combined_transactions
WHERE
    asset_class IN ('STK', 'WAR')
    AND currency = 'USD'
