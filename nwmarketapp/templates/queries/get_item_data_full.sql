WITH server_prices AS (
    SELECT * FROM prices WHERE server_id = 8 AND timestamp > NOW() - INTERVAL '1 MONTH'
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

ranked_prices AS (
    select price as lowest_price,
           name_id,
           avail,
           timestamp::DATE as price_date,
           timestamp,
           row_number() over (
           PARTITION BY server_prices.name_id, timestamp::DATE
           ORDER BY price
           ) as rank
   from server_prices
    order by name_id, price_date, rank
    ),

price_quantities AS (
     SELECT name_id, price_date, MAX(total_avail) as total_avail FROM (
SELECT
            run_id,
           name_id,
            timestamp::DATE as price_date,
            SUM(avail) AS total_avail
        FROM server_prices
        GROUP BY 1, 2, 3
    ) as calc
      GROUP BY 1, 2
),
final_prices as (
    select
        name_id,
        lowest_price,
        price_date,
        ranked_prices.timestamp,
        avail,
        total_avail,
        rank

    from ranked_prices
    JOIN price_quantities USING(name_id, price_date)
    where ranked_prices.rank <= 10
    GROUP BY 1, 2, 3, 4, 5, 6,7
    ORDER BY price_date DESC, name_id, lowest_price
),
    graph_data AS (
    SELECT
        name_id,
        JSON_AGG(
            JSON_BUILD_OBJECT(
                --names are not great to make it backwards compatible with old JSON entries
                'price_date', timestamp,
                'date_only', timestamp::DATE,
                'avail', total_avail,
                'single_price_avail', avail,
                'lowest_price', lowest_price

            )
        ) AS graph_data
    FROM final_prices
    GROUP BY 1
)
INSERT INTO price_summaries (server_id, confirmed_name_id, lowest_prices, graph_data)
SELECT
    {{ server_id }} AS server_id,
    name_id AS confirmed_name,
    lowest_10_prices.lowest_10,
    graph_data.graph_data
FROM lowest_10_prices
JOIN graph_data USING(name_id)
ON CONFLICT (server_id, confirmed_name_id)
DO UPDATE SET
    lowest_prices = excluded.lowest_prices,
    graph_data = excluded.graph_data
