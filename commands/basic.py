import discord
import logging
from discord import app_commands
from datetime import datetime
import platform
import time
import random
import re
import asyncio

logger = logging.getLogger(__name__)

def setup(bot):
    @bot.tree.command(name="ping", description="Check your current ping!")
    async def ping(interaction: discord.Interaction):
        try:
            latency = round(bot.latency * 1000)
            await interaction.response.send_message(f"🏓 Pong! Your ping is **{latency}ms**.")
        except Exception as e:
            logger.error(f"Error in ping command: {str(e)}")
            await interaction.response.send_message("❌ An error occurred while checking the ping.", ephemeral=True)

    @bot.tree.command(name="hey", description="Say hi to the bot!")
    async def hey(interaction: discord.Interaction):
        try:
            await interaction.response.send_message(f"Hey {interaction.user.mention}! 👋")
        except Exception as e:
            logger.error(f"Error in hey command: {str(e)}")
            await interaction.response.send_message("❌ An error occurred while sending the greeting.", ephemeral=True)

    @bot.tree.command(name="math", description="Perform basic arithmetic operations.")
    @app_commands.describe(operation="Choose an operation", a="First number", b="Second number")
    @app_commands.choices(
        operation=[
            app_commands.Choice(name="Add", value="add"),
            app_commands.Choice(name="Subtract", value="subtract"),
            app_commands.Choice(name="Multiply", value="multiply"),
            app_commands.Choice(name="Divide", value="divide"),
        ]
    )
    async def math(interaction: discord.Interaction, operation: app_commands.Choice[str], a: int, b: int):
        try:
            await interaction.response.defer(ephemeral=True)  # Defer to avoid timeout

            if operation.value == "divide" and b == 0:
                await interaction.followup.send("❌ Division by zero is not allowed!", ephemeral=True)
                return

            result = {
                "add": a + b,
                "subtract": a - b,
                "multiply": a * b,
                "divide": a / b
            }[operation.value]

            await interaction.followup.send(f"🔢 The answer is: **{result}**", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in math command: {str(e)}")
            await interaction.followup.send("❌ An error occurred while performing the calculation.", ephemeral=True)

    @bot.tree.command(name="serverinfo", description="Display detailed information about the server")
    async def serverinfo(interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)  # Make response ephemeral
            
            guild = interaction.guild
            
            # Get member counts with more detailed stats
            total_members = guild.member_count
            bot_count = len([m for m in guild.members if m.bot])
            human_count = total_members - bot_count
            online_members = len([m for m in guild.members if m.status != discord.Status.offline])
            offline_members = total_members - online_members
            
            # Get channel counts with more details
            text_channels = len(guild.text_channels)
            voice_channels = len(guild.voice_channels)
            categories = len(guild.categories)
            # Count news channels by checking channel type
            news_channels = len([c for c in guild.text_channels if isinstance(c, discord.TextChannel) and c.is_news()])
            # Count forum channels by checking channel type
            forum_channels = len([c for c in guild.channels if isinstance(c, discord.ForumChannel)])
            
            # Get role count and highest role
            role_count = len(guild.roles)
            highest_role = guild.roles[-1] if guild.roles else None
            
            # Get boost level and count
            boost_level = guild.premium_tier
            boost_count = guild.premium_subscription_count
            
            # Get verification level
            verification_levels = {
                discord.VerificationLevel.none: "None",
                discord.VerificationLevel.low: "Low",
                discord.VerificationLevel.medium: "Medium",
                discord.VerificationLevel.high: "High",
                discord.VerificationLevel.highest: "Highest"
            }
            verification_level = verification_levels.get(guild.verification_level, "Unknown")
            
            # Get content filter level
            content_filter_levels = {
                discord.ContentFilter.disabled: "Disabled",
                discord.ContentFilter.no_role: "No Role",
                discord.ContentFilter.all_members: "All Members"
            }
            content_filter = content_filter_levels.get(guild.explicit_content_filter, "Unknown")
            
            # Get server features
            features = [f.replace('_', ' ').title() for f in guild.features]
            
            # Create embed
            embed = discord.Embed(
                title=f"📊 Server Information: {guild.name}",
                color=discord.Color.blue()
            )
            
            # Add server icon and banner if available
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            if guild.banner:
                embed.set_image(url=guild.banner.url)
            
            # Add fields
            embed.add_field(
                name="👥 Members",
                value=f"Total: **{total_members:,}**\n"
                      f"Humans: **{human_count:,}**\n"
                      f"Bots: **{bot_count:,}**\n"
                      f"Online: **{online_members:,}**\n"
                      f"Offline: **{offline_members:,}**",
                inline=True
            )
            
            embed.add_field(
                name="📝 Channels",
                value=f"Text: **{text_channels}**\n"
                      f"Voice: **{voice_channels}**\n"
                      f"Categories: **{categories}**\n"
                      f"News: **{news_channels}**\n"
                      f"Forums: **{forum_channels}**",
                inline=True
            )
            
            embed.add_field(
                name="🎭 Roles",
                value=f"Total: **{role_count}**\n"
                      f"Highest: {highest_role.mention if highest_role else 'None'}",
                inline=True
            )
            
            embed.add_field(
                name="🚀 Server Boost",
                value=f"Level: **{boost_level}**\n"
                      f"Boosts: **{boost_count}**",
                inline=True
            )
            
            embed.add_field(
                name="⚙️ Server Settings",
                value=f"Verification: **{verification_level}**\n"
                      f"Content Filter: **{content_filter}**",
                inline=True
            )
            
            embed.add_field(
                name="📅 Created On",
                value=f"<t:{int(guild.created_at.timestamp())}:F>\n"
                      f"(<t:{int(guild.created_at.timestamp())}:R>)",
                inline=True
            )
            
            embed.add_field(
                name="👑 Owner",
                value=f"{guild.owner.mention}",
                inline=True
            )
            
            if features:
                embed.add_field(
                    name="✨ Server Features",
                    value=", ".join(features),
                    inline=False
                )
            
            # Add footer with server ID
            embed.set_footer(text=f"Server ID: {guild.id}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in serverinfo command: {str(e)}")
            await interaction.followup.send("❌ An error occurred while fetching server information.", ephemeral=True)

    @bot.tree.command(name="userinfo", description="Display detailed information about a user")
    @app_commands.describe(member="The user to get information about (defaults to you)")
    async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
        try:
            await interaction.response.defer(ephemeral=True)  # Make response ephemeral
            
            # If no member is specified, use the command user
            member = member or interaction.user
            
            # Get user roles (excluding @everyone)
            roles = [role.mention for role in member.roles if role.name != "@everyone"]
            roles.reverse()  # Reverse to show highest role first
            
            # Get user's key permissions
            key_permissions = []
            if member.guild_permissions.administrator:
                key_permissions.append("👑 Administrator")
            if member.guild_permissions.manage_guild:
                key_permissions.append("⚙️ Manage Server")
            if member.guild_permissions.manage_messages:
                key_permissions.append("📝 Manage Messages")
            if member.guild_permissions.manage_roles:
                key_permissions.append("🎭 Manage Roles")
            if member.guild_permissions.ban_members:
                key_permissions.append("🔨 Ban Members")
            if member.guild_permissions.kick_members:
                key_permissions.append("👢 Kick Members")
            if member.guild_permissions.manage_channels:
                key_permissions.append("📊 Manage Channels")
            if member.guild_permissions.manage_emojis:
                key_permissions.append("😀 Manage Emojis")
            if member.guild_permissions.manage_webhooks:
                key_permissions.append("🔗 Manage Webhooks")
            if member.guild_permissions.mention_everyone:
                key_permissions.append("📢 Mention Everyone")
            if member.guild_permissions.mute_members:
                key_permissions.append("🔇 Mute Members")
            if member.guild_permissions.deafen_members:
                key_permissions.append("🔈 Deafen Members")
            if member.guild_permissions.move_members:
                key_permissions.append("↔️ Move Members")
            
            # Get user's status and activity
            status = str(member.status).title()
            activities = []
            for activity in member.activities:
                if isinstance(activity, discord.Game):
                    activities.append(f"🎮 Playing {activity.name}")
                elif isinstance(activity, discord.Streaming):
                    activities.append(f"📺 Streaming {activity.name}")
                elif isinstance(activity, discord.Activity):
                    if activity.type == discord.ActivityType.listening:
                        activities.append(f"🎵 Listening to {activity.name}")
                    elif activity.type == discord.ActivityType.watching:
                        activities.append(f"👀 Watching {activity.name}")
                    elif activity.type == discord.ActivityType.competing:
                        activities.append(f"🏆 Competing in {activity.name}")
                    else:
                        activities.append(f"🎯 {activity.name}")
            
            # Get user's platform
            platform_info = []
            if member.is_on_mobile():
                platform_info.append("📱 Mobile")
            if member.desktop_status != discord.Status.offline:
                platform_info.append("💻 Desktop")
            if member.web_status != discord.Status.offline:
                platform_info.append("🌐 Web")
            
            # Create embed
            embed = discord.Embed(
                title=f"👤 User Information: {member.display_name}",
                color=member.color
            )
            
            # Add user avatar and banner if available
            embed.set_thumbnail(url=member.display_avatar.url)
            if member.banner:
                embed.set_image(url=member.banner.url)
            
            # Add fields
            embed.add_field(
                name="📝 Username",
                value=f"Name: **{member.name}**\n"
                      f"Nickname: **{member.nick or 'None'}**\n"
                      f"ID: **{member.id}**\n"
                      f"Bot: **{'Yes' if member.bot else 'No'}**",
                inline=False
            )
            
            embed.add_field(
                name="📅 Account Created",
                value=f"<t:{int(member.created_at.timestamp())}:F>\n"
                      f"(<t:{int(member.created_at.timestamp())}:R>)",
                inline=True
            )
            
            embed.add_field(
                name="📥 Joined Server",
                value=f"<t:{int(member.joined_at.timestamp())}:F>\n"
                      f"(<t:{int(member.joined_at.timestamp())}:R>)",
                inline=True
            )
            
            if platform_info:
                embed.add_field(
                    name="💻 Platform",
                    value="\n".join(platform_info),
                    inline=True
                )
            
            if status != "Offline":
                embed.add_field(
                    name="🟢 Status",
                    value=f"**{status}**",
                    inline=True
                )
            
            if activities:
                embed.add_field(
                    name="🎯 Activities",
                    value="\n".join(activities),
                    inline=False
                )
            
            if key_permissions:
                embed.add_field(
                    name="🔑 Key Permissions",
                    value="\n".join(key_permissions),
                    inline=False
                )
            
            if roles:
                # Split roles into chunks if there are too many
                roles_text = " ".join(roles)
                if len(roles_text) > 1024:
                    roles_text = " ".join(roles[:10]) + f"\n... and {len(roles) - 10} more roles"
                embed.add_field(
                    name=f"🎭 Roles [{len(roles)}]",
                    value=roles_text,
                    inline=False
                )
            
            # Add footer
            embed.set_footer(text=f"Requested by {interaction.user.name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)  # Make followup ephemeral
            
        except Exception as e:
            logger.error(f"Error in userinfo command: {str(e)}")
            await interaction.followup.send("❌ An error occurred while fetching user information.", ephemeral=True)

    @bot.tree.command(name="diceroll", description="Roll dice with elegant formatting")
    @app_commands.describe(
        dice="Number of dice to roll (e.g., '2d20' for two 20-sided dice)",
        modifier="Optional modifier to add/subtract (e.g., '+5' or '-3')"
    )
    async def diceroll(interaction: discord.Interaction, dice: str, modifier: str = None):
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Parse the dice notation
            match = re.match(r'(\d+)d(\d+)', dice.lower())
            if not match:
                await interaction.followup.send("❌ Invalid dice notation. Please use format like '2d20' (2 twenty-sided dice).", ephemeral=True)
                return
                
            num_dice = int(match.group(1))
            sides = int(match.group(2))
            
            # Validate input
            if num_dice > 100:
                await interaction.followup.send("❌ Maximum 100 dice can be rolled at once.", ephemeral=True)
                return
            if sides > 100:
                await interaction.followup.send("❌ Maximum 100 sides per die.", ephemeral=True)
                return
                
            # Parse modifier if provided
            mod_value = 0
            if modifier:
                mod_match = re.match(r'([+-]?\d+)', modifier)
                if mod_match:
                    mod_value = int(mod_match.group(1))
            
            # Create initial embed for animation
            embed = discord.Embed(
                title="🎲 Rolling Dice...",
                description="The dice are tumbling...",
                color=discord.Color.blue()
            )
            
            # Send initial message
            message = await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Animate the roll
            for _ in range(2):  # Faster animation
                temp_rolls = [random.randint(1, sides) for _ in range(num_dice)]
                temp_total = sum(temp_rolls) + mod_value
                
                embed.description = f"Rolling...\nCurrent total: **{temp_total}**"
                await message.edit(embed=embed)
                await asyncio.sleep(0.1) # Faster animation
            
            # Final roll
            rolls = [random.randint(1, sides) for _ in range(num_dice)]
            total = sum(rolls) + mod_value
            
            # Create final embed
            final_embed = discord.Embed(
                title="🎲 Dice Roll Result",
                color=discord.Color.blue()
            )
            
            # Add fields with elegant formatting
            final_embed.add_field(
                name="🎯 Roll Details",
                value=f"**Dice:** {num_dice}d{sides}\n"
                      f"**Modifier:** {mod_value:+d}\n"
                      f"**Total:** {total}",
                inline=False
            )
            
            # Format individual rolls
            if num_dice <= 10:  # Only show individual rolls if 10 or fewer dice
                rolls_text = " ".join(f"`{roll}`" for roll in rolls)
                final_embed.add_field(
                    name="📊 Individual Rolls",
                    value=rolls_text,
                    inline=False
                )
            
            # Add special messages for certain rolls
            if num_dice == 1:
                if rolls[0] == sides:
                    final_embed.add_field(
                        name="✨ Special Roll",
                        value="🎉 **Critical Success!**",
                        inline=False
                    )
                elif rolls[0] == 1:
                    final_embed.add_field(
                        name="✨ Special Roll",
                        value="💔 **Critical Failure!**",
                        inline=False
                    )
            
            # Add footer
            final_embed.set_footer(text=f"Rolled by {interaction.user.name}")
            
            # Send final result
            await message.edit(embed=final_embed)
            
        except Exception as e:
            logger.error(f"Error in diceroll command: {str(e)}")
            await interaction.followup.send("❌ An error occurred while rolling the dice.", ephemeral=True)

    @bot.tree.command(name="coinflip", description="Flip a coin with a realistic animation")
    async def coinflip(interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Initial embed with a spinning coin GIF for a smooth animation
            embed = discord.Embed(
                title="🪙 Flipping Coin...",
                description="The coin is spinning in the air!",
                color=discord.Color.gold()
            )
            embed.set_image(url="https://media.tenor.com/XOoQu8wc35UAAAAj/coin.gif") # Reliable Tenor GIF
            
            # Send the initial message with the GIF
            message = await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Let the animation play for a moment to build suspense
            await asyncio.sleep(2) # 2-second delay for suspense
            
            # Final result
            final_result = random.choice(["HEADS", "TAILS"])
            
            # Create the final embed with the simple result
            final_embed = discord.Embed(
                title="🪙 Coin Flip Result",
                color=discord.Color.gold()
            )
            
            # Add result with simple formatting
            if final_result == "HEADS":
                final_embed.add_field(
                    name="✨ Result",
                    value="**HEADS**",
                    inline=False
                )
            else:
                final_embed.add_field(
                    name="✨ Result",
                    value="**TAILS**",
                    inline=False
                )
            
            # Add footer
            final_embed.set_footer(text=f"Flipped by {interaction.user.name}")
            
            # Edit the original message to show the final result
            await message.edit(embed=final_embed)
            
        except Exception as e:
            logger.error(f"Error in coinflip command: {str(e)}")
            await interaction.followup.send("❌ An error occurred while flipping the coin.", ephemeral=True)

    # --------------------
    # /help command
    # --------------------
    @bot.tree.command(name="help", description="Get the full HexxaBot game guide")
    async def help_command(interaction: discord.Interaction):
        """Send an embed directing users to the online game guide."""
        try:
            embed = discord.Embed(
                title="📖 HexxaBot Game Guide",
                description=(
                    "Want detailed rules, commands & strategies for every game?\n\n"
                    "👉 **Visit the online guide:** [HexxaBot Systems Guide](https://hexxabot.netlify.app/guide)\n\n\n"
                ),
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url="https://hexxabot.netlify.app/logo.jpg")
            embed.set_footer(text="Have fun and good luck!\nHexxaBot V6")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in help command: {str(e)}")
            await interaction.response.send_message("❌ An error occurred while fetching the guide.", ephemeral=True)
