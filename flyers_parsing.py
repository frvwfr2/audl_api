# -*- coding: utf-8 -*-
"""
Created on Mon May 16 06:45:55 2022

@author: JaysC
"""

import argparse
import json
import logging
import os
import requests

import pandas as pd

# Retrieves the game
def get_events_for_team(team_id, years_back) -> pd.DataFrame:
    pass

# URL to get matchups from -> https://audl-stat-server.herokuapp.com/web-api/games?limit=10&years=2021,2022&page=29
# team_id is generally the team mascot, all lowercase
# Returns a list of dicts
def get_game_list_for_team(team_id=None, years_back=2) -> list:
    # TODO - I don't think this gets all the games from 2021 as is 
    #   It only gets 8 for Raleigh but they played ~15 including playoffs
    
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

# Returns a python dict
def get_players_from_game(d):
    
    players_dict = dict()
    for player in d["rostersHome"]:
        players_dict[player["id"]] = f'{player["player"]["first_name"]} {player["player"]["last_name"]}'
    for player in d["rostersAway"]:
        players_dict[player["id"]] = f'{player["player"]["first_name"]} {player["player"]["last_name"]}'
    
    return players_dict

def get_game_tuple(d):
    game_id = d['game']['id']
    date = d['game']['start_timestamp'][0:10]
    home_team = d['game']['team_season_id_home']
    away_team = d['game']['team_season_id_away']
    
    
    ret_tup = (game_id, date, home_team, away_team)
    
    return ret_tup

# Logs all info to console, currently. should def slap it into a dataframe. Or just a mega-dict -> dataframe later
def parse_game_data(d, home_team=True, to_console=True):
    
    # Create a dict to store the players in
    players_dict = get_players_from_game(d)
    game_tup = get_game_tuple(d)
    
    if home_team:
        which_team = d["tsgHome"]
    else:
        which_team = d["tsgAway"]
    
    # Can change this for when we parse both teams
    team_id = which_team['teamSeasonId']
    
    events = json.loads(which_team["events"])
    # print(events)

    # Initializing some stuff we need later
    current_quarter = 0
    tup_list = []
    event_counter = 0
    
    # Columns for DataFrame
    event_columns = [
        "event_counter", "team_id", "current_quarter", "time", 
        "event_type", "player", "x", "y", "o_point", "d_point"
        ]
    game_colums = ["game_id", "date", "home_team", "away_team"]
    current_quarter = None
    o_point = False
    d_point = False
    
    # Locations of the previous event, to map the distance
    for e in events:
        
        # Initializing some stuff we need later
        player = ""
        time = ""
        x= ""
        y = ""
        
        
        # print(e)
        # event_type = e["t"]
        event_type = event_ids.get(str(e["t"]), None)
        
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
            
        # Handle Quarters
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
                for p in e.get("l"):
                    player += f'{players_dict[p]}, '
        # O Points and D Points
        if event_type == "SET_O_LINE":
            o_point = True
            d_point = False
        if event_type in ["SET_D_LINE"]:
            d_point = True
            o_point = False
        
        # Event Parsing
        
        # If we got a timestamp...
        if "s" in e:
            m, s = divmod(e.get("s"), 60)
            time = f'Q{current_quarter} {m:02d}:{s:02d} '
        
        # If there is a player associated with this event...
        if "r" in e:
            player = players_dict[e["r"]]
        
        # If there are x,y coordinates with this event
        if "x" in e:
            x = e['x']
        if "y" in e:
            y = e['y']   
        
        # Print Info to console
        if to_console:
            info = f"{spacing}{time}{event_type} {player} X: {x}, Y: {y}"
            print(info)
        # print(event_ids[str(e["t"])])
        
        # Same Info, but list of tuples
        # Could be a list of dicts or something but this is fine for now
        tup = ()
        for col in event_columns:
            tup += (vars()[col], )
        
        tup_list.append(tup)
        
        event_counter +=1
    
    # Add info about the game/teams
    full_tup_list = [game_tup + x for x in tup_list]
    
    full_column_list = game_colums + event_columns
    
    team_event_df = pd.DataFrame(full_tup_list, columns=full_column_list)
    
    if to_console:
        print(team_event_df.head())

    return team_event_df       

if __name__ == "__main__":
    # Load the event_types into event_ids dict
    with open("event_types.json", "r") as event_types:
        event_ids = json.load(event_types)

    # d = load_data_from_file(r"F:\Media\audl_api\2022-05-07 CAR TB full_raw.json")

    games = get_game_list_for_team("flyers", years_back=1)
    # print(games)
    # print(len(games))

    game_raw = get_stats_for_game("2021-06-04-TB-PHI")
    game_events = parse_game_data(game_raw, to_console=False)
    
    flyers_games = get_game_list_for_team(team_id="flyers", years_back=1)
    flyers_games_ids = [x['gameID'] for x in flyers_games]
    
    big_flyers_df = pd.DataFrame()
    
    for game in flyers_games_ids:
        single_game_raw = get_stats_for_game(game)
        print(game)
        single_game_events = parse_game_data(
            single_game_raw,
            home_team=True,
            to_console=False
            )

        big_flyers_df = pd.concat([big_flyers_df, single_game_events])
        
        single_game_events = parse_game_data(
            single_game_raw,
            home_team=False,
            to_console=False
            )

        big_flyers_df = pd.concat([big_flyers_df, single_game_events])
        
        output_file = "FlyersWeek3.csv"
        big_flyers_df.to_csv(
            os.path.join(os.path.abspath(""), output_file)
            )
    