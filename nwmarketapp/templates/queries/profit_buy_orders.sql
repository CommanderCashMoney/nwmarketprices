select cn.name, lpdata->>'buy_order_price' as bo_price,lpdata->>'qty' as qty ,lpdata->>'price' as sell_price, lpdata->>'avail' as avail, servers.name, abs(round((cast(lpdata->>'price' as decimal) / cast(lpdata->>'buy_order_price' as decimal) * 100),0)-100) as diff  from (
                  select jsonb_array_elements(lowest_prices) as lpdata,
                         confirmed_name_id,
                         server_id
                         from price_summaries

              ) as lp
join confirmed_names cn on cn.id = lp.confirmed_name_id
join servers on server_id = servers.id

where
      server_id in ({{server_id}})
and cast(lpdata->>'avail' as int) > 5
and cast(lpdata->>'price' as decimal) < (cast(lpdata->>'buy_order_price' as decimal) - (cast(lpdata->>'buy_order_price' as decimal) * 8.0 / 100.0))
order by diff desc