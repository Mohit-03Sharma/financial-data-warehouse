with constituents as (
    select * from {{ ref('stg_sp500_constituents') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['ticker']) }} as ticker_id,
        ticker,
        company_name,
        sector,
        sub_industry,
        date_added
    from constituents
)

select * from final