#!editcmd (name) [addalias/enabled/cost/cooldown/message/delete] (str)
from core.database import db_context
from kick import Message
from globals import client, commands, commands_dir

async def reload_commands(deleted_command):
    async with db_context as db:
        command_docs = await db.commands.find().to_list(length=None)
        total_commands = len(command_docs)
        loaded_commands = 0
        print(f"!{deleted_command} Deleted Reloading Commands")
        for command_doc in command_docs:
            #print(f"{command_doc['name']} with aliases: {', '.join(command_doc['aliases'])}")
            for alias in command_doc['aliases']:
                commands[alias] = command_doc['_id']
        print(f" Successfully reloaded {total_commands} commands")

async def addAlias(args, msg: Message):
    command_name = args[1]
    alias = args[2]
    async with db_context as db:
        commands_collection = db.commands
        command = await commands_collection.find_one({"name": command_name})
        if command:
            aliases = command.get("aliases", [])
            if alias not in aliases:
                aliases.append(alias)
                await commands_collection.update_one({"name": command_name}, {"$set": {"aliases": aliases}})
            await msg.chatroom.send(f"Added alias: {alias} to command: {command_name}")
    return

async def delete(args, msg: Message):
    command_name = args[1]
    async with db_context as db:
        commands_collection = db.commands
        result = await commands_collection.delete_one({"name": command_name})
        if result.deleted_count > 0:
            await msg.chatroom.send(f"Command {command_name} deleted")
            await reload_commands(command_name)
    return

async def enabled(args, msg: Message):
    command_name = args[1]
    enabled_status = args[2].lower() == 'true'
    async with db_context as db:
        commands_collection = db.commands
        command = await commands_collection.find_one({"name": command_name})
        if command:
            await commands_collection.update_one({"name": command_name}, {"$set": {"enabled": enabled_status}})
            await msg.chatroom.send(f"Set enabled status of command: {command_name} to {enabled_status}")
    return

async def cost(args, msg: Message):
    command_name = args[1]
    cost_value = int(args[2])
    async with db_context as db:
        commands_collection = db.commands
        command = await commands_collection.find_one({"name": command_name})
        if command:
            await commands_collection.update_one({"name": command_name}, {"$set": {"cost": cost_value}})
            await msg.chatroom.send(f"Set cost of command: {command_name} to {cost_value}")
    return

async def cooldown(args, msg: Message):
    command_name = args[1]
    cooldown_value = int(args[2])
    async with db_context as db:
        commands_collection = db.commands
        command = await commands_collection.find_one({"name": command_name})
        if command:
            await commands_collection.update_one({"name": command_name}, {"$set": {"cooldown": cooldown_value}})
            await msg.chatroom.send(f"Set cooldown of command: {command_name} to {cooldown_value}")
    return

async def message(args, msg: Message):
    command_name = args[1]
    message_value = ' '.join(args[2:])
    async with db_context as db:
        commands_collection = db.commands
        command = await commands_collection.find_one({"name": command_name})
        if command:
            await commands_collection.update_one({"name": command_name}, {"$set": {"message": message_value}})
            await msg.chatroom.send(f"Set message of command: {command_name} to {message_value}")
    return

async def isfile(args, msg: Message):
    command_name = args[1]
    file_value = ' '.join(args[2:])
    if file_value.lower() not in ["true", "false"]:
        await msg.chatroom.send(" isfile must be true or false")
        return
    file_value = bool(file_value)
    async with db_context as db:
        commands_collection = db.commands
        command = await commands_collection.find_one({"name": command_name})
        if command:
            await commands_collection.update_one({"name": command_name}, {"$set": {"file": file_value}})
            await msg.chatroom.send(f"Set file to: {command_name} to {file_value}")
    return

async def cooldowntype(args, msg: Message):
    command_name = args[1]
    cooldowntype = ' '.join(args[2:])
    if cooldowntype.lower() not in ["global", "user"]:
        await msg.chatroom.send("cooldowntype must be 'global' or 'user'")
        return

    async with db_context as db:
        commands_collection = db.commands
        command = await commands_collection.find_one({"name": command_name})
        if command:
            await commands_collection.update_one({"name": command_name}, {"$set": {"cooldowntype": cooldowntype}})
            await msg.chatroom.send(f"Set cooldown for {command_name} to {cooldowntype}")
    return

async def permission(args, msg: Message):
    command_name = args[1]
    permission = ' '.join(args[2:])

    if permission not in ["0","1","2","3","4","5"]:
        await msg.chatroom.send("Permission must be 0 to 5")
        return
    if permission == 0:
        permission == -1
    else: 
        permission = int(permission)

    async with db_context as db:
        commands_collection = db.commands
        command = await commands_collection.find_one({"name": command_name})
        if command:
            await commands_collection.update_one({"name": command_name}, {"$set": {"permission": permission}})
            await msg.chatroom.send(f"Set permission for {command_name} to {permission}")
    return

subcommands = {
  "addalias": addAlias,
  "enabled": enabled,
  "cost": cost,
  "cooldown": cooldown,
  "message": message,
  "permission": permission,
  "file": isfile,
  "cooldowntype": cooldowntype,
  "delete" : delete
}

async def editcmd(msg: Message):

    args = msg.content.replace("!editcmd ","").split(" ")
    #print(f"Arguments: {args}")
    if args[0] is None:
        return

    sub_command = subcommands.get(args[0])

    if sub_command:
        command_name = args[1]
        async with db_context as db:
            commands_collection = db.commands
            command = await commands_collection.find_one({"name": command_name})
            if command:
                await sub_command(args, msg)
            else:
                await msg.chatroom.send(f"Command {command_name} does not exist")
    return
