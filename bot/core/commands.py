import logging
import os
from kick import Message
from core.database import db_context
from core.cooldown import command_cooldown
from core.points import viewpoints, rmpoints
from core.permissions import PermissionSystem
import globals

permission_system = PermissionSystem()

async def processCommands(msg: Message, command: str):
    args = msg.content.split(" ")
    uargs = msg.content.split(" ")

    commandName = args[0][1:].casefold() # remove the '!' prefix
    
    async with db_context as db:
        command_doc = await db.commands.find_one({"aliases": commandName})

    if command_doc and command_doc['enabled']:
        #Debug Code - This is for testing and making sure that it is properly loading the commands as they are ran
        
        logging.info(f"Enabled: {command_doc['enabled']} Loaded command: {command_doc['name']} with aliases: {', '.join(command_doc['aliases'])}")
        
        #Check to make sure the command is enabled
        if command_doc and command_doc['enabled']:
            if command_doc['enabled'] == False:
                #Debug Code - For making sure disabled commands are working
                logging.info("command is disabled")

            badges = msg.author.badges
            badge_types = [badge['type'] for badge in badges]
            user_permission = await permission_system.get_permission_level(badge_types)

            #Debug Code - to make sure permissions are working correctly 
            logging.info(f"User Perm: {user_permission} | Cmd Perm: {command_doc['permission']}")
            
            if user_permission < command_doc['permission']:
                #Debug Code - to make sure it doesnt run commands when the users permission is too low
                logging.info("users perms are too low")
                return

            cmdcooldown = False
            #Check if the command is under cooldown
            #If cooldown is set to per user
            if command_doc['cooldowntype'] == 'user':
                cmdcooldown = await command_cooldown(msg.author.id, command_doc['name'], command_doc['cooldown'])
            else: #Else cooldown is set to global (applys to everyone)
                await command_cooldown(command_doc['name'], command_doc['name'], command_doc['cooldown'])
            if cmdcooldown: 
                return

            # Check if the user has enough points, if not do not continue running the command
            points = await viewpoints(msg.author.id)
            cost = command_doc['cost']

            if points >= cost:
                await rmpoints(msg.author.id, cost)
            else:
                await msg.chatroom.send(f"@{str(msg.author)} you do not have enough points!")
                return

        # If the command type is set to file, run the python file instead
        if command_doc['file']:
            if os.path.isfile(f"bot/commands/{commandName}.py"):
                command_module = __import__(f"commands.{commandName}", fromlist=[commandName])
                command_func = getattr(command_module, commandName)
                await command_func(msg)
            else:
                await msg.chatroom.send(f"File for command '{commandName}' not found.")
        else: # If the command is stored in the database this will run it
            #TODO - Move the parser into modules.parser
            message = command_doc['message']
            username = msg.author

            message = message.replace("[sender]", str(username))

            for i, arg in enumerate(args[1:], start=1):
                message = message.replace(f"(arg{i})", arg)

            #TBH this is a fix for just the so command, to properly handle usernames with _ and - being inconsistent,
            # to actually use this change please make sure the database so message is ""    
            if command_doc['name'] == 'so':
                try:
                    logging.info("Username is valid and exists")
                    user = await globals.client.fetch_user(arg)
                    print(f"User {user.username}")
                except:
                    logging.info("Username does not exist, applying a fix which may work")
                    userslug = uargs[1]
                    message = message.replace("-", "_").replace("_", "-")
            for j, uarg in enumerate(uargs[1:], start=1):
                message = message.replace(f"(uarg{j})", uarg)
          
            await msg.chatroom.send(message)
    else:
        return
        # This will send a chat message if a user does ! and the command doesnt exist
        #await msg.chatroom.send("Invalid command.")
