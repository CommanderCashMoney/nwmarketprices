from django.core.management.base import BaseCommand
import discord
import os
from dotenv import load_dotenv
import psycopg2
import logging


load_dotenv()
bot = discord.Bot(intents=discord.Intents.all())
conn = psycopg2.connect(f"dbname={os.getenv('DB_NAME')} user={os.getenv('RDS_USERNAME')} password={os.getenv('RDS_PASSWORD')} host={os.getenv('RDS_HOSTNAME')}")
curr = conn.cursor()

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

def get_user_id(username):
    userid_query = "SELECT ID FROM auth_user where username=%s"
    with conn.cursor() as cursor:
        cursor.execute(userid_query, (username,))
        user_id = cursor.fetchone()
    return user_id


def get_all_users():
    query = "SELECT username FROM auth_user"
    with conn.cursor() as cursor:
        cursor.execute(query)
        all_users = cursor.fetchall()

    all_users = [item.lower() for sublist in all_users for item in sublist]

    query = """select username from auth_user
                where id in (
                select user_id from auth_user_groups
                where group_id = 1
                group by user_id)"""
    with conn.cursor() as cursor:
        cursor.execute(query)
        all_mws = cursor.fetchall()

    all_mws = [item.lower() for sublist in all_mws for item in sublist]
    return all_users, all_mws

class Command(BaseCommand):
    help = "Run a discord bot"

    def handle(self, *args, **options):
        print('starting bot')

        @bot.slash_command()
        async def create_scanner_signup(ctx):
            await ctx.send("", view=RegionSelectView())

        @bot.slash_command()
        async def stop_bot_v2(ctx):
            await ctx.respond("nwmp_bot_v2 stopped", ephemeral=True)
            exit()

        @bot.slash_command()
        async def find_inactive_scanners(ctx):
            all_users, all_mws = get_all_users()
            guild = bot.get_guild(936405548792938546) # nwmp channel
            # guild = bot.get_guild(826816215900749824) # CREAM channel
            roleid = 950235365082533918  # market watcher role on main channel
            # roleid = 1050251920310284449  # market watcher role on CREAM

            role = guild.get_role(roleid)

            manual_clean = []
            remove_role = []

            for member in role.members:
                mem_name = str(member)
                pos = mem_name.rfind('#')
                mem_name = mem_name[:pos]
                mem_name = mem_name.lower()
                # print(mem_name)
                if mem_name in all_users:
                    # print(f'found {member}')
                    if mem_name not in all_mws:
                        # print(f'Found user first try. Remove MW role {member}')
                        remove_role.append(member)
                else:
                    # pos2 = member.rfind(' ')
                    # clean_mem = member[:pos2]
                    # print(f'no match for {member}. {pos2}')
                    manual_clean.append(member)
                    # if clean_mem not in all_users:
                    #     print(f'Need to manually clean {member}')
                    #     manual_clean.append(member)
                    # else:
                    #     # found user after cleaning
                    #     if clean_mem not in mws:
                    #         # remove mw role
                    #         print(f'Found user after cleaning. Remove MW role {member}')
                    #         remove_role.append(member)

            # print('REMOVE THESE')
            # print(remove_role)
            for x in remove_role:
                user = guild.get_member(x.id)
                print(x.name)
                # await user.remove_roles(role)
                # print(x.name)

            # print('MANUALLY CONFIRM THESE')
            # for z in manual_clean:
            #     print(z)

            # await ctx.send("\n".join(str(member) for member in role.members)
            await ctx.respond("Role Monitor removed inactive scanners", ephemeral=True)

        @bot.event
        async def on_member_update(before, after):

            public_channel = bot.get_channel(954906680141946890) # nwmp channel
            # public_channel = bot.get_channel(826816215900749827) # CREAM channel
            private_channel = bot.get_channel(1062231562399256738) # nwmp channel
            # private_channel = bot.get_channel(1050188410108788817) # CREAM channel

            user_name = before.name

            if len(before.roles) < len(after.roles):
                # role was added
                new_role = next(role for role in after.roles if role not in before.roles)
                if new_role.name in ('Gold Subscriber', 'Premium Members'):

                    user_id = get_user_id(before.name)
                    if user_id:
                        # found the user id. They have an acount on the website
                        group_query = f"""select aug.group_id from auth_user au 
                                                            join auth_user_groups aug
                                                            on au.id = aug.user_id
                                                            where au.id = {user_id[0]}
                                                            and group_id = 91"""
                        with conn.cursor() as cursor:
                            cursor.execute(group_query)
                            group_id = cursor.fetchone()
                        if group_id:
                            # user already has the discord gold group

                            await private_channel.send(
                                f"{user_name} subscribed but they already had the discord gold role")

                        else:
                            # user does not have discord gold role. let's add it
                            add_discord_gold_query = "INSERT INTO auth_user_groups (user_id, group_id) VALUES (%s, %s)"
                            with conn.cursor() as cursor:
                                try:
                                    cursor.execute(add_discord_gold_query, (user_id, 91,))
                                    conn.commit()

                                    await public_channel.send(
                                        f'Thanks for subscribing {before.mention}! :partying_face: Your support keeps this whole thing running. Your access has been set up on the site and you should have access to all the subscriber perks now')

                                except Exception as e:

                                    await public_channel.send(
                                        f'Thanks for subscribing {before.mention}! Something went wrong when trying to setup your account. Admins have been notified.')
                                    await private_channel.send(
                                        f' Tried to add {user_name} to discord gold role but got this: {e}')

                    else:
                        # they do not have an account on the site or we couldnt find their name

                        await public_channel.send(
                            f"Thanks for subscribing {before.mention}! :partying_face: It looks like you haven't logged in on nwmarketprices.com yet to create your account there, once you have done that send a message to @CashMoney and he can give you access to all the subscriber perks.")

            elif len(before.roles) > len(after.roles):
                # role was removed
                removed_role = next(role for role in before.roles if role not in after.roles)
                if removed_role.name in ('Gold Subscriber', 'Premium Members'):
                    # remove gold group from site
                    user_id = get_user_id(before.name)
                    if user_id:
                        # user has an account on site
                        remove_discord_gold_query = "DELETE FROM auth_user_groups WHERE user_id = %s and group_id = %s"
                        with conn.cursor() as cursor:
                            try:
                                cursor.execute(remove_discord_gold_query, (user_id, 91,))
                                conn.commit()

                                await private_channel.send(
                                    f"{user_name} was removed from discord gold role")

                            except Exception as e:

                                await private_channel.send(
                                    f"ERROR: tried to remove{user_name} discord gold role, but this happened: {e}")
                    else:
                        # user doesn't have an account on site or couldn't find name
                        await private_channel.send(
                            f"Tried to remove {user_name} discord gold role, but their user name wasnt found")


                elif removed_role.name == 'Market Watcher':
                    # remove scanner roup from site
                    user_id = get_user_id(before.name)
                    if user_id:
                        # user has an account on site
                        remove_discord_gold_query = "DELETE FROM auth_user_groups WHERE user_id = %s and group_id = %s"
                        with conn.cursor() as cursor:
                            try:
                                cursor.execute(remove_discord_gold_query, (user_id, 1,))
                                conn.commit()

                                await private_channel.send(
                                    f"{user_name} was removed from scanner role")

                            except Exception as e:

                                await private_channel.send(
                                    f"ERROR: tried to remove{user_name} scanner role, but this happened: {e}")
                    else:
                        # user doesnt have an account on site or couldnt find name
                        await private_channel.send(
                            f"Tried to remove {user_name} scannner role, but their user name wasnt found")

        @bot.event
        async def on_ready():
            print(f"{bot.user} is ready and online!")

        bot.run(os.getenv('DISCORDBOT_ROLEMONITOR_TOKEN'))


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
        role = interaction.guild.get_role(950235365082533918) # market watcher role on main channel
        # role = interaction.guild.get_role(1050251920310284449)  # market watcher role on CREAM# market watcher role
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
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role)
                await interaction.response.edit_message(view=RegionSelectView())
                await interaction.followup.send(respond_message, ephemeral=True)

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
                        respond_message = f'Thanks {username} You have been added as a scanner to {server_name}. Please follow the link above to download the scanner.'

                    except Exception as e:
                        print(e)
                        respond_message = f'Something went wrong when adding you. Please message CashMoney'

                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role)

                await interaction.response.send_message(respond_message, ephemeral=True)
                await interaction.user.add_roles()

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