import discord
import random
import asyncio
import logging
from discord import app_commands
from utils.database import get_guess_stats, update_guess_stats, get_guess_number_leaderboard
import statistics
from collections import Counter

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
    @bot.tree.command(name="guess-num", description="Guess the number (1-100). You have 10 tries!")
    async def guess_number(interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)  # Defer to avoid timeout

            user = interaction.user
            guild_id = interaction.guild_id
            user_id = str(user.id)
            target_number = random.randint(1, 100)

            try:
                await user.send("🎮 Welcome to the Guess Number game! Guess a number between 1 and 100.")
                await interaction.followup.send("✅ The game has started in your DMs!", ephemeral=True)
            except discord.errors.Forbidden:
                await interaction.followup.send("❌ I can't DM you! Please enable DMs and try again.", ephemeral=True)
                return

            attempts_left = 10
            guesses = []
            guess_gaps = []

            def check(message):
                return message.author == user and message.guild is None and message.content.isdigit()

            while attempts_left > 0:
                try:
                    await user.send(f"⏳ You have {attempts_left} tries left. Type your guess!")
                    guess_message = await bot.wait_for('message', timeout=60.0, check=check)
                    guess = int(guess_message.content)
                    
                    if guess < 1 or guess > 100:
                        await user.send("❌ Please enter a number between 1 and 100!")
                        continue
                        
                    gap = abs(target_number - guess)
                    guesses.append(guess)
                    guess_gaps.append(gap)
                    attempts_left -= 1

                    if guess == target_number:
                        await user.send(f"🎉 Correct! You guessed the number {target_number}!")
                        try:
                            update_guess_stats(supabase, guild_id, user_id, "correct", guesses, guess_gaps)
                        except Exception as e:
                            logger.error(f"Failed to update guess stats: {str(e)}")
                            await user.send("⚠️ Could not update stats due to a database error.")
                        return
                    else:
                        hint = "higher" if guess < target_number else "lower"
                        await user.send(f"❌ Incorrect! The number is {hint} than {guess}!")
                except asyncio.TimeoutError:
                    await user.send("⏰ Time's up! You took too long to respond!")
                    break
                except ValueError:
                    await user.send("❌ Please enter a valid number!")
                    continue

            await user.send(f"Game over! The correct number was {target_number}.")
            try:
                update_guess_stats(supabase, guild_id, user_id, "incorrect", guesses, guess_gaps)
            except Exception as e:
                logger.error(f"Failed to update guess stats: {str(e)}")
                await user.send("⚠️ Could not update stats due to a database error.")
        except Exception as e:
            logger.error(f"Error in guess_number command: {str(e)}")
            await interaction.followup.send("❌ An error occurred while starting the game.", ephemeral=True)

    @bot.tree.command(name="guess-num-stats", description="Check your Guess Number stats or stats of another user")
    @app_commands.describe(member="Mention a user to check their stats (optional)")
    async def guess_number_stats(interaction: discord.Interaction, member: discord.Member = None):
        try:
            await interaction.response.defer(ephemeral=True)
            
            guild_id = interaction.guild_id
            if guild_id is None:
                await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
                return
                
            if member is None:
                user_id = str(interaction.user.id)
                user_name = interaction.user.display_name
            else:
                user_id = str(member.id)
                user_name = member.display_name

            try:
                user_data = get_guess_stats(supabase, guild_id, user_id)
            except Exception as e:
                logger.error(f"Failed to get guess stats: {str(e)}")
                await interaction.followup.send("⚠️ Could not retrieve stats due to a database error.", ephemeral=True)
                return

            if not user_data:
                await interaction.followup.send(f"{user_name} hasn't played the Guess Number game yet!", ephemeral=True)
                return

            # Get data with proper error handling for missing fields
            guesses_str = user_data.get("guesses", "[]")
            guess_gaps_str = user_data.get("guess_gaps", "[]")
            
            try:
                import json
                guesses = json.loads(guesses_str) if isinstance(guesses_str, str) else []
                guess_gaps = json.loads(guess_gaps_str) if isinstance(guess_gaps_str, str) else []
            except json.JSONDecodeError:
                guesses = []
                guess_gaps = []
                logger.error(f"Failed to parse JSON for guesses or gaps")

            if guesses and guess_gaps:
                try:
                    mean_gap = round(sum(guess_gaps) / len(guess_gaps), 2)
                    median_gap = round(sorted(guess_gaps)[len(guess_gaps) // 2], 2)
                    
                    # Safe mode calculation (most common value)
                    if guess_gaps:
                        counter = Counter(guess_gaps)
                        mode_gap = round(counter.most_common(1)[0][0], 2)
                    else:
                        mode_gap = 0
                    
                    await interaction.followup.send(
                        f"📊 **{user_name}'s Guess Number Stats**\n\n"
                        f"✅ Correct Guesses: {user_data.get('correct_guesses', 0)}\n"
                        f"❌ Incorrect Guesses: {user_data.get('incorrect_guesses', 0)}\n"
                        f"🎮 Total Games: {user_data.get('total_games', 0)}\n"
                        f"📅 Total Attempts: {len(guesses)}\n"
                        f"⏱️ Mean Guess Gap: {mean_gap}\n"
                        f"📏 Median Guess Gap: {median_gap}\n"
                        f"🛠 Mode Guess Gap: {mode_gap}"
                    )
                except Exception as e:
                    logger.error(f"Error calculating stats: {str(e)}")
                    await interaction.followup.send(
                        f"📊 **{user_name}'s Guess Number Stats**\n\n"
                        f"✅ Correct Guesses: {user_data.get('correct_guesses', 0)}\n"
                        f"❌ Incorrect Guesses: {user_data.get('incorrect_guesses', 0)}\n"
                        f"🎮 Total Games: {user_data.get('total_games', 0)}"
                    )
            else:
                await interaction.followup.send(
                    f"📊 **{user_name}'s Guess Number Stats**\n\n"
                    f"✅ Correct Guesses: {user_data.get('correct_guesses', 0)}\n"
                    f"❌ Incorrect Guesses: {user_data.get('incorrect_guesses', 0)}\n"
                    f"🎮 Total Games: {user_data.get('total_games', 0)}"
                )
        except Exception as e:
            logger.error(f"Error in guess_number_stats command: {str(e)}")
            await interaction.followup.send("❌ An error occurred while retrieving stats.", ephemeral=True)
            
    @bot.tree.command(name="guess-num-lb", description="Show Guess Number game leaderboard")
    async def guess_number_leaderboard(interaction: discord.Interaction):
        await interaction.response.defer()  # Defer but not ephemeral
        
        guild_id = interaction.guild_id
        if not guild_id:
            await interaction.followup.send("This command can only be used in a server.")
            return
            
        try:
            leaderboard_data = get_guess_number_leaderboard(supabase, guild_id, 10)
            
            if not leaderboard_data:
                await interaction.followup.send("No one has played the Guess Number game yet!")
                return
                
            # Create a nice-looking embed for the leaderboard
            embed = discord.Embed(
                title="🔢 Guess Number Leaderboard 🎮",
                description="Top 10 players ranked by success rate",
                color=0x3498db  # Blue color
            )
            
            # Add guild icon to the embed if available
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
                
            # Add server name
            embed.set_author(name=interaction.guild.name)
            
            # Add footer with timestamp
            embed.set_footer(text=f"Requested by {interaction.user.name}", 
                           icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.timestamp = discord.utils.utcnow()
            
            # Format the leaderboard
            leaderboard_text = ""
            
            for i, player_data in enumerate(leaderboard_data, 1):
                # Get user info if possible
                user_id = int(player_data.get("user_id", "0"))
                display_name = await resolve_member_name(interaction.guild, user_id)
                
                # Calculate success rate
                correct = player_data.get("correct_guesses", 0)
                incorrect = player_data.get("incorrect_guesses", 0)
                total = player_data.get("total_games", 0)
                success_rate = (correct / total * 100) if total > 0 else 0
                
                # Format medal for top 3
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`#{i}`"
                
                # Add player to the leaderboard text with better formatting
                leaderboard_text += f"**{medal} {display_name}**\n"
                leaderboard_text += f"┣ Success Rate: **{success_rate:.1f}%**\n"
                leaderboard_text += f"┣ Correct: **{correct}** ┃ Incorrect: **{incorrect}**\n"
                leaderboard_text += f"┗ Total Games: **{total}**\n\n"
            
            # Add the formatted text to the embed
            embed.description = f"Top 10 players ranked by success rate\n\n{leaderboard_text}"
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to get Guess Number leaderboard: {str(e)}")
            await interaction.followup.send("⚠️ Could not retrieve the leaderboard due to an error.")

