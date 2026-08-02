{{
    config(
        materialized='table',
        schema='DTM_FINANCIAL_DATA',
        tags=['datamart', 'positions_data'],
        post_hook=[
                        "COPY (
                                SELECT * FROM {{ this }}
                        ) TO '/Users/stanislas/Projets/Business/financial-api/data/outputs/open_positions.csv'
                        (
                                FORMAT CSV,
                                HEADER TRUE,
                                DELIMITER ',',
                                USE_TMP_FILE TRUE
                        )"
                  ]
          )
}}

SELECT 
        -- Asset identifier
        asset_symbol,

        -- Asset trading information
        asset_currency_used_for_trading,
        asset_quantity_held,

        -- Asset performance information at the unit level
        asset_current_value_of_one_unit,
        asset_cost_of_one_unit,

        -- Asset performance information at the position level
        asset_current_position_value,
        asset_total_cost_of_the_position,
        asset_unrealized_profit_and_loss
FROM
        {{ ref('int_open_positions_in_dollars') }}
ORDER BY
        asset_unrealized_profit_and_loss DESC
