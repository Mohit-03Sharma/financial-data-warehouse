with source as (
    select * from {{ source('raw', 'sp500_constituents') }}
),

cleaned as (
    select
        upper(ticker) as ticker,
        company_name,
        sector,
        sub_industry,
        cast(date_added as date) as date_added,
        current_timestamp() as dbt_updated_at
    from source
    where ticker is not null
)

select * from cleaned