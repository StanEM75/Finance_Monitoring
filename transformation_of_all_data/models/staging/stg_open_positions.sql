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
        ClientAccountID AS client_account_id,

        -- Asset identifiers 
        Conid AS asset_contract_id,
        AssetClass AS asset_class,
        Symbol AS asset_symbol,
        Description AS asset_full_name,

        -- Asset trading information
        ListingExchange AS asset_trading_place,
        CurrencyPrimary AS asset_currency_used_for_trading,
        Multiplier AS asset_multiplier,
        Quantity AS asset_quantity_held,

        -- Asset performance information
        MarkPrice AS asset_current_value_of_one_unit,
        PositionValue AS asset_current_position_value,
        CostBasisPrice AS asset_cost_of_one_unit,
        CostBasisMoney AS asset_total_cost_of_the_position,
        FifoPnlUnrealized AS asset_unrealized_profit_and_loss,

        -- Date of the record in the source table
        Side AS asset_position_type
FROM 
        {{ source('raw', 'raw_open_positions_data') }}