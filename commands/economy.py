import discord
from discord import app_commands
import logging
from utils.database import get_user_balance, update_user_balance, get_economy_leaderboard, can_claim_reward, claim_reward

logger = logging.getLogger(__name__)

# HXC Emoji - Replace with your actual emoji ID from Discord Developer Portal
HXC_EMOJI = "<:hxc:1408428556308189378>"  # Replace YOUR_EMOJI_ID_HERE with actual ID

def setup(bot, supabase):
    @bot.tree.command(name="balance", description="Check your HXC (HexxaCoin) balance")
    @app_commands.describe(user="User to check balance for (optional)")
    async def balance(interaction: discord.Interaction, user: discord.Member = None):
        """Check HXC balance for yourself or another user."""
        try:
            target_user = user if user else interaction.user
            user_data = get_user_balance(supabase, str(target_user.id))
            
            if not user_data:
                await interaction.response.send_message("❌ Error retrieving balance data.", ephemeral=True)
                return
            
            # Create beautiful embed with dynamic colors
            balance = user_data["balance"]
            if balance >= 10000:
                color = 0xffd700  # Gold for rich users
            elif balance >= 1000:
                color = 0x00ff00  # Green for good balance
            elif balance >= 0:
                color = 0xff9900  # Orange for low balance
            else:
                color = 0xff0000  # Red for debt
                
            embed = discord.Embed(
                title="💰 HexxaCoin Balance",
                description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
                color=color
            )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            # Balance display with debt indicator
            balance_text = f"**{user_data['balance']:,}** {HXC_EMOJI}"
            if balance < 0:
                balance_text = f"🚨 **DEBT: {abs(balance):,}** {HXC_EMOJI} 🚨"
                
            embed.add_field(
                name="🪙 Current Balance", 
                value=f"\n{balance_text}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", 
                inline=False
            )
            embed.add_field(
                name="📈 Total Earned", 
                value=f"\n💎 **{user_data['total_earned']:,}** {HXC_EMOJI}\n", 
                inline=True
            )
            embed.add_field(
                name="📉 Total Spent", 
                value=f"\n💸 **{user_data['total_spent']:,}** {HXC_EMOJI}\n", 
                inline=True
            )
            
            # Add net profit/loss
            net = user_data['total_earned'] - user_data['total_spent']
            embed.add_field(
                name="💹 Net Profit/Loss",
                value=f"\n{'🚀' if net > 0 else '📉' if net < 0 else '📊'} **{net:,}** {HXC_EMOJI}\n",
                inline=True
            )
            
            embed.set_footer(text=f"Requested by {interaction.user.display_name}")
            
            # Add user info to description
            status_emoji = "👑" if balance >= 10000 else "💰" if balance >= 1000 else "⚠️" if balance >= 0 else "💀"
            if user:
                embed.description = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{status_emoji} Balance for {target_user.mention}\n"
            else:
                embed.description = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{status_emoji} Your current balance\n"
                
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in balance command: {str(e)}")
            await interaction.response.send_message("❌ An error occurred while retrieving balance.", ephemeral=True)

    @bot.tree.command(name="leaderboard", description="View the HXC leaderboard")
    @app_commands.describe(limit="Number of users to show (1-25, default: 10)")
    async def leaderboard(interaction: discord.Interaction, limit: int = 10):
        """Show the economy leaderboard."""
        try:
            # Validate limit
            if limit < 1 or limit > 25:
                await interaction.response.send_message("❌ Limit must be between 1 and 25.", ephemeral=True)
                return
                
            leaderboard_data = get_economy_leaderboard(supabase, limit)
            
            if not leaderboard_data:
                await interaction.response.send_message("❌ No economy data found.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🏆 HexxaCoin Leaderboard",
                description="Top users by HXC balance",
                color=0xffd700
            )
            
            leaderboard_text = ""
            medals = ["🥇", "🥈", "🥉"]
            
            for i, user_data in enumerate(leaderboard_data):
                try:
                    user = bot.get_user(int(user_data["user_id"]))
                    username = user.display_name if user else f"User {user_data['user_id'][:8]}..."
                    
                    medal = medals[i] if i < 3 else f"**{i+1}.**"
                    balance = user_data["balance"]
                    
                    leaderboard_text += f"{medal} {username} - **{balance:,}** {HXC_EMOJI}\n"
                    
                except Exception as e:
                    logger.error(f"Error processing user {user_data['user_id']}: {str(e)}")
                    continue
            
            embed.description = leaderboard_text if leaderboard_text else "No users found."
            embed.set_footer(text=f"Requested by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in leaderboard command: {str(e)}")
            await interaction.response.send_message("❌ An error occurred while retrieving the leaderboard.", ephemeral=True)

    @bot.tree.command(name="daily", description="Claim your daily HXC reward from SES!")
    async def daily(interaction: discord.Interaction):
        """Claim daily HXC reward."""
        try:
            user_id = str(interaction.user.id)
            
            # Check if user can claim
            can_claim, time_left, current_streak = can_claim_reward(supabase, user_id, "daily")
            
            if not can_claim:
                embed = discord.Embed(
                    title="🏛️ Social Economical Service (SES)",
                    description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⏰ **DAILY REWARD COOLDOWN** ⏰\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=0xff6b6b
                )
                embed.add_field(
                    name="⏳ Time Remaining",
                    value=f"**{time_left}**",
                    inline=True
                )
                embed.add_field(
                    name="🔥 Current Streak",
                    value=f"**{current_streak}** days",
                    inline=True
                )
                embed.set_footer(text="Come back when the cooldown expires!")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Claim the reward
            success, reward_amount, new_streak = claim_reward(supabase, user_id, "daily")
            
            if success:
                embed = discord.Embed(
                    title="🏛️ Social Economical Service (SES)",
                    description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎉 **DAILY REWARD CLAIMED** 🎉\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=0x4ecdc4
                )
                embed.add_field(
                    name="💰 Reward Received",
                    value=f"**+{reward_amount:,}** {HXC_EMOJI}",
                    inline=True
                )
                embed.add_field(
                    name="🔥 Daily Streak",
                    value=f"**{new_streak}** days",
                    inline=True
                )
                
                # Calculate streak bonus percentage
                streak_bonus = min((new_streak - 1) * 10, 100)
                if streak_bonus > 0:
                    embed.add_field(
                        name="⚡ Streak Bonus",
                        value=f"**+{streak_bonus}%** bonus applied!",
                        inline=True
                    )
                
                embed.add_field(
                    name="📅 Next Claim",
                    value="Available in **24 hours**",
                    inline=False
                )
                embed.set_footer(text="Keep your streak alive by claiming daily!")
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("❌ Failed to claim daily reward. Please try again.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in daily command: {str(e)}")
            await interaction.response.send_message("❌ An error occurred while claiming your daily reward.", ephemeral=True)

    @bot.tree.command(name="monthly", description="Claim your monthly HXC reward from SES!")
    async def monthly(interaction: discord.Interaction):
        """Claim monthly HXC reward."""
        try:
            user_id = str(interaction.user.id)
            
            # Check if user can claim
            can_claim, time_left, current_streak = can_claim_reward(supabase, user_id, "monthly")
            
            if not can_claim:
                embed = discord.Embed(
                    title="🏛️ Social Economical Service (SES)",
                    description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⏰ **MONTHLY REWARD COOLDOWN** ⏰\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=0xff6b6b
                )
                embed.add_field(
                    name="⏳ Time Remaining",
                    value=f"**{time_left}**",
                    inline=True
                )
                embed.add_field(
                    name="🔥 Current Streak",
                    value=f"**{current_streak}** months",
                    inline=True
                )
                embed.set_footer(text="Come back when the cooldown expires!")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Claim the reward
            success, reward_amount, new_streak = claim_reward(supabase, user_id, "monthly")
            
            if success:
                embed = discord.Embed(
                    title="🏛️ Social Economical Service (SES)",
                    description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎊 **MONTHLY REWARD CLAIMED** 🎊\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=0x9b59b6
                )
                embed.add_field(
                    name="💎 Reward Received",
                    value=f"**+{reward_amount:,}** {HXC_EMOJI}",
                    inline=True
                )
                embed.add_field(
                    name="🔥 Monthly Streak",
                    value=f"**{new_streak}** months",
                    inline=True
                )
                
                # Calculate streak bonus percentage
                streak_bonus = min((new_streak - 1) * 10, 100)
                if streak_bonus > 0:
                    embed.add_field(
                        name="⚡ Streak Bonus",
                        value=f"**+{streak_bonus}%** bonus applied!",
                        inline=True
                    )
                
                embed.add_field(
                    name="📅 Next Claim",
                    value="Available in **30 days**",
                    inline=False
                )
                embed.set_footer(text="Monthly rewards are substantial - don't miss them!")
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("❌ Failed to claim monthly reward. Please try again.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in monthly command: {str(e)}")
            await interaction.response.send_message("❌ An error occurred while claiming your monthly reward.", ephemeral=True)

    @bot.tree.command(name="yearly", description="Claim your yearly HXC reward from SES!")
    async def yearly(interaction: discord.Interaction):
        """Claim yearly HXC reward."""
        try:
            user_id = str(interaction.user.id)
            
            # Check if user can claim
            can_claim, time_left, current_streak = can_claim_reward(supabase, user_id, "yearly")
            
            if not can_claim:
                embed = discord.Embed(
                    title="🏛️ Social Economical Service (SES)",
                    description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⏰ **YEARLY REWARD COOLDOWN** ⏰\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=0xff6b6b
                )
                embed.add_field(
                    name="⏳ Time Remaining",
                    value=f"**{time_left}**",
                    inline=True
                )
                embed.add_field(
                    name="🔥 Current Streak",
                    value=f"**{current_streak}** years",
                    inline=True
                )
                embed.set_footer(text="Come back when the cooldown expires!")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Claim the reward
            success, reward_amount, new_streak = claim_reward(supabase, user_id, "yearly")
            
            if success:
                embed = discord.Embed(
                    title="🏛️ Social Economical Service (SES)",
                    description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🏆 **YEARLY REWARD CLAIMED** 🏆\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=0xf39c12
                )
                embed.add_field(
                    name="💰 Massive Reward",
                    value=f"**+{reward_amount:,}** {HXC_EMOJI}",
                    inline=True
                )
                embed.add_field(
                    name="🔥 Yearly Streak",
                    value=f"**{new_streak}** years",
                    inline=True
                )
                
                # Calculate streak bonus percentage
                streak_bonus = min((new_streak - 1) * 10, 100)
                if streak_bonus > 0:
                    embed.add_field(
                        name="⚡ Streak Bonus",
                        value=f"**+{streak_bonus}%** bonus applied!",
                        inline=True
                    )
                
                embed.add_field(
                    name="📅 Next Claim",
                    value="Available in **365 days**",
                    inline=False
                )
                embed.set_footer(text="🎉 Congratulations on your yearly commitment!")
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("❌ Failed to claim yearly reward. Please try again.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in yearly command: {str(e)}")
            await interaction.response.send_message("❌ An error occurred while claiming your yearly reward.", ephemeral=True)