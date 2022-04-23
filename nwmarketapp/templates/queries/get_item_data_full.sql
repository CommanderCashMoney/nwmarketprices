WITH most_recent_run AS (
    SELECT
       name_id,
       MAX(run_id) AS max_server_run_id
    FROM prices
    WHERE server_id = {{ server_id }}
    GROUP BY 1
),
lowest_10_prices AS (
    SELECT
        prices.name_id,
        price,
        avail,
        timestamp,
        timestamp::DATE AS price_date,
        ROW_NUMBER() OVER (
           PARTITION BY prices.name_id
           ORDER BY price
       ) as price_rank
    FROM prices
    JOIN most_recent_run ON run_id = max_server_run_id AND prices.name_id = most_recent_run.name_id
    WHERE run_id = max_server_run_id
    ORDER BY price
),
lowest_price_dates AS (
    select
       name_id,
       timestamp::DATE AS price_date,
       MIN(price) AS lowest_price
    FROM prices
    WHERE server_id = {{ server_id }}
    GROUP BY 1, 2
),
price_datetimes AS (
    SELECT
        lowest_price_dates.name_id,
        lowest_price_dates.price_date,
        MAX(timestamp) as price_datetime
    FROM lowest_price_dates
    JOIN prices on prices.name_id = lowest_price_dates.name_id AND timestamp::date = price_date AND lowest_price = price
    WHERE server_id = {{ server_id }}
    GROUP BY 1, 2
),
price_quantities AS (
    SELECT name_id, price_date, MAX(avail) as avail FROM (
        SELECT
            run_id,
            lowest_price_dates.name_id,
            lowest_price_dates.price_date,
            SUM(avail) AS avail
        FROM lowest_price_dates
        JOIN prices ON
            prices.name_id = lowest_price_dates.name_id AND
            timestamp::date = price_date
        WHERE server_id = {{ server_id }}
        GROUP BY 1, 2, 3
    ) calc GROUP BY 1, 2
),
final_prices as (
    select
        name_id,
        lowest_price,
        price_date,
        price_datetime,
        avail,
        AVG(lowest_price) OVER (
            PARTITION BY name_id
            ORDER BY price_date
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        ) AS rolling_average
    from lowest_price_dates
    JOIN price_datetimes USING(name_id, price_date)
    JOIN price_quantities USING(name_id, price_date)
    ORDER BY price_date DESC
)
INSERT INTO price_summaries (server_id, confirmed_name_id, lowest_prices, graph_data)
SELECT
    {{ server_id }} AS server_id,
    name_id AS confirmed_name,
    (
        SELECT JSON_AGG(
            JSON_BUILD_OBJECT(
                'datetime', timestamp,
                'price', price,
                'avail', avail
            )
        )
        FROM lowest_10_prices
        WHERE fp.name_id = lowest_10_prices.name_id AND price_rank < 10
    ) as lowest_prices,
    JSON_AGG(
        JSON_BUILD_OBJECT(
            'price_date', price_datetime,
            'avail', avail,
            'lowest_price', lowest_price,
            'rolling_average', CAST(TO_CHAR(rolling_average, 'FM999999.00') AS NUMERIC)
        )
    ) AS graph_data
FROM final_prices fp
JOIN confirmed_names ON name_id = confirmed_names.id
WHERE name_id is not null
GROUP BY 1, 2
ON CONFLICT (server_id, confirmed_name_id)
DO UPDATE SET
    lowest_prices = excluded.lowest_prices,
    graph_data = excluded.graph_data
