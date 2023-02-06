from django.core.management.base import BaseCommand
import discord
import os
from dotenv import load_dotenv
import psycopg2
Intents = discord.Intents.all()
Intents.members = True
Intents.presences = True
Intents.messages = True

load_dotenv()
bot = discord.Bot(intents=Intents)
conn = psycopg2.connect(f"dbname={os.getenv('DB_NAME')} user={os.getenv('RDS_USERNAME')} password={os.getenv('RDS_PASSWORD')} host={os.getenv('RDS_HOSTNAME')}")
curr = conn.cursor()


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
        async def stop_rolemonitor_bot(ctx):
            await ctx.respond("Role Monitor bot stopped", ephemeral=True)
            exit()

        @bot.slash_command()
        async def find_inactive_scanners(ctx):
            all_users, all_mws = get_all_users()
            guild = bot.get_guild(936405548792938546)
            roleid = 950235365082533918
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

            public_channel = bot.get_channel(1050192207673573386)
            private_channel = bot.get_channel(1050192207673573386)
            user_name = before.name

            if len(before.roles) < len(after.roles):
                # role was added
                new_role = next(role for role in after.roles if role not in before.roles)
                if new_role.name in ('Gold Subscriber', 'Premium Members'):

                    user_id = get_user_id(before.name)
                    if user_id:
                        #found the user id. They have an acount on the website
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

                                    await public_channel.send(f'Thanks for subscribing {before.mention}! :partying_face: Your support keeps this whole thing running. Your access has been set up on the site and you should have access to all the subscriber perks now')

                                except Exception as e:

                                    await public_channel.send(f'Thanks for subscribing {before.mention}! Something went wrong when trying to setup your account. Admins have been notified.')
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
                        # user doesnt have an account on site or couldnt find name
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



# to run on ssh into eb aws
# $ eb ssh
# screen -S my_bot --start new session
# screen -r my_bot  --reconnect to old
# $ sudo su -
# $ export $(cat /opt/elasticbeanstalk/deployment/env | xargs)
# $ source /var/app/venv/*/bin/activate
# $ python3 /var/app/current/manage.py nwmp_rolemonitor_bot