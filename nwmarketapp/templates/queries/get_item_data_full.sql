
WITH server_prices AS (
    SELECT * FROM prices WHERE server_id = {{ server_id }} AND timestamp > NOW() - INTERVAL '1 MONTH' and avail is not null
),
server_prices_buyorders AS (SELECT * FROM prices WHERE server_id = 2 AND timestamp > NOW() - INTERVAL '1 MONTH' and avail is null),

most_recent_run AS (
    SELECT
       name_id,
       MAX(run_id) AS max_server_run_id
    FROM server_prices
    GROUP BY 1
),
     most_recent_run_buyorders AS (
    SELECT
       name_id,
       MAX(run_id) AS max_server_run_id
    FROM server_prices_buyorders
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

highest_buyorder AS (
    SELECT
        server_prices_buyorders.name_id,
        price as buyorder_price,
        qty,
        --timestamp,
        timestamp::DATE AS price_date,
        ROW_NUMBER() OVER (
           PARTITION BY server_prices_buyorders.name_id
           ORDER BY price desc
       ) as buyorder_price_rank
    FROM server_prices_buyorders
    JOIN most_recent_run_buyorders ON run_id = max_server_run_id AND server_prices_buyorders.name_id = most_recent_run_buyorders.name_id
    WHERE server_prices_buyorders.run_id = max_server_run_id
    ORDER BY price desc
),

lowest_10_prices AS (
    SELECT
        lp.name_id,
        JSON_AGG(
            JSON_BUILD_OBJECT(
                'datetime', timestamp,
                'price', lp.price,
                'avail', avail,
                'qty', qty,
                'buy_order_price', buyorder_price
            )
        ) AS lowest_10
    FROM lowest_prices lp
    left join highest_buyorder hb on lp.name_id = hb.name_id and lp.price_rank = hb.buyorder_price_rank and lp.price_date = hb.price_date
    WHERE lp.price_rank < 10
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
 ranked_buy_orders AS (
    select price as highest_buy_order,
           name_id,
           qty,
           timestamp::DATE as price_date,
           timestamp,
           row_number() over (
           PARTITION BY server_prices_buyorders.name_id, timestamp::DATE
           ORDER BY price desc
           ) as rank
   from server_prices_buyorders
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
        rp.name_id,
        rp.lowest_price,
        rp.price_date,
        rp.timestamp,
        rp.avail,
        total_avail,
        rp.rank as price_rank,
        rbo.highest_buy_order,
        rbo.qty,
        rbo.rank as buyorder_rank,
           rbo.price_date as bo_pricedate


    from ranked_prices rp
    JOIN price_quantities USING(name_id, price_date)
    left JOIN ranked_buy_orders rbo on rp.name_id = rbo.name_id and rp.rank = rbo.rank and rbo.price_date = rp.price_date
    where rp.rank <= 10
    GROUP BY 1, 2, 3, 4, 5, 6,7, 8, 9, 10,11
    ORDER BY price_date DESC, rp.name_id, rp.lowest_price
),
-- select * from final_prices
-- --select * from ranked_prices
-- --select * from ranked_buy_orders
-- where name_id = 1463
-- order by price_date desc, lowest_price



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
                'lowest_price', lowest_price,
                'highest_buy_order', highest_buy_order,
                'qty', qty

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
