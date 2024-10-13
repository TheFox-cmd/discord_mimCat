import io
import os
from dotenv import load_dotenv
import random
import discord
from discord.ext import commands
import requests
import aiohttp
from user import User
from rps import start_rps_game
from emoji import art_react

load_dotenv("./.env")
token = os.environ['DISCORD_BOT_TOKEN']

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync(guild=None)
    print(f'Logged in as {bot.user.name}')

    # guild = discord.utils.get(bot.guilds, name="Just Us")
    # if not guild: 
    #     print("No guild found")
    #     return 
    
    # print(f'Guild: {guild.name} (id: {guild.id})')
    # for channel in guild.text_channels:
    #     print(f'Text Channel: {channel.name} (id: {channel.id})')


# Sync the server command tree
@bot.command()
@commands.has_permissions(manage_guild=True)
async def sync(ctx):
    """Sync server command tree"""
    await bot.tree.sync()
    await ctx.send('Synced!')

# Poke command
@bot.hybrid_command(name="poke", description="Poke a user")
async def poke(ctx, target_user : discord.Member):
    """Poke a user"""
    print(target_user)
    if target_user == ctx.author: await ctx.send(f'{ctx.author.display_name} poked themselves!')
    else: await ctx.send(f'{ctx.author.display_name} poked {target_user.mention}!') 

# Ping command
@bot.hybrid_command(name="ping", description="Bot's latency check")
async def ping(ctx):
    """Check bot's latency."""
    await ctx.send('Pong!')

# Nini command
@bot.hybrid_command(name="bonk", description="Easter Egg")
async def bonk(ctx):
    """Easter Egg"""
    guild = ctx.guild
    target = discord.utils.find(lambda member: member.display_name == "!NINI", guild.members)
    if target:
        bonk_message = f"{target.mention}, you've been bonked by {ctx.author.mention}! 🔨"
        await ctx.send(bonk_message)
    else: await ctx.send("Nini is not in this server!", ephemeral=True)

# Roll dice command
@bot.hybrid_command(name="roll", description="Roll a dice with a specified number of sides")
async def roll(ctx, sides: int = 6):
    """Roll a dice with a specified number of sides (default is 6)."""
    if sides < 2:
        await ctx.send(f"{ctx.author.display_name}, you need at least 2 sides to roll a dice!")
        return

    result = random.randint(1, sides)
    await ctx.send(f"{ctx.author.display_name} rolled a {result} on a {sides}-sided dice!")

# Rock paper scissors command
@bot.hybrid_command(name="rps", description="Play rock paper scissors with a user")
async def rps(ctx, target_user : discord.Member):
    """Play rock paper scissors with a user"""
    await start_rps_game(ctx, target_user)

serverUsers = {}
async def update_daily(discord_user : discord.Member):
    """Claim your daily streak"""
    if discord_user not in serverUsers:
        # Record new user in serverUsers dictionary
        user = User(discord_user)
        serverUsers[discord_user] = user
    else: user = serverUsers[discord_user]
    message = user.claimDaily()
    return message

# Event listener when a message is sent
@bot.event
async def on_message(message: discord.Message):
    await art_react(message)
    
    if message.author.bot: return

    streakID = 1281046465875148892
    practiceID = 1147617085741076481
    designID = 1158562205848055858

    streak_channel = discord.utils.get(message.guild.text_channels, id=streakID)
    practice_channel = discord.utils.get(message.guild.text_channels, id=practiceID)
    design_channel = discord.utils.get(message.guild.text_channels, id=designID)

    print(f"Message channel: {message.channel.name}")

    if message.channel != practice_channel and message.channel != design_channel: return 
    if not message.attachments: return
    for attachment in message.attachments:
        if not attachment.content_type.startswith('image/'): continue

        # Download the image
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status != 200:
                    print(f"Failed to download image: {attachment.url}")
                    return

                # Create a discord.File object from the binary data
                image_data = await resp.read()
                file = discord.File(fp=io.BytesIO(image_data), filename=attachment.filename)
                # Send the image to the streak_channel
                if streak_channel: await streak_channel.send(file=file)
    
        daily_message = await update_daily(message.author)
        await streak_channel.send(daily_message)
        print(f"{message.author} {daily_message}")
        await streak_channel.send(f"{message.author.mention} has submitted their daily artwork!")
        break 

    await bot.process_commands(message)


# authenticate with DeviantArt API
def authenticate_deviantart():
    auth_url = 'https://www.deviantart.com/oauth2/token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': os.getenv('DA_CLIENT_ID'),
        'client_secret': os.getenv('DA_CLIENT_SECRET')
    }
    response = requests.post(auth_url, data=data)
    
    print("DA status code: ", response.status_code)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception("Failed to authenticate with DeviantArt API (status code: {response.status_code})")

# Command to fetch images from DeviantArt based on a prompt
@bot.hybrid_command(name="image", description="Fetch images from DeviantArt based on a prompt")
async def image(ctx, prompt: str = None):
    """Fetch images from DeviantArt using the given prompt"""

    # API endpoint to search for images based on a prompt
    if not prompt: url = "https://www.deviantart.com/api/v1/oauth2/browse/dailydeviations?mature_content=false"
    else: 
        prompt = '_'.join(prompt.split())
        url = f'https://www.deviantart.com/api/v1/oauth2/browse/tags?tag={prompt}&mature_content=false'

    # Get access token
    try:
        access_token = authenticate_deviantart()
    except Exception as e:
        await ctx.send("Failed to authenticate with DeviantArt API")
        return

    # Headers with access token
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Fetch the randomly selected page
    results = []    
    base = random.randint(1, 1000)
    for i in range(5):
        response = requests.get(url, headers=headers, params={'offset': base + i, 'limit': 10,})
        data = response.json()
        images = data.get('results', [])
        results.extend(images)

    # If no results, notify user
    if not results:
        await ctx.send(f"No images found for prompt: {prompt}")
        return

    # Select 3 random images, or all if there are fewer than 3
    selected_images = random.sample(results, min(3, len(results)))

    # Iterate over selected images and extract URLs
    for image in selected_images:
        image_url = image['content']['src']
        await ctx.send(image_url)

bot.run(token)