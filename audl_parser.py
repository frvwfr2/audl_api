import json

with open("event_types.json", "r") as event_types:
    event_ids = json.load(event_types)
# with open(r"F:\Media\smart-crop\audl_api\2022-05-07 CAR-TB stats.json", 'r') as f:
with open(r"F:\Media\smart-crop\audl_api\2022-05-07 CAR TB full_raw.json", 'r') as f:
    d = json.load(f)

# URL to get matchups from -> https://audl-stat-server.herokuapp.com/web-api/games?limit=10&years=2021,2022&page=29
# "gameID" is the key to pass to -> https://audl-stat-server.herokuapp.com/stats-pages/game/{gameID} to see the stats
# https://audl-stat-server.herokuapp.com/stats-pages/game/2021-06-04-TB-PHI
# 

players_dict = dict()
for player in d["rostersHome"]:
    players_dict[player["id"]] = f'{player["player"]["first_name"]} {player["player"]["last_name"]}'
for player in d["rostersAway"]:
    players_dict[player["id"]] = f'{player["player"]["first_name"]} {player["player"]["last_name"]}'

away_team = d["tsgAway"]
events = json.loads(away_team["events"])
# print(events)

current_quarter = 0

# Locations of the previous event, to map the distance
prev_x = 0
prev_y = 0
for e in events:
    player = ""
    time = ""
    # print(e)
    # event_type = e["t"]
    event_type = event_ids[str(e["t"])]
    # Set the spacing based on type of event. 
    # Quarter changes should have no spacing
    if event_type in ["END_OF_Q1", "END_OF_Q3", "HALFTIME", "GAME_OVER", "START_OF_GAME", "END_OF_OT1", "END_OF_OT2"]:
        spacing = ""
    # Turnovers and goals should have some spacing
    elif event_type in ["SCORED_ON", "GOAL", "BLOCK", "THROWAWAY", "THROWAWAY_CAUSED", "DROP", "STALL", "STALL_CAUSED", "CALLAHAN", "CALLAHAN_THROWN"]:
        spacing = "  "
    # Everything else has max spacing
    else:
        spacing = "    "

    if event_type == "START_OF_GAME":
        current_quarter = 1
    elif event_type == "END_OF_Q1":
        current_quarter = 2
    elif event_type == "HALFTIME":
        current_quarter = 3
    elif event_type == "END_OF_Q3":
        current_quarter = 4
    # We need to handle setting lines a little differently
    if event_type in ["SET_O_LINE", "SET_O_LINE_NO_PULL", "SET_D_LINE", "SET_D_LINE_NO_PULL", "THEIR_MIDPOINT_TIMEOUT", "OUR_MIDPOINT_TIMEOUT"]:
        spacing = "  "
        if "l" in e:
            for p in e["l"]:
                player += f'{players_dict[p]}, '
    
    # If we got a timestamp...
    if "s" in e:
        m, s = divmod(e["s"], 60)
        time = f'Q{current_quarter} {m:02d}:{s:02d} '
    # If there is a player associated with this event...
    if "r" in e:
        player = players_dict[e["r"]]
    info = f"{spacing}{time}{event_type} {player}"
    print(info)
    # print(event_ids[str(e["t"])])
