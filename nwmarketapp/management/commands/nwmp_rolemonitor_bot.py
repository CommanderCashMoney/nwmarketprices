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
# conn = psycopg2.connect(f"dbname={os.getenv('DB_NAME')} user={os.getenv('RDS_USERNAME')} password={os.getenv('RDS_PASSWORD')} host={os.getenv('RDS_HOSTNAME')}")
# curr = conn.cursor()
# client = discord.Client()




class Command(BaseCommand):
    help = "Run a discord bot"

    def handle(self, *args, **options):
        print('starting bot')

        # @bot.slash_command()
        # async def scanner_signup(ctx):
        #     await ctx.send("", view=RegionSelectView())
        #
        @bot.slash_command()
        async def stop_scanner_bot(ctx):
            await ctx.respond("Add Scanner bot stopped", ephemeral=True)
            exit()

        @bot.event
        async def on_member_update(before, after):
            print('event fired')
            channel = bot.get_channel(1050192207673573386)
            user_name = before.name


            # for role in before.roles:
            #     await channel.send(f'{user_name}Before Roles: ')
            for role in after.roles:

                if role.name != '@everyone':
                    print(role.name)
                # await channel.send(f'{user_name}After Roles: {role}')

            # if len(before.roles) < len(after.roles):
            #     new_role = next(role for role in after.roles if role not in before.roles)
            #     if new_role.name in ('Gold Supporter', 'Platinum Supporter'):
            #         fmt = "{0.mention} your role request has been accepted! :confetti_ball: You've been granted the role '{1}'"
            #         await bot.message_command(bot.get_channel('1050192207673573386'), fmt.format(after, new_role.name))
            #     elif new_role.name in ('Market Watcher'):
            #         fmt = "{0.mention} you are now part of the CyberLife staff, we're so excited to have you here! :confetti_ball:"
            #         await bot.send_message(bot.get_channel('1050192207673573386'), fmt.format(after))


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
# $ python3 /var/app/current/manage.py start_scanner_bot