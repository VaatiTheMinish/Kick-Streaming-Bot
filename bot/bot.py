import asyncio
import configparser
import importlib
import json
import random
import re
import emoji
import unicodedata
import urllib.parse
import importlib.util
import os
import logging

from datetime import datetime
from kick import Credentials, Message, User, Livestream, Chatroom
from globals import client, commands, commands_dir

from core.database import db_context
from core.commands import processCommands
from core.points import addpoints, addusertodb
from core.tts import texttospeach
from core.pointsmultiplier import pointsmultiplier

#-----

#Uncomment the line below for debugging
#logging.getLogger().setLevel(logging.INFO)

current_datetime = datetime.now()


config = configparser.ConfigParser()
config.read("config/config.ini")
channel = str(config.get("botcredentials", "channel"))
username = str(config.get("botcredentials", "username"))
password = str(config.get("botcredentials", "password"))
version = str(config.get("version", "version"))

data = {
    'username': username,
    'password': password
}


formatted_datetime = current_datetime.strftime("%m/%d/%Y - %H:%M:%S")


@client.event
async def on_message(msg: Message):
    if msg.author.id == client.user.id:  # Check if the message is sent by the bot itself
        return
    
    #check if the user exists in the database, if not add them
    await addusertodb(str(msg.author), int(msg.author.id))

    #a fix for standered and kicks emojis
    pattern = r'\[emote:\d+:(.*?)\]' 
    message = re.sub(pattern, r'\1', msg.content)
    message = emoji.demojize(message)

    print(f"{formatted_datetime} | {msg.author}: {message}")

    command = message[1:].split(" ", 1)[0].lower()
    
    if commands.get(command, None):
        await processCommands(msg, command)
    else:

        async with db_context as db:
            tts = await db.general.find_one({"name": "tts"}, {"_id": 0})
            points = await db.general.find_one({"name": "points"}, {"_id": 0})
        if tts['type'] == 'chat':
            await texttospeach(msg)

        if points['enabled']:
            points = await pointsmultiplier(msg, random.randint(points['min'],points['max']))
            await addpoints(str(msg.author), msg.author.id, points, True)
        return

@client.event
async def on_ready():

    print(f"I have successfully logged in")
    print ("loading events")

    user = await client.fetch_user(channel)
    await user.chatroom.connect()

    print("loading commands...")
    async with db_context as db:
        command_docs = await db.commands.find().to_list(length=None)
        total_commands = len(command_docs)
        loaded_commands = 0

        for command_doc in command_docs:
            print(f"{command_doc['name']} with aliases: {', '.join(command_doc['aliases'])}")
            for alias in command_doc['aliases']:
                commands[alias] = command_doc['_id']
            loaded_commands += 1

    print(f'''
== Done Loading {loaded_commands} commannds. == 
   Version: {version} | Made by Ryohei
   There May and will be bugs 
   Logged in as: {client.user.slug} in Channel: {channel}
{formatted_datetime} | Bot Now Online and waiting!''')



# You have to authenticate yourself in order to send mesages
async def run_bot():
    while True:
        try:
            credentials = Credentials(**data)
            await client.start(credentials)
            
        except Exception as e:
            print(f'''{formatted_datetime} Bot disconnected due to error: {e}. 
                  Trying to Reconnect...
                  
                  ''')
            await asyncio.sleep(10)  # wait for 10 seconds before trying to reconnect

asyncio.run(run_bot())
