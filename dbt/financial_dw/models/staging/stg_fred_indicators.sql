with source as (
    select * from {{ source('raw', 'fred_economic_indicators') }}
),

cleaned as (
    select
        series_id,
        cast(date as date) as indicator_date,
        cast(value as float64) as indicator_value,
        case series_id
            when 'FEDFUNDS' then 'Federal Funds Rate'
            when 'CPIAUCSL' then 'CPI Inflation'
            when 'GDP' then 'GDP (Billions USD)'
            when 'UNRATE' then 'Unemployment Rate'
        end as indicator_name,
        case series_id
            when 'FEDFUNDS' then 'monthly'
            when 'CPIAUCSL' then 'monthly'
            when 'GDP' then 'quarterly'
            when 'UNRATE' then 'monthly'
        end as frequency,
        current_timestamp() as dbt_updated_at
    from source
    where value is not null
)

select * from cleaned