WITH lowest_price_dates AS (
    select
       name_id,
       timestamp::date as price_date,
       MIN(price) as lowest_price,
       RANK() OVER (
           PARTITION BY name_id
           ORDER BY timestamp::date DESC
       ) as newest
    from prices
    WHERE server_id=1
    GROUP BY 1, 2
),
lowest_prices_recent AS (
    select *,
    AVG(lowest_price) OVER (
        PARTITION BY name_id
        ORDER BY price_date
        ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
    )  AS rolling_average
    from lowest_price_dates
)
SELECT
    name_id,
    price_date,
    lowest_price,
    TO_CHAR(rolling_average, 'FM999999.00') AS rolling_average
FROM lowest_prices_recent
WHERE newest <= 10
ORDER BY name_id, price_date;
