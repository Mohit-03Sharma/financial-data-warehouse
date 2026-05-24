with prices as (
    select * from {{ ref('stg_stock_prices') }}
),

tickers as (
    select * from {{ ref('dim_tickers') }}
),

dates as (
    select * from {{ ref('dim_dates') }}
),

regimes as (
    select * from {{ ref('dim_economic_regime') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['p.ticker', 'p.price_date']) }} as performance_id,
        p.ticker,
        p.price_date,
        p.open_price,
        p.high_price,
        p.low_price,
        p.close_price,
        p.volume,
        round(p.close_price - p.open_price, 4) as daily_pnl,
        round((p.close_price - p.open_price) / nullif(p.open_price, 0) * 100, 4) as daily_return_pct,
        round(p.high_price - p.low_price, 4) as daily_range,
        t.ticker_id,
        t.sector,
        t.company_name,
        d.date_id,
        d.year,
        d.month,
        d.quarter,
        d.is_weekday,
        r.regime_id,
        r.economic_regime
    from prices p
    left join tickers t on p.ticker = t.ticker
    left join dates d on p.price_date = d.full_date
    left join regimes r on date_trunc(p.price_date, month) = r.month
)

select * from final