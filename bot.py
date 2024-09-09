import os
from dotenv import load_dotenv
import random
import tkinter as tk
import discord
from discord.ext import commands
import requests
from user import User
from rps import start_rps_game
from emoji import art_react

load_dotenv()
token = os.environ['DISCORD_BOT_TOKEN']

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  

bot = commands.Bot(command_prefix='!', intents=intents)



@bot.event
async def on_ready():
    await bot.tree.sync(guild=None)
    print(f'Logged in as {bot.user.name}')

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

# Daily streak command
serverUsersID = {}
@bot.hybrid_command(name= "daily", description="Claim your daily streak")
async def daily(ctx):
    """Claim your daily streak"""
    userID = ctx.author.id
    if userID not in serverUsersID:
        # New user
        user = User((userID, ctx.author.name))
        serverUsersID[userID] = user
    else: user = serverUsersID[userID]
    message = user.claimDaily()
    await ctx.send(message)

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

# Auto react to art related messages
@bot.event
async def on_message(message: discord.Message):
    await art_react(message)
    
    # Allow other commands to process if applicable
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

# def create_wheel_image(titles, percentiles):
#     """Create the picker wheel image."""
#     # Create a blank image
#     size = (400, 400)
#     wheel = tk.Image.new("RGBA", size, (255, 255, 255, 0))
#     draw = tk.ImageDraw.Draw(wheel)

#     # Calculate the angles
#     angles = [p * 3.6 for p in percentiles]
#     start_angle = 0

#     # Colors for each slice
#     colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]

#     for i, angle in enumerate(angles):
#         end_angle = start_angle + angle
#         draw.pieslice([(0, 0), size], start_angle, end_angle, fill=colors[i % len(colors)])
#         start_angle = end_angle

#     # Save the image to a bytes buffer
#     buffer = io.BytesIO()
#     wheel.save(buffer, format="PNG")
#     buffer.seek(0)
#     return buffer

bot.run(token)