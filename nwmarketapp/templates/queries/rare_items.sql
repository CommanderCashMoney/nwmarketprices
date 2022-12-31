
SET work_mem = '150MB';

with tbl1 as (
    SELECT id,
           confirmed_name_id,
           server_id,
           jsonb_array_elements(graph_data) AS elem

    FROM price_summaries
    where server_id = {{ server_id}}

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
         group by confirmed_name_id, elem ->> 'date_only'
         order by elem ->> 'date_only'
     ),

      tbl3 as (
         select *,
                coalesce(lag(date_only) over (order by confirmed_name_id, date_only), date_only)           as prev_date,
                coalesce(lag(confirmed_name_id) over (order by confirmed_name_id, date_only),
                         confirmed_name_id)                                                                      as prev_cn,
                ROW_NUMBER() OVER (
                    PARTITION BY confirmed_name_id
                    order by price_date desc
                    )                                                                                            as price_rank

         from tbl2
          ),
     tbl4 as (
         select confirmed_name_id,
               DATE_PART('day', date_only::DATE) - DATE_PART('day', prev_date::DATE) as diff
         from tbl3

         where date_only::DATE > NOW() - INTERVAL '2 DAYS'
           and DATE_PART('day', date_only::DATE) - DATE_PART('day', prev_date::DATE) > 7
           and confirmed_name_id = prev_cn
         order by DATE_PART('day', date_only::DATE) - DATE_PART('day', prev_date::DATE) desc
     )

select diff, price_summaries.*
from tbl4
join price_summaries on tbl4.confirmed_name_id = price_summaries.confirmed_name_id
and server_id = {{ server_id}}




