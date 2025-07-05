import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from utils.database import create_server_tables, clean_missing_users_data
from commands import basic, rps, guess_number, tictactoe, battle, flipnfind
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
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    raise

# Confirmation dialog for data cleanup
class CleanupConfirmationModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.add_item(discord.ui.TextInput(
            label="Type 'CONFIRM CLEANUP' to proceed",
            placeholder="CONFIRM CLEANUP",
            required=True,
            max_length=20
        ))
    
    async def on_submit(self, interaction: discord.Interaction):
        # Get confirmation value
        confirmation = self.children[0].value
        
        if confirmation != "CONFIRM CLEANUP":
            await interaction.response.send_message("❌ Cleanup cancelled. Confirmation text did not match.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get all current member IDs in the guild
            member_ids = []
            async for member in interaction.guild.fetch_members(limit=None):
                member_ids.append(str(member.id))
            
            # Call the cleanup function
            deleted_rps, deleted_guess = await clean_missing_users_data(supabase, interaction.guild, member_ids)
            
            total_deleted = deleted_rps + deleted_guess
            if total_deleted > 0:
                await interaction.followup.send(
                    f"✅ Cleanup completed successfully!\n"
                    f"Removed data for users who left the server:\n"
                    f"• RPS entries deleted: {deleted_rps}\n"
                    f"• Guess Number entries deleted: {deleted_guess}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send("✅ No data needed to be cleaned up. All user data is for current server members.", ephemeral=True)
        
        except Exception as e:
            logger.error(f"Error during data cleanup: {str(e)}")
            await interaction.followup.send(f"❌ An error occurred during cleanup: {str(e)}", ephemeral=True)
    
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        logger.error(f"Error in cleanup confirmation modal: {str(error)}")
        await interaction.followup.send("❌ Something went wrong with the cleanup operation.", ephemeral=True)

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

# Add cleanup command
@bot.tree.command(name="purge-data", description="Remove data for users who left the server (Admin only)")
async def purge_data(interaction: discord.Interaction):
    # Check if user is an admin
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ This command is for administrators only!", ephemeral=True)
        return
    
    # Show confirmation dialog
    modal = CleanupConfirmationModal(title="Confirm Data Cleanup")
    await interaction.response.send_modal(modal)

# Add command modules
basic.setup(bot)
rps.setup(bot, supabase)
guess_number.setup(bot, supabase)
tictactoe.setup(bot, supabase)
battle.setup(bot, supabase)
flipnfind.setup(bot, supabase)

# Keep bot alive
keep_alive()
bot.run(TOKEN)
