select name, max(name_id) as item_id, avg(avgPrice) as price, avg(avgQty) as qty, count(name) as total from (
                  select name, max(name_id) as name_id, avg(price) as avgPrice, avg(qty) as avgQty, server_id
                  from sold_items
                  where status = 'Completed'
                    and timestamp > NOW() - INTERVAL '15 DAYS'
                  group by completion_time, username, name, server_id
                  order by max(name)
              ) as tbl1
group by name
order by total desc
limit 15
