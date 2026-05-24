with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2010-01-01' as date)",
        end_date="cast('2026-12-31' as date)"
    ) }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['date_day']) }} as date_id,
        date_day as full_date,
        extract(year from date_day) as year,
        extract(month from date_day) as month,
        extract(quarter from date_day) as quarter,
        extract(dayofweek from date_day) as day_of_week,
        format_date('%B', date_day) as month_name,
        case extract(dayofweek from date_day)
            when 1 then false
            when 7 then false
            else true
        end as is_weekday,
        date_trunc(date_day, month) as month_start,
        date_trunc(date_day, quarter) as quarter_start
    from date_spine
)

select * from final