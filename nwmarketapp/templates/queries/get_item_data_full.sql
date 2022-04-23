WITH server_prices AS (
    SELECT * FROM prices WHERE server_id = {{ server_id }} AND timestamp > NOW() - INTERVAL '1 MONTH'
),
most_recent_run AS (
    SELECT
       name_id,
       MAX(run_id) AS max_server_run_id
    FROM server_prices
    GROUP BY 1
),
lowest_prices AS (
    SELECT
        server_prices.name_id,
        price,
        avail,
        timestamp,
        timestamp::DATE AS price_date,
        ROW_NUMBER() OVER (
           PARTITION BY server_prices.name_id
           ORDER BY price
       ) as price_rank
    FROM server_prices
    JOIN most_recent_run ON run_id = max_server_run_id AND server_prices.name_id = most_recent_run.name_id
    WHERE server_prices.run_id = max_server_run_id
    ORDER BY price
),
lowest_10_prices AS (
    SELECT
        name_id,
        JSON_AGG(
            JSON_BUILD_OBJECT(
                'datetime', timestamp,
                'price', price,
                'avail', avail
            )
        ) AS lowest_10
    FROM lowest_prices WHERE price_rank < 10
    GROUP BY 1
),
lowest_price_dates AS (
    select
       name_id,
       timestamp::DATE AS price_date,
       MIN(price) AS lowest_price
    FROM server_prices
    GROUP BY 1, 2
),
price_datetimes AS (
    SELECT
        lowest_price_dates.name_id,
        lowest_price_dates.price_date,
        MAX(timestamp) as price_datetime
    FROM lowest_price_dates
    JOIN server_prices ON
        server_prices.name_id = lowest_price_dates.name_id AND
        timestamp::date = price_date AND
        lowest_price = price
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
        JOIN server_prices ON
            server_prices.name_id = lowest_price_dates.name_id AND
            timestamp::date = price_date
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
    GROUP BY 1, 2, 3, 4, 5
    ORDER BY price_date DESC
),
graph_data AS (
    SELECT
        name_id,
        JSON_AGG(
            JSON_BUILD_OBJECT(
                'price_date', price_datetime,
                'avail', avail,
                'lowest_price', lowest_price,
                'rolling_average', CAST(TO_CHAR(rolling_average, 'FM999999.00') AS NUMERIC)
            )
        ) AS graph_data
    FROM final_prices
    GROUP BY 1
)
INSERT INTO price_summaries (server_id, confirmed_name_id, lowest_prices, graph_data)
SELECT
    2 AS server_id,
    name_id AS confirmed_name,
    lowest_10_prices.lowest_10,
    graph_data.graph_data
FROM lowest_10_prices
JOIN graph_data USING(name_id)
ON CONFLICT (server_id, confirmed_name_id)
DO UPDATE SET
    lowest_prices = excluded.lowest_prices,
    graph_data = excluded.graph_data
