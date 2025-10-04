import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from utils.database import create_server_tables, clean_missing_users_data
from commands import basic, rps, guess_number, tictactoe, battle, flipnfind, kidnapped_jack, moderation, economy, roulette, job
from keep_alive import keep_alive

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validate environment variables
if not all([TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    missing_vars = []
    if not TOKEN: missing_vars.append("DISCORD_TOKEN")
    if not SUPABASE_URL: missing_vars.append("SUPABASE_URL")
    if not SUPABASE_KEY: missing_vars.append("SUPABASE_KEY")
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Initialize bot with necessary intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # Required for reading message content
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize Supabase with error handling
try:
    logger.info("Initializing Supabase client...")
    # Create client with older API for compatibility
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    logger.error("This might be due to version compatibility issues.")
    logger.error("Try running: pip install supabase==1.2.0")
    raise

# Load commands
@bot.event
async def on_ready():
    try:
        # Sync commands with Discord
        logger.info("Syncing commands with Discord...")
        await bot.tree.sync()
        
        # Log available commands
        commands = [cmd.name for cmd in bot.tree.get_commands()]
        logger.info(f"Available commands after sync: {commands}")
        
        print(f"Logged in as {bot.user} and synced commands.")
        print(f"Available commands: {commands}")
        
        # Ensure tables exist for each guild
        for guild in bot.guilds:
            try:
                logger.info(f"Creating tables for guild {guild.id}")
                create_server_tables(supabase, guild.id)
            except Exception as e:
                logger.error(f"Failed to create tables for guild {guild.id}: {str(e)}")
                print(f"\nERROR: Could not create tables for guild {guild.id}")
                print("Make sure you've created the create_guild_tables function in your Supabase SQL editor.")
                print("Visit the bot status page for setup instructions.")
    
    except Exception as e:
        logger.error(f"Error in on_ready event: {str(e)}")
        raise
@bot.event
async def on_guild_join(guild):
    try:
        logger.info(f"Bot joined guild {guild.id}, creating tables...")
        create_server_tables(supabase, guild.id)
    except Exception as e:
        logger.error(f"Failed to create tables for guild {guild.id}: {str(e)}")
        print(f"\nERROR: Could not create tables for guild {guild.id}")
        print("Make sure you've created the create_guild_tables function in your Supabase SQL editor.")
        print("Visit the bot status page for setup instructions.")

# Add command modules
basic.setup(bot)
rps.setup(bot, supabase)
guess_number.setup(bot, supabase)
tictactoe.setup(bot, supabase)
battle.setup(bot, supabase)
flipnfind.setup(bot, supabase)
kidnapped_jack.setup(bot, supabase)
moderation.setup(bot, supabase)
economy.setup(bot, supabase)
roulette.setup(bot, supabase)
job.setup(bot, supabase)

# Keep bot alive with Supabase keepalive
keep_alive(supabase)
bot.run(TOKEN)
