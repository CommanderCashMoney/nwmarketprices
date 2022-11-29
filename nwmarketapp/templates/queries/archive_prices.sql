
insert into price_archive
select * from prices
where timestamp <= '2022-11-7T00:00:0'

delete from prices
where timestamp <= '2022-11-7T00:00:0'