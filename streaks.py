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
# * 5. Discord UI for claiming daily streak 
# / 7. Leaderboard 

load_dotenv("./.env")

class StreakCog(commands.Cog): 
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

  # * Sync Past User Data
  @commands.command()
  async def syncPastData(self, ctx):
    now = datetime.now(self.LA_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    startClaim = now
    endClaim = now + timedelta(days=2)

    print(startClaim, endClaim)

    with open ("streak_data.txt", "r", encoding="utf-8") as file:
      for line in file:
        user_id, _, _, user_current_streak, user_longest_streak = line.strip().split(",")
        self.c.execute(f'INSERT INTO streaks (id, currentStreak, longestStreak, redeemDays, startClaim, endClaim) VALUES ({user_id}, {user_current_streak}, {user_longest_streak}, {0}, "{startClaim}", "{endClaim}")')
        self.conn.commit()
    await ctx.send("Synced past data!")

  @commands.command()
  async def fetchStreakData(self, ctx): 
    self.c.execute('SELECT * FROM streaks')
    print(self.c.fetchall())
    await ctx.send("Data fetched!")

  @commands.command()
  async def clearStreakData(self, ctx):
    self.c.execute('DELETE FROM streaks')
    self.conn.commit()
    await ctx.send("Data cleared!")

  @commands.command()
  async def addStreak(self, ctx, member : discord.Member):
    self.c.execute(f'SELECT * FROM streaks WHERE id = {member.id}')
    user = self.c.fetchone()
    if user is None: return

    current, longest = user[1] + 1, user[1] + 1 if user[1] + 1 > user[2] else user[2]
    self.c.execute(f'UPDATE streaks SET currentStreak = {current}, longestStreak = {longest} WHERE id = {member.id}')
    self.conn.commit()
    await member.send("Streak added!")

  # * Claim Daily Streak
  async def claimDaily(self, member : discord.Member):
    # Get ctx author's Info 
    userID = member.id
    print("User ID: ", userID)
    userTime = datetime.now(self.LA_TZ)

    # Check if user exists in the database
    self.c.execute(f'SELECT * FROM streaks WHERE id = {userID}')
    acquireUser = self.c.fetchone()


    # New user claiming daily streak
    if acquireUser is None: 
      userStartClaim = userTime.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
      userEndClaim = userStartClaim + timedelta(days=1)
      self.c.execute(f'INSERT INTO streaks (id, currentStreak, longestStreak, redeemDays, startClaim, endClaim) VALUES ({userID}, 1, 1, 0, "{userStartClaim}", "{userEndClaim}")')
      self.conn.commit()
      return f"Daily streak claimed! {member.mention}\nCurrent streak: 1\nLongest streak: 1"
    
    userCurrentStreak, userLongestStreak, userRedeemDays, userStartClaim, userEndClaim = acquireUser[1], acquireUser[2], acquireUser[3], datetime.fromisoformat(acquireUser[4]), datetime.fromisoformat(acquireUser[5])

    # User has already claimed their daily streak today
    if userTime < userStartClaim: 
      print(userStartClaim, userTime, userEndClaim, userCurrentStreak, userLongestStreak, userRedeemDays)
      print("--------------------")
      return f"{member.mention}, You have already claimed your daily streak today. Please wait until tomorrow to claim again." 

    # Determine if user has claimed their daily streak within the 24 hour window
    if userTime < userEndClaim: userCurrentStreak += 1
    else: userCurrentStreak = 1

    # Check if user has redeemed their daily streak for 7 days
    userRedeemDays = userRedeemDays + 1 if userCurrentStreak >= 7 else userRedeemDays

    # Update longest streak if current streak is greater
    if userCurrentStreak > userLongestStreak: userLongestStreak = userCurrentStreak

    # Set the start and end claim time for the user
    userStartClaim = userTime.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    userEndClaim = userStartClaim + timedelta(days=1)
    
    # Sync user's streak data to the database
    self.c.execute(f'UPDATE streaks SET currentStreak = {userCurrentStreak}, longestStreak = {userLongestStreak}, redeemDays = "{userRedeemDays}", startClaim = "{userStartClaim}", endClaim = "{userEndClaim}" WHERE id = {userID}')
    self.conn.commit()
    return f"Daily streak claimed! {member.mention}\nCurrent streak: {userCurrentStreak}\nLongest streak: {userLongestStreak}"
  
  # * Reroute to Streak Channel for Artwork Uploads
  async def rerouteStreakChannel(self, message):

    print(message)

    # Ignore messages from bots
    if message.author.bot: return

    # Get the actual channel objects
    streak_channel = discord.utils.get(message.guild.text_channels, id=int(os.getenv('JU_STREAK_ID')))

    print(streak_channel)

    # Check if the message is in either the practice or design channel
    if message.channel.id not in {int(os.getenv('JU_PRACTICE_ID')), int(os.getenv('JU_DESIGN_ID'))}: return  

    print(message.channel.id)
    
    print(f"Rerouting message from {message.channel} to {streak_channel}")

    # Proceed if the message contains attachments
    if not message.attachments: return  

    print("Message contains attachments")

    for attachment in message.attachments:
      # Only process image files
      if not attachment.content_type.startswith('image/'):
        continue

      try:
        # Download and process the image
        async with aiohttp.ClientSession() as session:
          async with session.get(attachment.url) as resp:
            if resp.status != 200:
              print(f"Failed to download image: {attachment.url} (status: {resp.status})")
              return

            # Create a discord.File object from the binary data
            image_data = await resp.read()
            file = discord.File(fp=io.BytesIO(image_data), filename=attachment.filename)

            # Send the image to the streak_channel
            if streak_channel:
              print(f"Sending image to {streak_channel}")
              await streak_channel.send(file=file)

      except aiohttp.ClientError as e:
        print(f"An error occurred during image download: {e}")
        await streak_channel.send(f"Failed to download {attachment.filename}. Please try again later.")
        return
      finally:
        # Update the user's streak and send a daily message
        print("Message Author ID: ", message.author.id)  
        dailyMessage = await self.claimDaily(message.author)
        print(dailyMessage)
        await streak_channel.send(dailyMessage)
        break
        print(f"{message.author} {dailyMessage}")
        await streak_channel.send(f"{message.author.mention} has submitted their daily artwork!")

  # * Get Calendar View for Streaks
  # @commands.command()
  # def getStreakCalendar(self, ctx):
  #   pass

  ############################################################################

  # class StreakView(View): 
  #   def __init__(self):
  #     super().__init__()
  #     self.add_item(Button(style=ButtonStyle.primary, label="Claim Streak", custom_id="claim_streak"))

  #   @discord.ui.button(label="Claim Streak", style=ButtonStyle.primary)
  #   async def claim_streak(self, button, interaction):
  #     await interaction.response.send_message("Claimed!", ephemeral=True)

  