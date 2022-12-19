
-- find user with zero scans
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

-- find users with less than 5 scans who havnt scanned since 11-21-22
select * from (
                  select max(au.id) as user_id, max(last_login) as last_login, r.username, max(date_joined), max(start_date) as scan_start, count(r.id) as scan_num
                  from auth_user au
                           left join runs r on au.username = r.username
                  where r.username is not null
                    and au.is_active = True

                  group by r.username
                  order by max(r.start_date) desc
              ) as tb1
join auth_user_groups aug on tb1.user_id = aug.user_id
where aug.group_id = 1
and scan_start <= '2022-11-21'
and scan_num < 5
order by scan_start
--order by last_login


-- archive data
insert into price_archive
select * from prices
where timestamp <= '2022-11-20T00:00:0'

delete from prices
where timestamp <= '2022-11-02T00:00:0'
--


---RESET SEQUENCE ID
SELECT MAX(id) FROM confirmed_names;

-- Then run...
-- This should be higher than the last result.
SELECT nextval('confirmed_names_id_seq');

-- If it's not higher... run this set the sequence last to your highest id.


BEGIN;
-- protect against concurrent inserts while you update the counter
LOCK TABLE confirmed_names IN EXCLUSIVE MODE;
-- Update the sequence
SELECT setval('confirmed_names_id_seq', COALESCE((SELECT MAX(id)+1 FROM your_table), 1), false);
COMMIT;
END