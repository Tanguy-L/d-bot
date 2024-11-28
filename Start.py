import discord
from discord.ext import commands
import Core.MemberPool
import Core.Database
import Core.CommandParser
import codecs
import random
from dotenv import load_dotenv
import os
from collections import defaultdict

"""  
===================================================

GLOBAL VAR

==================================
"""
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
load_dotenv()
connection_command = os.getenv('CONNECTION')
url_connection_button = os.getenv('URL_BUTTON_CONNECTION')
bot_token = os.getenv('BOT_TOKEN')


"""  
===================================================

BOT CLASS

==================================
"""
class VCMBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix,  intents=intents)
        self.members = Core.MemberPool.VCMMemberPool()
        self.db = Core.Database.VCMDatabase()
        self.parser = Core.CommandParser.VCMCommandParser()

    async def scan_for_connected_members(self, guild):
        guild_channels = list(await guild.fetch_channels())
        for ch in guild_channels:
            if ch.type == discord.ChannelType.voice:
                for member in ch.members:
                    print(self.db.is_discord_member_known(discord_id=member.id))
                    if self.db.is_discord_member_known(discord_id=member.id) is False:
                        self.db.add_member(member_id=member.id, member_name=member.display_name)
                    bot.db.set_member_connection_state(member_id=member.id, state=True)
                    self.members.add(member=member)

"""  
===================================================

BOT INSTANCE

==================================
"""
bot = VCMBot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    for guild in bot.guilds:
        await bot.scan_for_connected_members(guild=guild)  
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

@bot.event
async def on_message(ctx):
    if ctx.author.id != bot.user.id:
        cmd = bot.parser.parse(ctx.content)
        if cmd is not None:
            await cmd.execute(ctx)

@bot.event
async def on_voice_state_update(member, before, after):
    old_channel = getattr(before.channel, 'id', None)
    new_channel = getattr(after.channel, 'id', None)
    
    ctx = await bot.get_context(member)

    is_member_connecting    = lambda o, n: o is None and n is not None
    is_member_disconnecting = lambda o, n: o is not None and n is None
    is_member_switching     = lambda o, n: o is not None and n is not None and o != n

    is_known = bot.db.is_discord_member_known(discord_id=member.id)

    if is_member_connecting(old_channel, new_channel):
        if is_known is False:
            bot.db.add_member(member_id=member.id, member_name=member.display_name)
        bot.db.set_member_connection_state(member_id=member.id, state=True)
        bot.members.add(member=member)

    if is_member_disconnecting(old_channel, new_channel):
        bot.db.set_member_connection_state(member_id=member.id, state=False)
        bot.members.remove(member_id=member.id)

"""  
===================================================

PARTY MANAGEMENT

==================================
"""


# SHOW CONNECT BUTTON PANEL
@bot.parser.command(name="connect")
async def display_connect_button(ctx):
    channel_id = int(os.getenv('CHANNEL_BOT'))
    print(channel_id)
    embed = discord.Embed(title="PLG: Party Lan Gaming", description="Venez vous battre !", colour=0xff8000)
    embed.add_field(name="commande de connection :", value=connection_command, inline=False)
    embed.set_thumbnail(url="https://cdn.akamai.steamstatic.com/apps/csgo/images/csgo_react/social/cs2.jpg")
    
    with codecs.open("./rsc/plg_meanings.txt", "r", "utf-8") as file:
        meanings = [line.rstrip() for line in file]
        chosen_one = random.choice(meanings)
        embed.title = "PLG: " + chosen_one

    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Rejoindre le serveur", url="http://localhost:5000"))
    await bot.get_channel(channel_id).send(view=view, embed=embed)
    
@bot.parser.command(name="admin-office")
async def display_connect_button(ctx):
    channel_id = int(os.getenv('CHANNEL_BOT'))
    print(channel_id)
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Gestion des équipes", url="http://localhost:5000"))
    await bot.get_channel(channel_id).send(view=view)

@bot.parser.command(name="list-channel")
async def list_channels(message):
    # Check if the command is used in a guild (server)
    if message.guild is None:
        await message.channel.send("This command can only be used in a server.")
        return

    # Create a list to store channel information
    channel_list = []

    # Iterate through all channels in the guild
    for channel in message.guild.channels:
        # Check the channel type
        if isinstance(channel, discord.TextChannel):
            channel_info = f"Text Channel: {channel.name} (ID: {channel.id})"
        elif isinstance(channel, discord.VoiceChannel):
            channel_info = f"Voice Channel: {channel.name} (ID: {channel.id})"
        elif isinstance(channel, discord.CategoryChannel):
            channel_info = f"Category: {channel.name} (ID: {channel.id})"
        else:
            channel_info = f"Other Channel: {channel.name} (ID: {channel.id})"
       
        channel_list.append(channel_info)

    # Join the channel information into a single string
    channels_text = "\n".join(channel_list)

    # Split the message if it's too long
    max_length = 1900  # Leave some room for the formatting
    chunks = [channels_text[i:i+max_length] for i in range(0, len(channels_text), max_length)]

    # Send the channel list
    await message.channel.send(f"Channels in this server:")
    for chunk in chunks:
        await message.channel.send(f"```\n{chunk}\n```")
    

@bot.parser.command(name="split-parties")
async def split_parties(ctx: commands.Context):
    # Get all members
    all_members = bot.members.get_all()
    
    teams = defaultdict(list)
    channel_bot = ctx.get_channel(os.getenv("CHANNEL_BOT"))

    for member in all_members:
        member_data = bot.db.get_member(member.id)
        print(member_data)
        if member_data and member_data['team_id']:
            teams[member_data['team_id']].append(member)
            
    if len(teams) != 2:
        await ctx.send(f"Error: Found {len(teams)} teams. Expected exactly 2 teams.")
        return

    team_ids = list(teams.keys())
    
    team_channels = {
        team_ids[0]: bot.get_channel(os.getenv("CHANNEL_1")),
        team_ids[1]: bot.get_channel(os.getenv("CHANNEL_2"))
    }
    
    # Move members to their team channels
    for team_id, members in teams.items():
        channel = team_channels.get(team_id)
        if not channel:
            await ctx.channel.send(f"Error: Could not find channel for team {team_id}")
            continue

        for member in members:
            try:
                await member.move_to(channel)
                print(f"Moved {member.name} to {channel.name}")
            except discord.errors.HTTPException as e:
                print(f"Failed to move {member.name}: {e}")

    await ctx.channel.send('Split parties completed!')

@bot.parser.command(name="group-parties")
async def split_parties(ctx):
    group_channel = bot.get_channel(int(os.getenv("CHANNEL_GROUP")))
    print(group_channel)
    for member in bot.members.get_all():
        await member.move_to(group_channel)

    await bot.get_channel(ctx.channel.id).send('Done!')

"""  
===================================================

WEBHOOK

==================================
"""
@bot.parser.command(name="get-webhook")
async def get_webhook(ctx: commands.Context):
    guild_webhooks = list(await ctx.guild.webhooks())

    while len(guild_webhooks) > 0:
        wh = guild_webhooks.pop()
        if wh.user.id == bot.user.id:
            embed = discord.Embed(title="Webhook trouvé 🤖", colour=0x30c543)
            embed.add_field(name="Nom", value=f"{wh.name}", inline=True)
            embed.add_field(name="Url", value=f"{wh.url}", inline=True)
            await ctx.channel.send(embed=embed)
            return
        
    embed = discord.Embed(title="Webhook introuvable 😶", colour=0xa12d2f)
    embed.add_field(name="créer le webhook", value="!create-webhook", inline=True)
    await ctx.channel.send(embed=embed)

@bot.parser.command(name="create-webhook")
async def create_webhook(ctx: commands.Context, webhook_name: str = "VCM Webhook"):
    try:
        channel = await ctx.guild.fetch_channel(ctx.channel.id)
        await channel.create_webhook(name=webhook_name)
        embed = discord.Embed(title="Webhook créé 🛠️", colour=0x30c543)
        embed.add_field(name="supprimer le webhook", value="!delete-webhook", inline=True)
        await ctx.channel.send(embed=embed)

    except:
        embed = discord.Embed(title="Oups 🩹", colour=0xa12d2f)
        embed.add_field(name="Quelque chose s'est mal passée...", value="Vérifiez que l'id du channel est valide", inline=True)
        await ctx.channel.send(embed=embed)
    

@bot.parser.command(name="delete-webhook")
async def create_webhook(ctx: commands.Context):
    channel = await ctx.guild.fetch_channel(ctx.channel.id)
    channel_webhooks = list(await channel.webhooks())

    for wh in channel_webhooks:
        if wh.user.id == bot.user.id:
            await wh.delete()
            embed = discord.Embed(title="Webhook supprimé 🚽", colour=0x30c543)
            await ctx.channel.send(embed=embed)
            return

    embed = discord.Embed(title="Aucun webhook à supprimer 😵", colour=0xa12d2f)
    await ctx.channel.send(embed=embed)

bot.run(bot_token)
