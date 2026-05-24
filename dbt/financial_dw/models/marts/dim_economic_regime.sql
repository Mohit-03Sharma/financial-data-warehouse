with fred as (
    select * from {{ ref('stg_fred_indicators') }}
),

monthly_indicators as (
    select
        date_trunc(indicator_date, month) as month,
        max(case when series_id = 'FEDFUNDS' then indicator_value end) as fed_funds_rate,
        max(case when series_id = 'CPIAUCSL' then indicator_value end) as cpi,
        max(case when series_id = 'UNRATE' then indicator_value end) as unemployment_rate
    from fred
    group by 1
),

with_yoy_cpi as (
    select
        *,
        lag(cpi, 12) over (order by month) as cpi_year_ago,
        (cpi - lag(cpi, 12) over (order by month))
            / nullif(lag(cpi, 12) over (order by month), 0) * 100 as cpi_yoy_pct
    from monthly_indicators
),

classified as (
    select
        {{ dbt_utils.generate_surrogate_key(['month']) }} as regime_id,
        month,
        fed_funds_rate,
        cpi_yoy_pct as inflation_rate_yoy,
        unemployment_rate,
        case
            when cpi_yoy_pct > 4 and fed_funds_rate > 3 then 'High Inflation / Tightening'
            when cpi_yoy_pct > 4 and fed_funds_rate <= 3 then 'High Inflation / Accommodative'
            when fed_funds_rate < 1 then 'Near-Zero Rates'
            when unemployment_rate > 7 then 'High Unemployment'
            else 'Normal'
        end as economic_regime
    from with_yoy_cpi
)

select * from classified