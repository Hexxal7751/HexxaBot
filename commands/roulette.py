import discord
from discord import app_commands
import random
import logging
from utils.database import get_user_balance, update_user_balance, get_roulette_stats, update_roulette_stats, get_roulette_leaderboard

logger = logging.getLogger(__name__)

# HXC Emoji - Replace with your actual emoji ID from Discord Developer Portal
# Format: <:emoji_name:emoji_id>
HXC_EMOJI = "<:hxc:1408428556308189378>"
def setup(bot, supabase):
    @bot.tree.command(name="roulette", description="Play roulette and bet your HXC!")
    @app_commands.describe(
        bet="Amount of HXC to bet (or 'all' for entire balance, 'max' for 10,000)",
        choice="Choose red, black, or a number (1-24). Number 24 can be typed manually"
    )
    @app_commands.choices(choice=[
        app_commands.Choice(name="Red", value="red"),
        app_commands.Choice(name="Black", value="black"),
        app_commands.Choice(name="1", value="1"),
        app_commands.Choice(name="2", value="2"),
        app_commands.Choice(name="3", value="3"),
        app_commands.Choice(name="4", value="4"),
        app_commands.Choice(name="5", value="5"),
        app_commands.Choice(name="6", value="6"),
        app_commands.Choice(name="7", value="7"),
        app_commands.Choice(name="8", value="8"),
        app_commands.Choice(name="9", value="9"),
        app_commands.Choice(name="10", value="10"),
        app_commands.Choice(name="11", value="11"),
        app_commands.Choice(name="12", value="12"),
        app_commands.Choice(name="13", value="13"),
        app_commands.Choice(name="14", value="14"),
        app_commands.Choice(name="15", value="15"),
        app_commands.Choice(name="16", value="16"),
        app_commands.Choice(name="17", value="17"),
        app_commands.Choice(name="18", value="18"),
        app_commands.Choice(name="19", value="19"),
        app_commands.Choice(name="20", value="20"),
        app_commands.Choice(name="21", value="21"),
        app_commands.Choice(name="22", value="22"),
        app_commands.Choice(name="23", value="23")
    ])
    async def roulette(interaction: discord.Interaction, bet: str, choice: str):
        """Play roulette with HXC betting."""
        try:
            # Get user balance first for 'all' and 'max' options
            user_data = get_user_balance(supabase, str(interaction.user.id))
            if not user_data:
                await interaction.response.send_message("❌ Error retrieving balance data!", ephemeral=True)
                return
            
            # Handle special bet amounts
            original_bet = bet
            if str(bet).lower() == "all":
                bet = user_data["balance"]
            elif str(bet).lower() == "max":
                bet = 10000
            else:
                try:
                    bet = int(bet)
                except ValueError:
                    await interaction.response.send_message("❌ Invalid bet amount! Use a number, 'all', or 'max'.", ephemeral=True)
                    return
            
            # Validate bet amount
            if bet <= 0:
                await interaction.response.send_message("❌ Bet amount must be positive!", ephemeral=True)
                return
            
            # Only apply 10k limit if not using 'all' option
            if original_bet != "all" and bet > 10000:
                await interaction.response.send_message(f"❌ Maximum bet is 10,000 {HXC_EMOJI}! Use 'all' to bet your entire balance.", ephemeral=True)
                return
            
            # Balance validation (already retrieved above)
                
            # Prevent zero/negative balance players from playing
            if user_data["balance"] <= 0:
                broke_messages = [
                    f"💸 You need a positive balance to play roulette! Current balance: **{user_data['balance']:,}** {HXC_EMOJI}",
                    f"🚫 Can't gamble with zero or negative balance. Get some {HXC_EMOJI} first! Balance: **{user_data['balance']:,}** {HXC_EMOJI}",
                    f"💰 You're in debt! Come back when you have some {HXC_EMOJI} to bet. Balance: **{user_data['balance']:,}** {HXC_EMOJI}",
                    f"⚠️ Insufficient funds for gambling. You need positive {HXC_EMOJI} to play! Balance: **{user_data['balance']:,}** {HXC_EMOJI}"
                ]
                await interaction.response.send_message(random.choice(broke_messages), ephemeral=True)
                return
                
            # Prevent betting more than current balance
            if bet > user_data["balance"]:
                await interaction.response.send_message(
                    f"❌ You can't bet more than you have! Your balance: **{user_data['balance']:,}** {HXC_EMOJI} | Bet amount: **{bet:,}** {HXC_EMOJI}", 
                    ephemeral=True
                )
                return
            
            # Validate choice
            choice = choice.lower().strip()
            valid_colors = ["red", "black"]
            valid_numbers = [str(i) for i in range(1, 24)]  # 1-23
            
            if choice not in valid_colors and choice not in valid_numbers:
                await interaction.response.send_message(
                    "❌ Invalid choice! Choose 'red', 'black', or a number (1-23).", 
                    ephemeral=True
                )
                return
            
            # Deduct bet from balance
            if not update_user_balance(supabase, str(interaction.user.id), bet, "subtract"):
                await interaction.response.send_message("❌ Failed to process bet!", ephemeral=True)
                return
            
            # Spin the roulette wheel
            winning_number = random.randint(1, 24)
            
            # Define red and black numbers (1-24 only)
            red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23]
            black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22]
            
            # Determine winning color
            if winning_number in red_numbers:
                winning_color = "red"
            else:
                winning_color = "black"
            
            # Calculate winnings
            won = False
            winnings = 0
            
            if choice.isdigit():
                # Number bet (35:1 payout)
                if int(choice) == winning_number:
                    won = True
                    winnings = bet * 36  # 35:1 + original bet
            else:
                # Color bet (1:1 payout, but user wins twice the bet as requested)
                if choice == winning_color:
                    won = True
                    winnings = bet * 2  # User wins twice the betted amount
                else:
                    # Red/black losses are 1.5x the bet amount
                    additional_loss = int(bet * 0.5)
                    update_user_balance(supabase, str(interaction.user.id), additional_loss, "subtract")
            
            # Create beautiful result embed with dynamic styling
            embed = discord.Embed(
                title="🎰 Roulette Casino",
                description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎲 **SPIN RESULTS** 🎲\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
                color=0x00ff00 if won else 0xff0000
            )
            
            # Add wheel emoji based on winning color
            wheel_emoji = "🔴" if winning_color == "red" else "⚫"
            
            embed.add_field(
                name="🎯 Winning Number",
                value=f"\n🎡 {wheel_emoji} **{winning_number}** 🎡\n🏷️ **{winning_color.upper()}**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
                inline=False
            )
            
            embed.add_field(
                name="💰 Your Wager",
                value=f"\n🎯 **{bet:,}** {HXC_EMOJI}\n🎲 **{choice.upper()}**\n",
                inline=True
            )
            
            if won:
                embed.add_field(
                    name="🎉 JACKPOT!",
                    value=f"\n🎊 **+{winnings:,}** {HXC_EMOJI} 🎊\n💎 **WINNER!** 💎\n",
                    inline=True
                )
                # Add winnings to balance
                update_user_balance(supabase, str(interaction.user.id), winnings, "add")
                # Update stats (guild-specific)
                update_roulette_stats(supabase, str(interaction.guild.id), str(interaction.user.id), "win", bet, winnings)
            else:
                # Calculate total loss for red/black bets (1.5x)
                if choice in ['red', 'black']:
                    total_loss = int(bet * 1.5)
                    embed.add_field(
                        name="💸 BUST!",
                        value=f"\n💀 **-{total_loss:,}** {HXC_EMOJI} 💀\n⚡ **1.5x LOSS PENALTY** ⚡\n",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="💸 BUST!",
                        value=f"\n💀 **-{bet:,}** {HXC_EMOJI} 💀\n🎯 **BETTER LUCK NEXT TIME** 🎯\n",
                        inline=True
                    )
                # Update stats (guild-specific)
                update_roulette_stats(supabase, str(interaction.guild.id), str(interaction.user.id), "loss", bet, 0)
            
            # Removed new balance display as requested
            
            embed.set_footer(text=f"🎰 Played by {interaction.user.display_name} | HexxaBot Casino 🎰")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in roulette command: {str(e)}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ An error occurred while playing roulette.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ An error occurred while playing roulette.", ephemeral=True)
            except:
                pass  # Ignore if we can't send error message

    @bot.tree.command(name="roulette-stats", description="View your roulette statistics")
    @app_commands.describe(user="User to check stats for (optional)")
    async def roulette_stats(interaction: discord.Interaction, user: discord.Member = None):
        """View roulette statistics for yourself or another user."""
        try:
            target_user = user if user else interaction.user
            stats = get_roulette_stats(supabase, str(interaction.guild.id), str(target_user.id))
            
            if not stats:
                message = f"{target_user.mention} hasn't played roulette yet!" if user else "You haven't played roulette yet!"
                await interaction.response.send_message(message, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🎰 Roulette Statistics",
                color=0x9932cc
            )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            # Calculate win rate
            win_rate = (stats["games_won"] / stats["games_played"] * 100) if stats["games_played"] > 0 else 0
            
            embed.add_field(
                name="🎮 Games Played",
                value=f"**{stats['games_played']:,}**",
                inline=True
            )
            embed.add_field(
                name="🏆 Games Won",
                value=f"**{stats['games_won']:,}**",
                inline=True
            )
            embed.add_field(
                name="📊 Win Rate",
                value=f"**{win_rate:.1f}%**",
                inline=True
            )
            embed.add_field(
                name="💰 Total Bet",
                value=f"**{stats['total_bet']:,}** {HXC_EMOJI}",
                inline=True
            )
            embed.add_field(
                name="🎉 Total Won",
                value=f"**{stats['total_won']:,}** {HXC_EMOJI}",
                inline=True
            )
            embed.add_field(
                name="💸 Total Lost",
                value=f"**{stats['total_lost']:,}** {HXC_EMOJI}",
                inline=True
            )
            embed.add_field(
                name="🔥 Biggest Win",
                value=f"**{stats['biggest_win']:,}** {HXC_EMOJI}",
                inline=True
            )
            embed.add_field(
                name="💔 Biggest Loss",
                value=f"**{stats['biggest_loss']:,}** {HXC_EMOJI}",
                inline=True
            )
            
            # Net profit/loss
            net = stats['total_won'] - stats['total_lost']
            embed.add_field(
                name="💹 Net Profit/Loss",
                value=f"{'📈' if net >= 0 else '📉'} **{net:,}** {HXC_EMOJI}",
                inline=True
            )
            
            if user:
                embed.description = f"Roulette stats for {target_user.mention} in this server"
            else:
                embed.description = "Your roulette statistics in this server"
                
            embed.set_footer(text=f"Requested by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in roulette-stats command: {str(e)}")
            await interaction.response.send_message("❌ An error occurred while retrieving stats.", ephemeral=True)

    @bot.tree.command(name="roulette-leaderboard", description="View the roulette leaderboard for this server")
    @app_commands.describe(limit="Number of users to show (1-25, default: 10)")
    async def roulette_leaderboard(interaction: discord.Interaction, limit: int = 10):
        """Show the roulette leaderboard for this server."""
        try:
            # Validate limit
            if limit < 1 or limit > 25:
                await interaction.response.send_message("❌ Limit must be between 1 and 25.", ephemeral=True)
                return
                
            leaderboard_data = get_roulette_leaderboard(supabase, str(interaction.guild.id), limit)
            
            if not leaderboard_data:
                await interaction.response.send_message("❌ No roulette data found for this server.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🎰 Roulette Leaderboard",
                description="Top players by total winnings in this server",
                color=0xffd700
            )
            
            leaderboard_text = ""
            medals = ["🥇", "🥈", "🥉"]
            
            for i, user_data in enumerate(leaderboard_data):
                try:
                    user = bot.get_user(int(user_data["user_id"]))
                    username = user.display_name if user else f"User {user_data['user_id'][:8]}..."
                    
                    medal = medals[i] if i < 3 else f"**{i+1}.**"
                    total_won = user_data["total_won"]
                    
                    leaderboard_text += f"{medal} {username} - **{total_won:,}** {HXC_EMOJI} won\n"
                    
                except Exception as e:
                    logger.error(f"Error processing user {user_data['user_id']}: {str(e)}")
                    continue
            
            embed.description = leaderboard_text if leaderboard_text else "No players found."
            embed.set_footer(text=f"Requested by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in roulette-leaderboard command: {str(e)}")
            await interaction.response.send_message("❌ An error occurred while retrieving the leaderboard.", ephemeral=True)
