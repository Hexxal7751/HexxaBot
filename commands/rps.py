import discord
import random
import logging
from discord import app_commands
from utils.database import get_rps_stats, update_rps_stats, get_rps_leaderboard

logger = logging.getLogger(__name__)

async def resolve_member_name(guild, user_id):
    """Helper function to try harder to resolve member names from IDs."""
    # First try from member cache
    member = guild.get_member(user_id)
    if member:
        return member.display_name
        
    # Try to fetch from API if not in cache
    try:
        member = await guild.fetch_member(user_id)
        return member.display_name
    except (discord.NotFound, discord.HTTPException):
        pass
    
    # Fall back to a nicer format than just the ID
    return f"Unknown Player"

def setup(bot, supabase):
    @bot.tree.command(name="rps", description="Play Rock Paper Scissors!")
    @app_commands.describe(choice="Your choice: rock, paper, or scissors")
    @app_commands.choices(
        choice=[
            app_commands.Choice(name="Rock", value="rock"),
            app_commands.Choice(name="Paper", value="paper"),
            app_commands.Choice(name="Scissors", value="scissors"),
        ]
    )
    async def rps(interaction: discord.Interaction, choice: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)  # Defer to avoid timeout

        bot_choice = random.choice(["rock", "paper", "scissors"])
        guild_id = interaction.guild_id
        user_id = str(interaction.user.id)

        result = (
            "tie" if choice.value == bot_choice else
            "win" if (choice.value, bot_choice) in [("rock", "scissors"), ("paper", "rock"), ("scissors", "paper")] else
            "loss"
        )

        if result == "win":
            result_message = f"🎉 You won!"
        elif result == "loss":
            result_message = f"❌ You lost!"
        elif result == "tie":
            result_message = f"🤝 It's a tie! Both chose {choice.value.capitalize()}!"        

        try:
            update_rps_stats(supabase, guild_id, user_id, result)
        except Exception as e:
            logger.error(f"Failed to update RPS stats: {str(e)}")
            # Continue with the game even if stats update fails
            result_message += "\n⚠️ Could not update stats due to a database error."

        if interaction.response.is_done():
            await interaction.followup.send(f"You chose **{choice.name}**, I chose **{bot_choice.capitalize()}**. {result.capitalize()}!\n{result_message}")
        else:
            await interaction.response.send_message(f"You chose **{choice.name}**, I chose **{bot_choice.capitalize()}**. {result.capitalize()}!\n{result_message}")

    @bot.tree.command(name="rps-stats", description="Check RPS stats")
    async def rps_stats(interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer(ephemeral=True)  # Defer to avoid timeout

        guild_id = interaction.guild_id
        user_id = str(member.id if member else interaction.user.id)
        user_name = member.name if member else interaction.user.name
        
        try:
            stats = get_rps_stats(supabase, guild_id, user_id)
            if stats:
                wins = stats["wins"]
                losses = stats["losses"]
                ties = stats["ties"]
                total_games = stats["total_games"]
                await interaction.followup.send(
                    f"📊 **{user_name}'s RPS Stats**\n\n"
                    f"🏆 Wins: {wins}\n"
                    f"❌ Losses: {losses}\n"
                    f"🤝 Ties: {ties}\n"
                    f"🎮 Total Games Played: {total_games}"
                )
            else:
                await interaction.followup.send(f"{user_name} hasn't played Rock Paper Scissors yet!")
        except Exception as e:
            logger.error(f"Failed to get RPS stats: {str(e)}")
            await interaction.followup.send("⚠️ Could not retrieve stats due to a database error.")
            
    @bot.tree.command(name="rps-lb", description="Show Rock Paper Scissors leaderboard")
    async def rps_leaderboard(interaction: discord.Interaction):
        await interaction.response.defer()  # Defer but not ephemeral
        
        guild_id = interaction.guild_id
        if not guild_id:
            await interaction.followup.send("This command can only be used in a server.")
            return
            
        try:
            leaderboard_data = get_rps_leaderboard(supabase, guild_id, 10)
            
            if not leaderboard_data:
                await interaction.followup.send("No one has played Rock Paper Scissors yet!")
                return
                
            # Create a nice-looking embed for the leaderboard
            embed = discord.Embed(
                title="🏆 Rock Paper Scissors Leaderboard 🏆",
                description="Top 10 players ranked by win percentage",
                color=0x00ff00  # Green color
            )
            
            # Add guild icon to the embed if available
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
                
            # Add server name
            embed.set_author(name=interaction.guild.name)
            
            # Add footer
            embed.set_footer(text=f"Requested by {interaction.user.name}", 
                           icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            
            # Format the leaderboard
            leaderboard_text = ""
            
            for i, player_data in enumerate(leaderboard_data, 1):
                # Get user info if possible
                user_id = int(player_data.get("user_id", "0"))
                display_name = await resolve_member_name(interaction.guild, user_id)
                
                # Calculate win percentage
                wins = player_data.get("wins", 0)
                losses = player_data.get("losses", 0)
                ties = player_data.get("ties", 0)
                total = player_data.get("total_games", 0)
                win_rate = (wins / total * 100) if total > 0 else 0
                
                # Format medal for top 3
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`#{i}`"
                
                # Add player to the leaderboard text with better formatting
                leaderboard_text += f"**{medal} {display_name}**\n"
                leaderboard_text += f"┣ Win Rate: **{win_rate:.1f}%**\n"
                leaderboard_text += f"┣ W: **{wins}** ┃ L: **{losses}** ┃ T: **{ties}**\n"
                leaderboard_text += f"┗ Total Games: **{total}**\n\n"
            
            # Add the formatted text to the embed
            embed.description = f"Top 10 players ranked by win percentage\n\n{leaderboard_text}"
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to get RPS leaderboard: {str(e)}")
            await interaction.followup.send("⚠️ Could not retrieve the leaderboard due to an error.")
