import requests
from pprint import pprint

LEAGUE_ID = "<your league ID here>"  # From settings.ini

def find_user_id(league_id, username=None):
    response = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/users")
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    users = response.json()
    print("Users in league:")
    for user in users:
        print(f"{user['display_name']} \t {user['user_id']}")
        # Check for username in metadata or directly
        user_name = user.get("metadata", {}).get("username", user.get("username", ""))
        if username and user_name.lower() == username.lower():
            return user["user_id"]
    return None

def get_lineup(league_id, user_id, week=None):
    """Fetch and display the lineup for the given user in the specified league."""
    # Get user info
    user_response = requests.get(f"https://api.sleeper.app/v1/user/{user_id}")
    if user_response.status_code != 200:
        print(f"Error fetching user: {user_response.status_code} - {user_response.text}")
        return
    user = user_response.json()
    print(f"User Info: {user['display_name']} (Username: {user['username']})")

    # Get current week from NFL state if not specified
    if not week:
        state_response = requests.get("https://api.sleeper.app/v1/state/nfl")
        if state_response.status_code != 200:
            print(f"Error fetching NFL state: {state_response.status_code}")
            return
        week = state_response.json()["week"]

    # Get rosters for the league
    rosters_response = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters")
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

    # Get starting lineup
    starters = matchup.get("starters", [])
    print(f"\nLineup for {user['display_name']} (Week {week}):")
    if not starters:
        print("  No starters set")
    else:
        # Fetch player names (optional, minimal storage)
        players_response = requests.get("https://api.sleeper.app/v1/players/nfl")
        if players_response.status_code != 200:
            print(f"Error fetching players: {players_response.status_code}")
            players = {}
        else:
            players = players_response.json()
        for player_id in starters:
            player = players.get(player_id, {})
            name = player.get("full_name", player_id)
            print(f"  - {name}")

if __name__ == "__main__":
    # Step 1: Find user_id (replace 'your_username' with your Sleeper username if known)
    username = "your_username"  # Replace with your actual Sleeper username
    user_id = find_user_id(LEAGUE_ID, username)
    if user_id:
        print(f"\nFound user_id for {username}: {user_id}")
        # Step 2: Get lineup for the found user_id
        get_lineup(LEAGUE_ID, user_id)
    else:
        print(f"\nUsername {username} not found in league {LEAGUE_ID}")
        # Fallback: Try the user_id from SleerperId.py
        user_id = "1259559664937349120"
        print(f"Trying user_id from SleerperId.py: {user_id}")
        get_lineup(LEAGUE_ID, user_id)