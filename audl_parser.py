import json
import requests
import argparse
import pandas
import logging


# Retrieves the game
def get_events_for_team(team_id, years_bad) -> pandas.DataFrame:
    pass

# URL to get matchups from -> https://audl-stat-server.herokuapp.com/web-api/games?limit=10&years=2021,2022&page=29
# team_id is generally the team mascot, all lowercase
# Returns a list of dicts
def get_game_list_for_team(team_id=None, years_back=2) -> list:
    logging.info(f"Getting list of games for team {team_id} for {years_back} years")
    game_list = list()

    # Make the team_id_string to put in the URL. We don't want the naked parameter there if not used. Maybe team_id should just be required
    if team_id is None:
        team_id_string = ""
    else:
        team_id_string = f"&teamID={team_id}"

    # Figure out how many years back to go. Only 1 and 2 supported. Definitely a smarter way to do this.
    if years_back == 1:
        years = "2022"
    elif years_back == 2:
        years = "2021,2022"

    # Get the first page. Do some meta-analysis to figure out how many pages we need to go
    r = requests.get(f"https://audl-stat-server.herokuapp.com/web-api/games?limit=20&years={years}{team_id_string}&page=1")
    d = r.json()
    total_game_count = d["total"]
    # Number of pages to scrape games from
    page_count = (total_game_count // 20) + 1
    print(f"Scraping {page_count} pages")
    # Add each game from page 1to the game list
    for game in d["games"]:
        # If there's no roster, the game is in the far future. This should probably just compare to the startTimestamp tho - "startTimestamp":"2022-07-23T18:00:00-04:00"
        if game["hasRosterReport"]:
            game_list.append(game)

    for page in range(2, page_count):
        r = requests.get(f"https://audl-stat-server.herokuapp.com/web-api/games?limit=20&years={years}{team_id_string}&page=1")
        d = r.json()
        for game in d["games"]:        
            # If there's no roster, the game is in the far future. This should probably just compare to the startTimestamp tho - "startTimestamp":"2022-07-23T18:00:00-04:00"
            if game["hasRosterReport"]:
                game_list.append(game)
    return game_list

# Returns the json from https://audl-stat-server.herokuapp.com/stats-pages/game/{game_id} for the given game id
# https://audl-stat-server.herokuapp.com/stats-pages/game/2021-06-04-TB-PHI
# Returns it as a python dict
def get_stats_for_game(game_id) -> dict:
    logging.info(f"Retrieving stats for game {game_id}")
    r = requests.get(f"https://audl-stat-server.herokuapp.com/stats-pages/game/{game_id}")
    return r.json()

# Returns a python dict
def load_data_from_file(filepath) -> dict:
    logging.info(f"Loading data from file {filepath}")
    # with open(r"F:\Media\smart-crop\audl_api\2022-05-07 CAR TB full_raw.json", 'r') as f:
    with open(filepath, 'r') as f:
        d = json.load(f)
    return d

# Logs all info to console, currently. should def slap it into a dataframe. Or just a mega-dict -> dataframe later
def parse_game_data(d):
    # Create a dict to store the players in
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

if __name__ == "__main__":
    # Load the event_types into event_ids dict
    with open("event_types.json", "r") as event_types:
        event_ids = json.load(event_types)

    # d = load_data_from_file(r"F:\Media\audl_api\2022-05-07 CAR TB full_raw.json")

    games = get_game_list_for_team("flyers")
    print(len(games))
    print(games)

    d = get_stats_for_game("2021-06-04-TB-PHI")
    # parse_game_data(d)