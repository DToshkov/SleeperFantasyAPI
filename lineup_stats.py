import requests
from pprint import pprint
import time

USER_ID = "<your user id here>"  # From SleerperId.py
LEAGUE_ID = "<youre league id here>"  # From settings.ini

def get_user(user_id):
    """Fetch user information by user_id."""
    response = requests.get(f"https://api.sleeper.app/v1/user/{user_id}")
    time.sleep(0.1)  # Avoid rate limits
    if response.status_code != 200:
        print(f"Error fetching user: {response.status_code} - {response.text}")
        return None
    return response.json()

def get_lineup(league_id, user_id, week=None):
    """Fetch and display the lineup and bench, with start/sit recommendations."""
    # Get user info
    user = get_user(user_id)
    if not user:
        return
    print(f"User Info: {user['display_name']} (User ID: {user_id})")

    # Get current week from NFL state if not specified
    if not week:
        state_response = requests.get("https://api.sleeper.app/v1/state/nfl")
        time.sleep(0.1)
        if state_response.status_code != 200:
            print(f"Error fetching NFL state: {state_response.status_code}")
            return
        week = state_response.json()["week"]

    # Get rosters for the league
    rosters_response = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters")
    time.sleep(0.1)
    if rosters_response.status_code != 200:
        print(f"Error fetching rosters: {rosters_response.status_code}")
        return
    rosters = rosters_response.json()

    # Find the user's roster
    user_roster = next((r for r in rosters if r["owner_id"] == user_id), None)
    if not user_roster:
        print(f"No roster found for user_id {user_id} in league {league_id}")
        return

    # Get matchups for the specified week
    matchups_response = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}")
    time.sleep(0.1)
    if matchups_response.status_code != 200:
        print(f"Error fetching matchups: {matchups_response.status_code}")
        return
    matchups = matchups_response.json()

    # Find matchup for the user's roster
    roster_id = user_roster["roster_id"]
    matchup = next((m for m in matchups if m["roster_id"] == roster_id), None)
    if not matchup:
        print(f"No matchup found for {user['display_name']} (Roster ID: {roster_id})")
        return

    # Get starting lineup and bench
    starters = matchup.get("starters", [])
    players_on_roster = user_roster.get("players", [])  # All players on roster
    bench = [p for p in players_on_roster if p not in starters]

    # Fetch player metadata and projections
    players_response = requests.get("https://api.sleeper.app/v1/players/nfl")
    time.sleep(0.1)
    if players_response.status_code != 200:
        print(f"Error fetching players: {players_response.status_code}")
        players = {}
    else:
        players = players_response.json()

    projections_response = requests.get(f"https://api.sleeper.app/v1/projections/nfl/{week}/season/standard")
    time.sleep(0.1)
    if projections_response.status_code != 200:
        print(f"Error fetching projections: {projections_response.status_code}")
        projections = {}
    else:
        projections = projections_response.json()

    # Display starting lineup with projected points
    print(f"\nStarting Lineup for {user['display_name']} (Week {week}):")
    starter_stats = []
    if not starters:
        print("  No starters set")
    else:
        for player_id in starters:
            player = players.get(player_id, {})
            name = player.get("full_name", player_id)
            position = player.get("position", "N/A")
            projection = projections.get(player_id, {}).get("pts_std", 0.0)
            starter_stats.append({"name": name, "position": position, "projected_points": projection})
            print(f"  - {name} ({position}): {projection:.2f} projected points")

    # Display bench with projected points
    print(f"\nBench for {user['display_name']} (Week {week}):")
    bench_stats = []
    if not bench:
        print("  No bench players")
    else:
        for player_id in bench:
            player = players.get(player_id, {})
            name = player.get("full_name", player_id)
            position = player.get("position", "N/A")
            projection = projections.get(player_id, {}).get("pts_std", 0.0)
            bench_stats.append({"name": name, "position": position, "projected_points": projection})
            print(f"  - {name} ({position}): {projection:.2f} projected points")

    # Recommend players to start (basic: higher projected points by position)
    print(f"\nStart/Sit Recommendations for {user['display_name']} (Week {week}):")
    positions = ["QB", "RB", "WR", "TE", "K", "DEF"]  # Common fantasy positions
    for position in positions:
        # Get starters and bench players for this position
        pos_starters = [s for s in starter_stats if s["position"] == position]
        pos_bench = [b for b in bench_stats if b["position"] == position]
        if not pos_bench or not pos_starters:
            continue
        # Find bench players with higher projected points than starters
        for bench_player in pos_bench:
            for starter in pos_starters:
                if bench_player["projected_points"] > starter["projected_points"]:
                    print(f"  Consider starting {bench_player['name']} ({bench_player['projected_points']:.2f} pts) "
                          f"over {starter['name']} ({starter['projected_points']:.2f} pts) at {position}")

if __name__ == "__main__":
    get_lineup(LEAGUE_ID, USER_ID)