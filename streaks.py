import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime, timedelta
import pytz
import sqlite3
import aiohttp
import io
import os
from dotenv import load_dotenv

# TODO: Implement daily streaks for users
# ? 4. Redeem Days
# * 5. Discord UI for claiming daily streak 
# ? 6. Based on user's local time
# / 7. Leaderboard 

load_dotenv("./.env")

class StreakCog(commands.cog): 
  def __init__(self, bot):
    self.bot = bot
    self.conn = sqlite3.connect('user.db')
    self.c = self.conn.cursor()
    self.LA_TZ = pytz.timezone('America/Los_Angeles')
    self.initStreakDB()

  # * Initialize Streak Database
  def initStreakDB(self): 
    self.c.execute('''CREATE TABLE IF NOT EXISTS streaks (id INTEGER PRIMARY KEY, currentStreak INTEGER, longestStreak INTEGER, redeemDays INTEGER , startClaim TEXT, endClaim TEXT)''')
    self.conn.commit()

  # * Claim Daily Streak
  def claimDaily(self, ctx):
    # Get ctx author's Info 
    userID = ctx.author.id
    userTime = datetime.now(self.LA_TZ)

    # Check if user exists in the database
    acquireUser = self.c.execute(f'SELECT * FROM streaks WHERE id = {userID}')
    target = userTime.replace(hour=0, minute=0, second=0, microsecond=0)
    startClaim = target + timedelta(days=1)
    endClaim = target + timedelta(days=2)
    userCurrentStreak, userLongestStreak = acquireUser[1], acquireUser[2]

    # New user claiming daily streak
    if acquireUser is None: 
      self.c.execute(f'INSERT INTO streaks (id, currentStreak, longestStreak, redeemDays, startClaim, endClaim) VALUES ({userID}, 1, 1, 0, "{startClaim}", "{endClaim}")')
      self.conn.commit()
      return f"Daily streak claimed! {ctx.author.mention}\nCurrent streak: 1\nLongest streak: 1"

    # User has already claimed their daily streak today
    if userTime < startClaim: 
      return f"{ctx.author.mention}, You have already claimed your daily streak today. Please wait until tomorrow to claim again." 

    # User has claimed their daily streak within the 24 hour window
    if startClaim < userTime and userTime < endClaim:
      currentStreak = userCurrentStreak + 1
      longestStreak = userLongestStreak

      if currentStreak > longestStreak: longestStreak = currentStreak

      self.c.execute(f'UPDATE streaks SET currentStreak = {currentStreak}, longestStreak = {longestStreak}, startClaim = "{startClaim}", endClaim = "{endClaim}" WHERE id = {userID}')
      self.conn.commit()
      return f"Daily streak claimed! {ctx.author.mention}\nCurrent streak: {currentStreak}\nLongest streak: {longestStreak}"
    
    # User has missed a day
    currentStreak = 1
    self.c.execute(f'UPDATE streaks SET currentStreak = {currentStreak}, startClaim = "{startClaim}", endClaim = "{endClaim}" WHERE id = {userID}')
    self.conn.commit()
    return f"Daily streak claimed! {ctx.author.mention}\nCurrent streak: {currentStreak}\nLongest streak: {userLongestStreak}"
  
  # * Check redeem day qualifications
  def checkRedeem(self, ctx):
    userID = ctx.author.id
    userTime = datetime.now(self.LA_TZ)
    acquireUser = self.c.execute(f'SELECT * FROM streaks WHERE id = {userID}')
    userCurrentStreak, userRedeemDays = acquireUser[1], acquireUser[3]

    if userCurrentStreak >= 7: 
      self.c.execute(f'UPDATE streaks SET currentStreak = 0, redeemDays = {userRedeemDays + 1} WHERE id = {userID}')
  
  # * Reroute to Streak Channel for Artwork Uploads
  @commands.Cog.listener()
  async def rerouteStreakChannel(self, message):
    # Ignore messages from bots
    if message.author.bot: return

    # Define the relevant channel IDs

    # Get the actual channel objects
    streak_channel = discord.utils.get(message.guild.text_channels, id=os.getenv('JU_STREAK_ID'))

    # Check if the message is in either the practice or design channel
    if message.channel.id not in {os.getenv('JU_PRACTICE_ID'), os.getenv('JU_DESIGN_ID')}: return  

    # Proceed if the message contains attachments
    if not message.attachments: return  

    for attachment in message.attachments:
      # Only process image files
      if not attachment.content_type.startswith('image/'):
        continue

      # Download and process the image
      async with aiohttp.ClientSession() as session:
        async with session.get(attachment.url) as resp:
          if resp.status != 200:
            print(f"Failed to download image: {attachment.url}")
            return

        # Create a discord.File object from the binary data
        image_data = await resp.read()
        file = discord.File(fp=io.BytesIO(image_data), filename=attachment.filename)

        # Send the image to the streak_channel
        if streak_channel:
            await streak_channel.send(file=file)

      # Update the user's streak and send a daily message
      dailyMessage = self.claimDaily(message.author)
      await streak_channel.send(dailyMessage)
      print(f"{message.author} {dailyMessage}")
      await streak_channel.send(f"{message.author.mention} has submitted their daily artwork!")

    # ? Continue processing other bot commands
    # await bot.process_commands(message)



  ############################################################################

  # class StreakView(View): 
  #   def __init__(self):
  #     super().__init__()
  #     self.add_item(Button(style=ButtonStyle.primary, label="Claim Streak", custom_id="claim_streak"))

  #   @discord.ui.button(label="Claim Streak", style=ButtonStyle.primary)
  #   async def claim_streak(self, button, interaction):
  #     await interaction.response.send_message("Claimed!", ephemeral=True)

  