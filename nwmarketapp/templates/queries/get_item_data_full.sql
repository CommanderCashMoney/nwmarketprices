WITH max_run_dates_per_date AS (
    SELECT
        timestamp::date as price_date,
        MAX(run_id) as max_run_id
    FROM prices
    WHERE server_id = {{ server_id }}
    GROUP BY 1
),
most_recent_run AS (
    SELECT MAX(run_id) AS max_server_run_id
    FROM prices
    WHERE server_id = {{ server_id }}
),
lowest_10_prices AS (
    SELECT
        name_id,
        price,
        avail,
        timestamp,
        timestamp::DATE AS price_date,
        ROW_NUMBER() OVER (
           PARTITION BY name_id
           ORDER BY price
       ) as price_rank
    FROM prices
    JOIN most_recent_run ON run_id = max_server_run_id
    WHERE run_id = max_server_run_id
    ORDER BY price
),
lowest_price_dates AS (
    select
       name_id,
       timestamp::DATE AS price_date,
       timestamp,
       MIN(price) AS lowest_price,
       SUM(CASE WHEN max_run_id = run_id THEN avail ELSE 0 END) AS avail,
       RANK() OVER (
           PARTITION BY name_id
           ORDER BY timestamp::date DESC
       ) as newest
    FROM prices
    LEFT JOIN max_run_dates_per_date ON run_id = max_run_id
    WHERE server_id = {{ server_id }}
    GROUP BY 1, 2,3
),
lowest_prices_recent AS (
    select *,
    AVG(lowest_price) OVER (
        PARTITION BY name_id
        ORDER BY price_date
        ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
    )  AS rolling_average
    from lowest_price_dates
),
final_prices as (
    SELECT
        name_id,
        price_date,
        timestamp,
        avail,
        lowest_price,
        TO_CHAR(rolling_average, 'FM999999.00') AS rolling_average
    FROM lowest_prices_recent
    WHERE newest <= 10
    ORDER BY name_id, price_date
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
            'price_date', timestamp,
            'avail', avail,
            'lowest_price', lowest_price,
            'rolling_average', rolling_average
        )
    ) AS graph_data
FROM final_prices fp
JOIN confirmed_names ON name_id = confirmed_names.id
WHERE name_id is not null
GROUP BY 1, 2