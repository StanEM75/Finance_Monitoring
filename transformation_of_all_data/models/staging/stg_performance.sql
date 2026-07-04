{{
    config(
        materialized='view',
        schema='STG_FINANCIAL_DATA',
        tags=['staging', 'performance_data'],
    )
}}

--====================================================================================================================================================
-- Import data from the raw_performance_data table to check profit and loss for assets sold in the past and for assets still held in the portfolio
-- ===================================================================================================================================================

SELECT 
        "Catégorie d'actifs" AS asset_category,
        Symbole AS asset_symbol,
        "Aj. coût" AS adjusted_cost_of_the_asset,
        "Realisé Profit C/T" AS realized_short_term_profit_for_sale_of_the_asset,
        "Realisé Perte C/T" AS realized_loss_for_sale_of_the_asset, 
        "Realisé Profit L/T" AS realized_long_term_profit_for_sale_of_the_asset,
        "Realisé Perte L/T" AS realized_long_term_loss_for_sale_of_the_asset,
        "Realisé Total" AS total_realized_profit_or_loss_for_sale_of_the_asset,
        "Non réalisé Profit C/T" AS unrealized_short_term_profit_for_sale_of_the_asset,
        "Non réalisé Perte C/T" AS unrealized_short_term_loss_for_sale_of_the_asset,
        "Non réalisé Profit L/T" AS unrealized_long_term_profit_for_sale_of_the_asset,
        "Non réalisé Perte L/T" AS unrealized_long_term_loss_for_sale_of_the_asset,
        "Non réalisé Total" AS total_unrealized_profit_or_loss_for_sale_of_the_asset,
        "Total" AS total_profit_or_loss_for_sale_of_the_asset,
        "Code" AS asset_code
FROM 
        {{ source('raw_data', 'raw_performance_data') }}