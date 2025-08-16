from supabase import create_client
import json
import logging

logger = logging.getLogger(__name__)

def create_server_tables(supabase, guild_id):
    """Create all necessary tables for a guild by calling the Supabase function."""
    try:
        logger.info(f"Attempting to create tables for guild {guild_id} via RPC...")
        # Try the RPC call first
        supabase.rpc("create_guild_tables", {"guild_id": str(guild_id)}).execute()
        logger.info(f"Successfully called create_guild_tables RPC for guild {guild_id}. Tables should be up-to-date.")
    except Exception as e:
        logger.warning(f"RPC call failed for guild {guild_id}: {str(e)}")
        logger.info("This is normal if the SQL function hasn't been created yet.")
        logger.info("Tables will be created automatically when games are played.")
        
        # Don't treat this as a critical error - the bot can still function
        # Tables will be created when needed by individual game functions
        
# Individual table creation functions are now just fallbacks and for reference
def create_rps_table(supabase, guild_id):
    """Create the RPS stats table for a guild if it doesn't exist."""
    table_name = f"rps_stats_{guild_id}"
    
    try:
        # Check if table exists
        response = supabase.table(table_name).select("*").limit(1).execute()
        logger.info(f"Table {table_name} already exists")
    except Exception as e:
        logger.error(f"Table {table_name} doesn't exist: {str(e)}")
        # We don't try to create directly - this is now handled by the create_guild_tables function

def create_guess_number_table(supabase, guild_id):
    """Create the Guess Number stats table for a guild if it doesn't exist."""
    table_name = f"guess_number_stats_{guild_id}"
    
    try:
        # Check if table exists
        response = supabase.table(table_name).select("*").limit(1).execute()
        logger.info(f"Table {table_name} already exists")
    except Exception as e:
        logger.error(f"Table {table_name} doesn't exist: {str(e)}")
        # We don't try to create directly - this is now handled by the create_guild_tables function

def create_tictactoe_table(supabase, guild_id):
    """Create the Tic Tac Toe stats table for a guild if it doesn't exist."""
    table_name = f"tictactoe_stats_{guild_id}"
    
    try:
        # Check if table exists
        response = supabase.table(table_name).select("*").limit(1).execute()
        logger.info(f"Table {table_name} already exists")
    except Exception as e:
        logger.error(f"Table {table_name} doesn't exist: {str(e)}")
        # We don't try to create directly - this is now handled by the create_guild_tables function

def get_tictactoe_stats(supabase, guild_id, user_id):
    """Get Tic Tac Toe stats for a user."""
    table_name = f"tictactoe_stats_{guild_id}"
    
    try:
        response = supabase.table(table_name).select("*").eq("user_id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error getting Tic Tac Toe stats: {str(e)}")
        return None

def update_tictactoe_stats(supabase, guild_id, user_id, result):
    """Update Tic Tac Toe stats for a user."""
    table_name = f"tictactoe_stats_{guild_id}"
    
    try:
        # Get current stats
        current_stats = get_tictactoe_stats(supabase, guild_id, user_id)
        
        if current_stats:
            # Update existing stats
            updates = {
                "total_games": current_stats["total_games"] + 1
            }
            
            if result == "win":
                updates["wins"] = current_stats["wins"] + 1
            elif result == "loss":
                updates["losses"] = current_stats["losses"] + 1
            elif result == "draw":
                updates["draws"] = current_stats["draws"] + 1
                
            supabase.table(table_name).update(updates).eq("user_id", user_id).execute()
        else:
            # Create new stats
            new_stats = {
                "user_id": user_id,
                "wins": 1 if result == "win" else 0,
                "losses": 1 if result == "loss" else 0,
                "draws": 1 if result == "draw" else 0,
                "total_games": 1
            }
            supabase.table(table_name).insert(new_stats).execute()
            
    except Exception as e:
        logger.error(f"Error updating Tic Tac Toe stats: {str(e)}")
        raise

def get_tictactoe_leaderboard(supabase, guild_id, limit=10):
    """Get Tic Tac Toe leaderboard for a guild."""
    table_name = f"tictactoe_stats_{guild_id}"
    
    try:
        response = supabase.table(table_name).select("*").order("wins", desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error getting Tic Tac Toe leaderboard: {str(e)}")
        return []

# ✅ RPS Functions
def get_rps_stats(supabase, guild_id, user_id):
    """Fetch user stats for Rock Paper Scissors."""
    if not guild_id:
        logger.error("No guild_id provided for get_rps_stats")
        return None

    table = f"rps_stats_{guild_id}"
    try:
        response = supabase.table(table).select("*").eq("user_id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error getting RPS stats for user {user_id} in guild {guild_id}: {str(e)}")
        return None

def update_rps_stats(supabase, guild_id, user_id, result):
    """Update user stats for Rock Paper Scissors."""
    if not guild_id:
        logger.error("No guild_id provided for update_rps_stats")
        return

    table = f"rps_stats_{guild_id}"
    try:
        stats = get_rps_stats(supabase, guild_id, user_id)

        if stats:
            update_data = {
                "wins": stats["wins"] + (1 if result == "win" else 0),
                "losses": stats["losses"] + (1 if result == "loss" else 0),
                "ties": stats["ties"] + (1 if result == "tie" else 0),
                "total_games": stats["total_games"] + 1
            }
            supabase.table(table).update(update_data).eq("user_id", user_id).execute()
            logger.info(f"Updated RPS stats for user {user_id} in guild {guild_id}")
        else:
            supabase.table(table).insert({
                "user_id": user_id,
                "wins": 1 if result == "win" else 0,
                "losses": 1 if result == "loss" else 0,
                "ties": 1 if result == "tie" else 0,
                "total_games": 1
            }).execute()
            logger.info(f"Created new RPS stats for user {user_id} in guild {guild_id}")
    except Exception as e:
        logger.error(f"Error updating RPS stats for user {user_id} in guild {guild_id}: {str(e)}")
        raise

def get_rps_leaderboard(supabase, guild_id, limit=10):
    """Get the RPS leaderboard for a guild."""
    if not guild_id:
        logger.error("No guild_id provided for get_rps_leaderboard")
        return []

    table = f"rps_stats_{guild_id}"
    try:
        # Use the table API directly instead of raw SQL
        logger.info(f"Fetching RPS leaderboard for guild {guild_id}")
        response = supabase.table(table).select("*").gte("total_games", 1).execute()
        
        if not response.data:
            logger.info(f"No RPS data found for guild {guild_id}")
            return []
            
        # Sort the data in Python
        players = response.data
        
        # Calculate win percentage for sorting
        for player in players:
            total = player.get("total_games", 0)
            if total > 0:
                player["win_percentage"] = (player.get("wins", 0) / total) * 100
            else:
                player["win_percentage"] = 0
        
        # Sort by win percentage then by wins
        players.sort(key=lambda x: (x.get("win_percentage", 0), x.get("wins", 0)), reverse=True)
        
        logger.info(f"Found {len(players)} players for RPS leaderboard in guild {guild_id}")
        return players[:limit]
    except Exception as e:
        logger.error(f"Error getting RPS leaderboard for guild {guild_id}: {str(e)}")
        return []


# ✅ Guess Number Functions
def get_guess_stats(supabase, guild_id, user_id):
    """Fetch user stats for the Guess Number game."""
    if not guild_id:
        logger.error("No guild_id provided for get_guess_stats")
        return None

    table = f"guess_number_stats_{guild_id}"
    try:
        response = supabase.table(table).select("*").eq("user_id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error getting guess stats for user {user_id} in guild {guild_id}: {str(e)}")
        return None

def update_guess_stats(supabase, guild_id, user_id, result, guesses, guess_gaps):
    """Update user stats for the Guess Number game."""
    if not guild_id:
        logger.error("No guild_id provided for update_guess_stats")
        return

    table = f"guess_number_stats_{guild_id}"
    try:
        stats = get_guess_stats(supabase, guild_id, user_id)

        # Convert lists to JSON strings
        guesses_json = json.dumps(guesses)
        guess_gaps_json = json.dumps(guess_gaps)

        if stats:
            new_correct = stats["correct_guesses"] + (1 if result == "correct" else 0)
            new_incorrect = stats["incorrect_guesses"] + (1 if result == "incorrect" else 0)
            new_total = stats["total_games"] + 1

            supabase.table(table).update({
                "correct_guesses": new_correct,
                "incorrect_guesses": new_incorrect,
                "total_games": new_total,
                "guesses": guesses_json,
                "guess_gaps": guess_gaps_json
            }).eq("user_id", user_id).execute()
            logger.info(f"Updated guess stats for user {user_id} in guild {guild_id}")
        else:
            supabase.table(table).insert({
                "user_id": user_id,
                "correct_guesses": 1 if result == "correct" else 0,
                "incorrect_guesses": 1 if result == "incorrect" else 0,
                "total_games": 1,
                "guesses": guesses_json,
                "guess_gaps": guess_gaps_json
            }).execute()
            logger.info(f"Created new guess stats for user {user_id} in guild {guild_id}")
    except Exception as e:
        logger.error(f"Error updating guess stats for user {user_id} in guild {guild_id}: {str(e)}")
        raise

def get_guess_number_leaderboard(supabase, guild_id, limit=10):
    """Get the Guess Number leaderboard for a guild."""
    if not guild_id:
        logger.error("No guild_id provided for get_guess_number_leaderboard")
        return []

    table = f"guess_number_stats_{guild_id}"
    try:
        # Use the table API directly instead of raw SQL
        logger.info(f"Fetching Guess Number leaderboard for guild {guild_id}")
        response = supabase.table(table).select("*").gte("total_games", 1).execute()
        
        if not response.data:
            logger.info(f"No Guess Number data found for guild {guild_id}")
            return []
            
        # Sort the data in Python
        players = response.data
        
        # Calculate success rate for sorting
        for player in players:
            total = player.get("total_games", 0)
            if total > 0:
                player["success_rate"] = (player.get("correct_guesses", 0) / total) * 100
            else:
                player["success_rate"] = 0
        
        # Sort by success rate then by correct guesses
        players.sort(key=lambda x: (x.get("success_rate", 0), x.get("correct_guesses", 0)), reverse=True)
        
        logger.info(f"Found {len(players)} players for Guess Number leaderboard in guild {guild_id}")
        return players[:limit]
    except Exception as e:
        logger.error(f"Error getting Guess Number leaderboard for guild {guild_id}: {str(e)}")
        return []

# ✅ Cleanup Functions
async def get_all_users_data(supabase, guild_id):
    """Get all users with stats in the database for a guild."""
    if not guild_id:
        logger.error("No guild_id provided for get_all_users_data")
        return []
    
    rps_table = f"rps_stats_{guild_id}"
    guess_table = f"guess_number_stats_{guild_id}"
    users = set()
    
    try:
        # Get RPS users
        rps_response = supabase.table(rps_table).select("user_id").execute()
        if rps_response.data:
            for entry in rps_response.data:
                users.add(entry.get("user_id"))
        
        # Get Guess Number users
        guess_response = supabase.table(guess_table).select("user_id").execute()
        if guess_response.data:
            for entry in guess_response.data:
                users.add(entry.get("user_id"))
        
        return list(users)
    except Exception as e:
        logger.error(f"Error getting all users data for guild {guild_id}: {str(e)}")
        return []

async def clean_missing_users_data(supabase, guild, member_ids):
    """Remove data for users who are not in the member_ids list."""
    if not guild or not guild.id:
        logger.error("No guild provided for clean_missing_users_data")
        return 0, 0
    
    guild_id = str(guild.id)
    rps_table = f"rps_stats_{guild_id}"
    guess_table = f"guess_number_stats_{guild_id}"
    
    deleted_rps = 0
    deleted_guess = 0
    
    try:
        # Get all users in database
        all_db_users = await get_all_users_data(supabase, guild_id)
        
        # Find users to delete (in DB but not in member_ids)
        users_to_delete = [user_id for user_id in all_db_users if user_id not in member_ids]
        
        if not users_to_delete:
            return 0, 0
        
        logger.info(f"Cleaning up data for {len(users_to_delete)} users in guild {guild_id}")
        
        # Delete users from RPS table
        for user_id in users_to_delete:
            try:
                resp = supabase.table(rps_table).delete().eq("user_id", user_id).execute()
                if resp and resp.data:
                    deleted_rps += len(resp.data) 
            except Exception as e:
                logger.error(f"Error deleting RPS data for user {user_id}: {str(e)}")
        
        # Delete users from Guess Number table
        for user_id in users_to_delete:
            try:
                resp = supabase.table(guess_table).delete().eq("user_id", user_id).execute()
                if resp and resp.data:
                    deleted_guess += len(resp.data)
            except Exception as e:
                logger.error(f"Error deleting Guess Number data for user {user_id}: {str(e)}")
        
        logger.info(f"Deleted {deleted_rps} RPS entries and {deleted_guess} Guess Number entries")
        return deleted_rps, deleted_guess
    
    except Exception as e:
        logger.error(f"Error in clean_missing_users_data for guild {guild_id}: {str(e)}")
        return 0, 0

# ✅ Battle Game Functions

def create_battle_table(supabase, guild_id):
    """Create the Battle stats table for a guild if it doesn't exist."""
    table_name = f"battle_stats_{guild_id}"
    try:
        # Check if table exists
        response = supabase.table(table_name).select("*").limit(1).execute()
        logger.info(f"Table {table_name} already exists")
    except Exception as e:
        logger.error(f"Table {table_name} doesn't exist: {str(e)}")
        # We don't try to create directly - this is now handled by the create_guild_tables function

def get_battle_stats(supabase, guild_id, user_id):
    """Get Battle stats for a user."""
    table_name = f"battle_stats_{guild_id}"
    try:
        response = supabase.table(table_name).select("*").eq("user_id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error getting Battle stats: {str(e)}")
        return None

def update_battle_stats(supabase, guild_id, user_id, result):
    """Update Battle stats for a user."""
    table_name = f"battle_stats_{guild_id}"
    try:
        current_stats = get_battle_stats(supabase, guild_id, user_id)
        if current_stats:
            updates = {
                "total_games": current_stats["total_games"] + 1
            }
            if result == "win":
                updates["wins"] = current_stats["wins"] + 1
            elif result == "loss":
                updates["losses"] = current_stats["losses"] + 1
            supabase.table(table_name).update(updates).eq("user_id", user_id).execute()
        else:
            new_stats = {
                "user_id": user_id,
                "wins": 1 if result == "win" else 0,
                "losses": 1 if result == "loss" else 0,
                "total_games": 1
            }
            supabase.table(table_name).insert(new_stats).execute()
    except Exception as e:
        logger.error(f"Error updating Battle stats: {str(e)}")
        raise

def get_battle_leaderboard(supabase, guild_id, limit=10):
    """Get Battle leaderboard for a guild."""
    table_name = f"battle_stats_{guild_id}"
    try:
        response = supabase.table(table_name).select("*").order("wins", desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error getting Battle leaderboard: {str(e)}")
        return []

# ✅ Flip & Find Functions

def create_flipnfind_table(supabase, guild_id):
    """Create the Flip & Find stats table for a guild if it doesn't exist."""
    table_name = f"flipnfind_stats_{guild_id}"
    try:
        # Check if table exists
        response = supabase.table(table_name).select("*").limit(1).execute()
        logger.info(f"Table {table_name} already exists")
    except Exception as e:
        logger.error(f"Table {table_name} doesn't exist: {str(e)}")
        # We don't try to create directly - this is now handled by the create_guild_tables function

def get_flipnfind_stats(supabase, guild_id, user_id):
    """Get Flip & Find stats for a user (now per-difficulty, user_id should be f'{user_id}_{difficulty}')."""
    table_name = f"flipnfind_stats_{guild_id}"
    try:
        response = supabase.table(table_name).select("*").eq("user_id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error getting Flip & Find stats: {str(e)}")
        return None

def update_flipnfind_stats(supabase, guild_id, user_id, result, game_time=None, turns=None, star_cards=None):
    """Update Flip & Find stats for a user (now per-difficulty, user_id should be f'{user_id}_{difficulty}')."""
    table_name = f"flipnfind_stats_{guild_id}"
    try:
        current_stats = get_flipnfind_stats(supabase, guild_id, user_id)
        updates = {}
        if current_stats:
            updates = {
                "total_games": current_stats["total_games"] + 1,
                "total_turns": current_stats["total_turns"] + (turns or 0),
                "total_time": current_stats["total_time"] + (game_time or 0)
            }
            if result == "win":
                updates["wins"] = current_stats["wins"] + 1
            elif result == "loss":
                updates["losses"] = current_stats["losses"] + 1
            if game_time and (current_stats["best_time"] is None or game_time < current_stats["best_time"]):
                updates["best_time"] = game_time
            if turns and (current_stats["best_turns"] is None or turns < current_stats["best_turns"]):
                updates["best_turns"] = turns
            if star_cards is not None:
                updates["star_cards"] = current_stats.get("star_cards", 0) + star_cards
            supabase.table(table_name).update(updates).eq("user_id", user_id).execute()
        else:
            new_stats = {
                "user_id": user_id,
                "wins": 1 if result == "win" else 0,
                "losses": 1 if result == "loss" else 0,
                "total_games": 1,
                "total_turns": turns or 0,
                "total_time": game_time or 0,
                "best_time": game_time,
                "best_turns": turns
            }
            if star_cards is not None:
                new_stats["star_cards"] = star_cards
            supabase.table(table_name).insert(new_stats).execute()
    except Exception as e:
        logger.error(f"Error updating Flip & Find stats: {str(e)}")
        raise

def get_flipnfind_leaderboard(supabase, guild_id, limit=10):
    """Get Flip & Find leaderboard for a guild (sum stats across all difficulties for each user)."""
    table_name = f"flipnfind_stats_{guild_id}"
    try:
        response = supabase.table(table_name).select("*").execute()
        if not response.data:
            return []
        from collections import defaultdict
        agg = defaultdict(lambda: {"wins": 0, "losses": 0, "total_games": 0, "star_cards": 0, "user_id": None})
        for row in response.data:
            base_id = row["user_id"].split("_")[0]
            agg[base_id]["user_id"] = base_id
            agg[base_id]["wins"] += row.get("wins", 0)
            agg[base_id]["losses"] += row.get("losses", 0)
            agg[base_id]["total_games"] += row.get("total_games", 0)
            agg[base_id]["star_cards"] += row.get("star_cards", 0)
        leaderboard = sorted(agg.values(), key=lambda x: (x["wins"], x["star_cards"]), reverse=True)
        return leaderboard[:limit]
    except Exception as e:
        logger.error(f"Error getting Flip & Find leaderboard: {str(e)}")
        return []

# ✅ The Kidnapped Jack Functions

def create_kidnapped_jack_table(supabase, guild_id):
    """Create the Kidnapped Jack stats table for a guild if it doesn't exist."""
    table_name = f"kidnapped_jack_stats_{guild_id}"
    try:
        # Check if table exists by trying to query it
        response = supabase.table(table_name).select("*").limit(1).execute()
        logger.info(f"Table {table_name} already exists")
    except Exception as e:
        logger.error(f"Table {table_name} doesn't exist or is inaccessible: {str(e)}")
        logger.error("This table should be created by the create_guild_tables SQL function.")
        logger.error("Please run the create_guild_tables function in your Supabase SQL editor.")
        # Don't raise the exception - let the game continue without stats
        return False
    return True

def get_kidnapped_jack_stats(supabase, guild_id, user_id):
    """Get Kidnapped Jack stats for a user."""
    table_name = f"kidnapped_jack_stats_{guild_id}"
    try:
        response = supabase.table(table_name).select("*").eq("user_id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error getting Kidnapped Jack stats: {str(e)}")
        return None

def update_kidnapped_jack_stats(supabase, guild_id, user_id, result, game_time=None, win_place=0):
    """Update Kidnapped Jack stats for a user.
    
    Args:
        supabase: Supabase client
        guild_id: ID of the guild
        user_id: ID of the user
        result: 'escape' or 'kidnapper'
        game_time: Duration of the game in seconds
        win_place: Placement in the game (1 = first place, 2 = second, etc.)
    """
    table_name = f"kidnapped_jack_stats_{guild_id}"
    try:
        current_stats = get_kidnapped_jack_stats(supabase, guild_id, user_id)
        updates = {}
        
        if current_stats:
            # Update existing stats
            updates = {
                "games_played": current_stats.get("games_played", 0) + 1,
                "total_time": current_stats.get("total_time", 0) + (game_time or 0)
            }
            
            # Update result-specific stats
            if result == "escape":
                updates["escapes"] = current_stats.get("escapes", 0) + 1
            elif result == "kidnapper":
                updates["kidnapper_count"] = current_stats.get("kidnapper_count", 0) + 1
            
            # Update best time if this game was faster
            if game_time and (current_stats.get("best_time") is None or game_time < current_stats["best_time"]):
                updates["best_time"] = game_time
            
            # Update best placement if this is better
            if win_place > 0 and (current_stats.get("best_placement") is None or win_place < current_stats["best_placement"]):
                updates["best_placement"] = win_place
            
            # Update total wins and placements
            if win_place > 0:
                updates["total_wins"] = current_stats.get("total_wins", 0) + (1 if win_place == 1 else 0)
                updates["total_placements"] = current_stats.get("total_placements", 0) + 1
                updates["placement_sum"] = current_stats.get("placement_sum", 0) + win_place
            
            supabase.table(table_name).update(updates).eq("user_id", user_id).execute()
        else:
            # Create new stats entry
            new_stats = {
                "guild_id": guild_id,
                "user_id": user_id,
                "games_played": 1,
                "escapes": 1 if result == "escape" else 0,
                "kidnapper_count": 1 if result == "kidnapper" else 0,
                "total_time": game_time or 0,
                "best_time": game_time,
                "best_placement": win_place if win_place > 0 else None,
                "total_wins": 1 if win_place == 1 else 0,
                "total_placements": 1 if win_place > 0 else 0,
                "placement_sum": win_place if win_place > 0 else 0
            }
            supabase.table(table_name).insert(new_stats).execute()
    except Exception as e:
        logger.error(f"Error updating Kidnapped Jack stats: {str(e)}")
        raise

def get_kidnapped_jack_leaderboard(supabase, guild_id, limit=10):
    """Get Kidnapped Jack leaderboard for a guild."""
    table_name = f"kidnapped_jack_stats_{guild_id}"
    try:
        response = supabase.table(table_name).select("*").order("escapes", desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error getting Kidnapped Jack leaderboard: {str(e)}")
        return []
