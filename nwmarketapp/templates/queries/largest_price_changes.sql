SET work_mem = '150MB';


with tbl1 as (
    SELECT id,
           confirmed_name_id,
           server_id,
           jsonb_array_elements(graph_data) AS elem
    FROM price_summaries
    where server_id = {{ server_id }}
),
     tbl2 as (
         select max(id)                                                                                as id,
                confirmed_name_id,
                max(server_id)                                                                         as server_id,
                elem ->> 'date_only'                                                                   as date_only,
                min(elem ->> 'lowest_price')                                                           as lowest_price,
                min(elem ->> 'price_date')                                                             as price_date,
                min(elem ->> 'avail')                                                                  as avail,
                min(elem ->> 'qty')                                                                    as qty,
                min(elem ->> 'highest_buy_order')                                                      as highest_buy_order,
                min(elem ->> 'single_price_avail')                                                     as single_price_avail,
                CAST(min(elem ->> 'avail') AS integer) * avg(CAST(elem ->> 'lowest_price' AS decimal)) as market_cap
         from tbl1
         where cast(elem ->> 'date_only' as date) > NOW() - INTERVAL '7 DAYS'
         group by confirmed_name_id, elem ->> 'date_only'

         order by elem ->> 'date_only'
     ),

     tbl3 as (
         select *,
                coalesce(lag(lowest_price) over (order by confirmed_name_id, date_only), lowest_price)           as prev_price,
                coalesce(lag(confirmed_name_id) over (order by confirmed_name_id, date_only),
                         confirmed_name_id)                                                                      as prev_cn,
                ROW_NUMBER() OVER (
                    PARTITION BY confirmed_name_id
                    order by price_date desc
                    )                                                                                            as price_rank

         from tbl2),

     tbl4 as (
         select *
         from tbl3
         where confirmed_name_id = prev_cn
           and price_rank = 1
     ),
     tbl5 as (
         select tbl4.confirmed_name_id


         from tbl4
         where ((cast(lowest_price as decimal) - cast(prev_price as decimal)) / cast(prev_price as decimal)) *
               100.0 not between -50 and 1000
--and  cast(price_date as timestamp) > NOW() - INTERVAL '4 DAYS'
           and market_cap > 50
           and cast(lowest_price as decimal) >= 0.1
         group by 1
     )

select price_summaries.*
from tbl5
    join price_summaries on tbl5.confirmed_name_id = price_summaries.confirmed_name_id
    and price_summaries.server_id = {{ server_id}}