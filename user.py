from datetime import datetime, timedelta
import pytz

class User: 
  def __init__(self, userInfo):
    self.id = userInfo[0]
    self.name = userInfo[1]

    # User Art Daily Streaks
    self.currentStreak = 0
    self.longestStreak = 0
    self.claimed = False
    self.prevClaim = None
    self.nextClaim = None

  def claimDaily(self):
    now = datetime.now(pytz.timezone('America/Los_Angeles'))

    if self.nextClaim is None or now > self.nextClaim:
      # User has not claimed their daily streak today
      self.claimed = False

    if self.claimed:
      # User has already claimed their daily streak today 
      return f"You have already claimed your daily streak today.\nCurrent streak: {self.currentStreak}\nLongest streak: {self.longestStreak}" 
    
    if self.prevClaim is None: 
      # First time user is claiming daily streak
      self.currentStreak = 1
      self.longestStreak = 1
      
      target = now.replace(hour=0, minute=0, second=0, microsecond=0)
      self.prevClaim = target + timedelta(days=1)
      self.nextClaim = target + timedelta(days=2)
      self.claimed = True

      return f"Daily streak claimed!\nCurrent streak: {self.currentStreak}\nLongest streak: {self.longestStreak}"

    if self.prevClaim < now and now < self.nextClaim:
      # User has claimed their daily streak within the 24 hour window
      self.currentStreak += 1
      if self.currentStreak > self.longestStreak:
        self.longestStreak = self.currentStreak
    else: 
      # User has missed a day
      self.currentStreak = 1

    target = now.replace(hour=0, minute=0, second=0, microsecond=0)
    self.prevClaim = target + timedelta(days=1)
    self.nextClaim = target + timedelta(days=2)
    self.claimed = True

    return f"Daily streak claimed!\nCurrent streak: {self.currentStreak}\nLongest streak: {self.longestStreak}"

