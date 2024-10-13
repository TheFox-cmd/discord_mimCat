from datetime import datetime, timedelta
import pytz


class User: 
  def __init__(self, user):
    self.user = user

    # User Art Daily Streaks
    self.currentStreak = 0
    self.longestStreak = 0
    self.claimed = False
    self.prevClaim = None
    self.nextClaim = None

  def claimDaily(self):
    now = datetime.now(pytz.timezone('America/Los_Angeles'))

    print(f'User: {self.user.display_name}')
    print(f"Claimed time: {now}")

    # User never claimed their daily streak or it has been more than 24 hours since their last claim
    if self.nextClaim is None or now > self.prevClaim:
      self.claimed = False

    # User has already claimed their daily streak today with flag set to True
    if self.claimed:
      return f"{self.user.mention}, You have already claimed your daily streak today. Please wait until tomorrow to claim again." 
    
    # First time user is claiming daily streak
    if self.prevClaim is None: 
      self.currentStreak = 1
      self.longestStreak = 1
      
      target = now.replace(hour=0, minute=0, second=0, microsecond=0)
      self.prevClaim = target + timedelta(days=1)
      self.nextClaim = target + timedelta(days=2)

      print(f"Next Available Lower Range: {self.prevClaim}")
      print(f"Next Available Upper Range: {self.nextClaim}")

      self.claimed = True

      return f"Daily streak claimed! {self.user.mention}\nCurrent streak: {self.currentStreak}\nLongest streak: {self.longestStreak}"

    if self.prevClaim < now and now < self.nextClaim:

      # User has claimed their daily streak within the 24 hour window
      self.currentStreak += 1
      if self.currentStreak > self.longestStreak: self.longestStreak = self.currentStreak
    
    else: 
    
      # User has missed a day
      self.currentStreak = 1

    target = now.replace(hour=0, minute=0, second=0, microsecond=0)
    self.prevClaim = target + timedelta(days=1)
    self.nextClaim = target + timedelta(days=2)

    print(f"Next Available Lower Range: {self.prevClaim}")
    print(f"Next Available Upper Range: {self.nextClaim}")

    self.claimed = True

    return f"Daily streak claimed! {self.user.mention}\nCurrent streak: {self.currentStreak}\nLongest streak: {self.longestStreak}"

