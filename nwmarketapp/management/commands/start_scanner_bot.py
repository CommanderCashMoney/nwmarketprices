from django.core.management.base import BaseCommand
from django.conf import settings
import discord
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
bot = discord.Bot()
conn = psycopg2.connect(f"dbname={os.getenv('DB_NAME')} user={os.getenv('RDS_USERNAME')} password={os.getenv('RDS_PASSWORD')} host={os.getenv('RDS_HOSTNAME')}")
curr = conn.cursor()


class Command(BaseCommand):
    help = "Run a discord bot"

    def handle(self, *args, **options):
        print('starting bot')

        @bot.slash_command()
        async def scanner_signup(ctx):
            await ctx.send("", view=RegionSelectView())

        @bot.slash_command()
        async def stop_scanner_bot(ctx):
            await ctx.respond("Add Scanner bot stopped", ephemeral=True)
            exit()


        @bot.event
        async def on_ready():
            print(f"{bot.user} is ready and online!")

        bot.run(os.getenv('DISCORDBOT_TOKEN'))


class RegionSelectView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    region_query = "SELECT region FROM servers where region is not null group by region"

    with conn.cursor() as cursor:
        cursor.execute(region_query)
        rows = cursor.fetchall()
    server_options = []
    if rows:
        for row in rows:
            server_options.append(discord.SelectOption(label=row[0]))

    @discord.ui.select(

        placeholder="Select your region",
        min_values=1,
        max_values=1,
        options=server_options

    )
    async def select_callback(self, select,
                              interaction):  # the function called when the user is done selecting options

        region_select = select.values[0]
        await interaction.response.send_message("", view=ServerSelectView(region_select), ephemeral=True)

class ServerDropdown(discord.ui.Select):
    def __init__(self, region_selected):
        super().__init__(min_values=1, max_values=1, placeholder='Select your server.')
        server_query = f"SELECT name, id FROM servers where region=%s order by name"

        with conn.cursor() as cursor:
            cursor.execute(server_query, (region_selected,))
            rows = cursor.fetchall()
        server_options = []
        if rows:
            for row in rows:
                server_options.append(discord.SelectOption(label=row[0], value=str(row[1])))
        self.server_data = rows
        self.options = server_options[:25]

    async def callback(self, interaction):
        respond_message = 'Something went wrong..'
        userid_query = "SELECT ID FROM auth_user where username=%s"
        with conn.cursor() as cursor:
            cursor.execute(userid_query, (interaction.user.name,))
            user_id = cursor.fetchone()
        if user_id:

            group_query = f"""select aug.group_id from auth_user au 
                              join auth_user_groups aug
                              on au.id = aug.user_id
                              where au.id = {user_id[0]}
                              and group_id = 1"""
            with conn.cursor() as cursor:
                cursor.execute(group_query)
                group_id = cursor.fetchone()
            if group_id:
                # user already setup as a scanner
                respond_message = 'You are already set up as a scanner. If you need to switch your server or add a new server please message CashMoney'

            else:
                # user has done intial steps and is not a scanner yet. Add their roles in the database

                server_id = int(interaction.data['values'][0])
                server_name = [tup for tup in self.server_data if tup[1] == server_id]
                server_auth_group_id = server_id + 3  # add +3 here because the auth group ids don't exactly match the server ids
                server_name = server_name[0][0]
                value_list = [(user_id, 1,), (user_id,
                                              server_auth_group_id,)]  # adds two record id=1 for scanner user, and another row for the server
                username = interaction.user.name
                add_scanner_query = "INSERT INTO auth_user_groups (user_id, group_id) VALUES (%s, %s)"
                with conn.cursor() as cursor:
                    try:
                        cursor.executemany(add_scanner_query, value_list)
                        conn.commit()
                        respond_message = f'Thanks {username} You have been added as a scanner to {server_name}'
                    except Exception as e:
                        print(e)
                        respond_message = f'Something went wrong when adding you. Please message CashMoney'

            await interaction.response.send_message(respond_message, ephemeral=True)

        else:
            # user has not setup their password in the wesbite.
            respond_message = f'No account found for: {interaction.user.name} You need to first setup your password on nwmarketprices.com. Please follow the steps listed above.'
            await interaction.response.edit_message(view=RegionSelectView())
            await interaction.followup.send(respond_message, ephemeral=True)

class ServerSelectView(discord.ui.View):

    def __init__(self, region_selected) -> None:
        super().__init__(timeout=None)
        server_select = ServerDropdown(region_selected)
        self.add_item(server_select)

# to run on ssh into eb aws
# $ eb ssh
# $ sudo su -
# $ export $(cat /opt/elasticbeanstalk/deployment/env | xargs)
# $ source /var/app/venv/*/bin/activate
# $ python3 /var/app/current/manage.py start_scanner_bot