
-- find inactive users
select * from (
                  select au.id as user_id, last_login, au.username, date_joined
                  from auth_user au
                           left join runs r on au.username = r.username
                  where r.username is null
                    and au.is_active = True
                  order by last_login
              ) as tb1
join auth_user_groups aug on tb1.user_id = aug.user_id
where aug.group_id = 1
order by last_login


-- archive data
insert into price_archive
select * from prices
where timestamp <= '2022-11-02T00:00:0'

delete from prices
where timestamp <= '2022-11-02T00:00:0'
--