from dotenv import load_dotenv
import requests
import matplotlib.pyplot as plt
import time
import os
import json

load_dotenv()
API_KEY = os.getenv('API_KEY')
HEADERS = {'X-Riot-Token': API_KEY}
ME = 'IYA-33ZGOldH7GZ9TEmfSuNABYRgmT2jx7cEVt7QbbHPvFzpmoU9Pe05M4ZdPJUONms4dMj5JSyPKQ'

timeNow = int(time.time()) # Maybe use at some point? pulls current time and returns epoch timestamp

data = []

if os.path.exists("local_api.json"):
    with open("local_api.json", "r") as f:
        data = json.load(f)
else:
    # Time set for start of set 17
    response = requests.get(f'https://americas.api.riotgames.com/tft/match/v1/matches/by-puuid/{ME}/ids?count=200&startTime=1776252000', headers=HEADERS)
    match_ids = response.json() # Match ids
    counter = 0
    for match_id in match_ids:
        response = requests.get(f'https://americas.api.riotgames.com/tft/match/v1/matches/{match_id}', headers=HEADERS)
        counter += 1
        print(str(counter) + " / " + str(len(match_ids)))
        time.sleep(1.2)
        match_data = response.json() # Match data (everything under match_id)
        data.append(match_data)
    match_data = response.json()
    print(response.status_code, match_data)
    with open("local_api.json", "w") as f:   
        json.dump(data, f)


match_total = (len(data)) # Total number of matches
placements = []
unit_counts = {}

# Loops through games, in each game it finds user by puuid
# Then it retrieves data from the user's board, etc.
for match_data in data:
    for i in range(len(match_data['info']['participants'])):
        if(match_data['info']['participants'][i]['puuid'] == ME):
            placement = match_data['info']['participants'][i]['placement'] # find me

            # Loops through units played by user, adds them to unit_counts dictionary
            for unit in match_data['info']['participants'][i]['units']:
                unit_name = unit['character_id'][6:]
                if(unit_name not in unit_counts):
                    unit_counts[unit_name] = 1
                else:
                    unit_counts[unit_name] += 1
            
            break

    placements.append(placement) # store my placement, go next game

sorted_units = sorted(unit_counts.items(), key=lambda item: item[1], reverse = True)
print(sorted_units)

print("Average placement: " + str(sum(placements)/len(placements)))

# Top 4 rate
top_4 = 0
for placement in placements:
    if(placement <= 4):
        top_4 += 1

print("Top 4 rate: " + str((top_4/len(placements))*100) + "%")

# Placement Trend Visual
plt.plot(placements, marker=".")
plt.gca().invert_yaxis()
plt.title("Performance Trend")
plt.ylabel("Placement")
plt.xlabel("Games (total = " + str(match_total) + ")")
plt.xticks([])
plt.show()