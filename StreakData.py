StreakData = {}
with open ("active_users.txt", "r", encoding="utf-8") as file:
  for line in file:
    user_id, user_name, user_display_name = line.strip().split(",")
    StreakData[user_id] = {"Name": user_name, "Display Name": user_display_name, "Current": 0, "Longest": 0}


with open ("streak_channel_messages.txt", "r", encoding="utf-8") as file:
  flag = 0 
  userID = ""
  for line in file:
    line = line.replace("\n", "")
    if flag == 1: 
      if line[:7] == "Current": 
        currentStreak = line[16:]
        StreakData[userID]["Current"] = int(currentStreak)
      elif line[:7] == "Longest": 
        longestStreak = line[16:]
        StreakData[userID]["Longest"] = int(longestStreak)
        flag = 0
    elif line[-1] == '>': 
      if '@' in line:
        print(line)
        i = line.index("@")
        userID = line[i+1:-1] 
        flag = 1

deleteIDs = []
for id, info in StreakData.items():
  if info["Current"] == 0: 
    deleteIDs.append(id)

for id in deleteIDs:
  del StreakData[id]

with open ("streak_data.txt", "w", encoding="utf-8") as file:
  for id, info in StreakData.items():
    file.write(f"{id},{info['Name']},{info['Display Name']},{info['Current']},{info['Longest']}\n")

