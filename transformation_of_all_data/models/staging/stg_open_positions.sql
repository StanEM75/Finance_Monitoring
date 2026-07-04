{{
    config(
        materialized='view',
        schema='STG_FINANCIAL_DATA',
        tags=['staging', 'stock_data'],
    )
}}

--================================================================================================================
-- Import data from the raw_open_positions_data table to monitor positions currently held in the portfolio
-- ===============================================================================================================

SELECT 
        DataDiscriminator AS data_discriminator,
        "Catégorie d'actifs" AS asset_category,
        Devise AS currency_used_for_purchasing_the_asset,
        Symbole AS asset_symbol,
        "Quantité" AS quantity_of_assets_held,
        Mult AS multiplier,
        "Coût" AS avg_cost_of_an_unit_of_the_asset,
        "Coût d'acquisition" AS total_cost_for_all_units_of_the_asset,
        "Cours de clôture" AS latest_closing_price_of_the_asset,
        "Valeur" AS market_value_for_all_units_of_the_asset,
        "P/L non réalisé" AS unrealized_profit_or_loss_for_all_units_of_the_asset,
        Code AS asset_code
FROM 
        {{ source('raw', 'raw_open_positions_data') }}