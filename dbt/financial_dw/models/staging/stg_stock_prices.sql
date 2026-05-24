with source as (
    select * from {{ source('raw', 'stock_prices') }}
),

cleaned as (
    select
        upper(ticker) as ticker,
        cast(date as date) as price_date,
        round(cast(open as float64), 4) as open_price,
        round(cast(high as float64), 4) as high_price,
        round(cast(low as float64), 4) as low_price,
        round(cast(close as float64), 4) as close_price,
        cast(volume as int64) as volume,
        current_timestamp() as dbt_updated_at
    from source
    where close is not null
        and close > 0
        and date >= '2010-01-01'
)

select * from cleaned