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
        ClientAccountID AS client_account_id,

        -- Asset identifiers 
        Conid AS asset_contract_id,
        ISIN AS asset_international_security_identification_number,
        AssetClass AS asset_class,
        Symbol AS asset_symbol,
        Description AS asset_full_name,

        -- Asset trading information
        ListingExchange AS asset_trading_place,
        Multiplier AS asset_multiplier,
        CostAdjustment AS asset_cost_adjustment,

        -- Asset performance information
        TotalRealizedPnl AS asset_total_realized_profit_and_loss,
        TotalUnrealizedPnl AS asset_total_unrealized_profit_and_loss,
        TotalFifoPnl AS asset_total_fifo_method_profit_and_loss,
        TransferredPnl AS asset_transferred_profit_and_loss,

        -- Date of the record in the source table
        ReportDate AS row_record_date
FROM 
        {{ source('raw', 'raw_performance_data') }}
WHERE 
        Symbol IS NOT NULL