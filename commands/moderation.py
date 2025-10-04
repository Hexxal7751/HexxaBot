import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

def _is_admin(interaction: discord.Interaction) -> bool:
    """Check if user has administrator permissions."""
    return interaction.user.guild_permissions.administrator

class CleanupConfirmationModal(discord.ui.Modal):
    def __init__(self, supabase, guild_id: int, title: str = "Confirm Data Cleanup"):
        super().__init__(title=title)
        self.supabase = supabase
        self.guild_id = guild_id

    confirmation = discord.ui.TextInput(
        label="Type 'CONFIRM' to proceed",
        placeholder="CONFIRM",
        required=True,
        max_length=7,
    )

    async def on_submit(self, interaction: discord.Interaction):
        if self.confirmation.value.upper() != "CONFIRM":
            await interaction.response.send_message(
                "❌ Confirmation failed. Data cleanup cancelled.", ephemeral=True
            )
            return

        try:
            guild = interaction.guild
            
            # Define all possible game tables for this guild
            tables = [
                f"rps_stats_{self.guild_id}",
                f"guess_number_stats_{self.guild_id}",
                f"tictactoe_stats_{self.guild_id}",
                f"battle_stats_{self.guild_id}",
                f"flipnfind_stats_{self.guild_id}",
                f"kidnapped_jack_stats_{self.guild_id}"
                f"roulette_stats_{self.guild_id}"
            ]
            
            total_deleted = 0
            
            for table in tables:
                try:
                    # Get all users in this table
                    response = self.supabase.table(table).select("user_id").execute()
                    
                    if response.data:
                        # Verify membership per user id without relying on cache
                        for row in response.data:
                            user_id = row.get("user_id")
                            if not user_id:
                                continue
                            try:
                                # Try REST fetch; if user is in guild, this succeeds
                                await guild.fetch_member(int(user_id))
                                # Member exists; do not delete
                                continue
                            except discord.NotFound:
                                # Member not found in guild; delete their rows
                                self.supabase.table(table).delete().eq("user_id", user_id).execute()
                                total_deleted += 1
                            except discord.HTTPException:
                                # On API error, skip deletion to be safe
                                logger.warning(f"Skipped deletion for {user_id} in {table} due to HTTPException")
                                continue
                except Exception as e:
                    logger.warning(f"Could not clean table {table}: {e}")
                    # Continue with other tables even if one fails
                    continue
            
            await interaction.response.send_message(
                f"✅ Data cleanup completed!\n\n"
                f"Removed data for **{total_deleted}** users who left the server.",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
            await interaction.response.send_message(
                "❌ An error occurred during cleanup. Please try again.",
                ephemeral=True
            )

def setup(bot: discord.Client, supabase):
    """Register moderation commands."""
    
    # Add cleanup command
    @bot.tree.command(
        name="purge-data",
        description="Remove data for users who left the server (Admin only)",
    )
    async def purge_data(interaction: discord.Interaction):
        if not _is_admin(interaction):
            await interaction.response.send_message(
                "❌ This command is for administrators only!", ephemeral=True
            )
            return
        modal = CleanupConfirmationModal(
            supabase, interaction.guild.id, title="Confirm Data Cleanup"
        )
        await interaction.response.send_modal(modal)

    logger.info("Moderation commands loaded.")
