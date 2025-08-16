import discord
import logging
import asyncio
from discord import app_commands
from utils.database import get_tictactoe_stats, update_tictactoe_stats, get_tictactoe_leaderboard

logger = logging.getLogger(__name__)

# Game state storage
active_games = {}
game_invites = {}

class TicTacToeGame:
    def __init__(self, player1, player2):
        self.board = [['⬜' for _ in range(3)] for _ in range(3)]
        self.current_player = player1
        self.player1 = player1
        self.player2 = player2
        self.winner = None
        self.is_draw = False
        self.last_move_time = discord.utils.utcnow()
        self.move_timeout = 15  # 15 seconds per move
        self.quit_by = None
        self.move_timer = None
        self.start_time = discord.utils.utcnow()
        self.moves_count = 0

    def get_time_left(self):
        elapsed = (discord.utils.utcnow() - self.last_move_time).total_seconds()
        return max(0, self.move_timeout - elapsed)

    def get_game_duration(self):
        return (discord.utils.utcnow() - self.start_time).total_seconds()

    def make_move(self, row, col):
        if self.board[row][col] != '⬜' or self.winner or self.is_draw:
            return False
        
        self.board[row][col] = '❌' if self.current_player == self.player1 else '⭕'
        self.last_move_time = discord.utils.utcnow()
        self.moves_count += 1
        
        # Check for win
        if self.check_win():
            self.winner = self.current_player
            return True
            
        # Check for draw
        if all(cell != '⬜' for row in self.board for cell in row):
            self.is_draw = True
            return True
            
        # Switch players
        self.current_player = self.player2 if self.current_player == self.player1 else self.player1
        return True

    def get_bot_move(self):
        """Get a valid move for the bot using minimax algorithm."""
        best_score = float('-inf')
        best_move = None
        
        # Try center first (best opening move)
        if self.board[1][1] == '⬜':
            return 1, 1
            
        # Try corners next
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        for row, col in corners:
            if self.board[row][col] == '⬜':
                return row, col
                
        # Try edges
        edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
        for row, col in edges:
            if self.board[row][col] == '⬜':
                return row, col
                
        # If no strategic moves, take any available move
        for row in range(3):
            for col in range(3):
                if self.board[row][col] == '⬜':
                    return row, col
                    
        return None

    def quit_game(self, quitter):
        self.quit_by = quitter
        self.winner = self.player2 if quitter == self.player1 else self.player1
        return True

    def check_win(self):
        # Check rows
        for row in self.board:
            if row[0] != '⬜' and row[0] == row[1] == row[2]:
                return True
                
        # Check columns
        for col in range(3):
            if self.board[0][col] != '⬜' and self.board[0][col] == self.board[1][col] == self.board[2][col]:
                return True
                
        # Check diagonals
        if self.board[0][0] != '⬜' and self.board[0][0] == self.board[1][1] == self.board[2][2]:
            return True
        if self.board[0][2] != '⬜' and self.board[0][2] == self.board[1][1] == self.board[2][0]:
            return True
            
        return False

    def get_board_embed(self):
        embed = discord.Embed(
            title="🎮 Tic Tac Toe",
            description="Use the buttons below to make your move!",
            color=0x00ff00
        )
        
        # Create the board display with better formatting
        board_text = "```\n"
        for row in self.board:
            board_text += " ".join(row) + "\n"
        board_text += "```"
            
        embed.add_field(name="Game Board", value=board_text, inline=False)
        
        # Add current player info with better formatting
        if self.winner:
            if self.quit_by:
                embed.add_field(
                    name="🏆 Game Over!",
                    value=f"🎉 {self.winner.mention} wins!\n{self.quit_by.mention} quit the game.",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🏆 Game Over!",
                    value=f"🎉 {self.winner.mention} wins!",
                    inline=False
                )
            embed.color = 0x00ff00  # Green for win
        elif self.is_draw:
            embed.add_field(
                name="🤝 Game Over!",
                value="It's a draw!",
                inline=False
            )
            embed.color = 0xffff00  # Yellow for draw
        else:
            time_left = self.get_time_left()
            embed.add_field(
                name="⏳ Current Turn",
                value=f"{self.current_player.mention}'s turn ({'❌' if self.current_player == self.player1 else '⭕'})\n"
                      f"⏰ Time left: {time_left:.1f} seconds",
                inline=False
            )
            embed.color = 0x3498db  # Blue for ongoing game
            
        # Add player info with better formatting
        embed.add_field(
            name="Players",
            value=f"❌ {self.player1.mention}\n⭕ {self.player2.mention}",
            inline=False
        )

        # Add game stats
        duration = self.get_game_duration()
        embed.add_field(
            name="Game Stats",
            value=f"⏱️ Duration: {duration:.1f} seconds\n"
                  f"🎯 Moves: {self.moves_count}",
            inline=False
        )
            
        return embed

class TicTacToeView(discord.ui.View):
    def __init__(self, game: TicTacToeGame, supabase):
        super().__init__(timeout=300)  # 5 minute timeout
        self.game = game
        self.supabase = supabase
        self.message = None
        self.last_update = discord.utils.utcnow()
        
        # Create buttons for each cell with better styling
        for row in range(3):
            for col in range(3):
                button = discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="⬜",
                    row=row,
                    custom_id=f"ttt_{row}_{col}"
                )
                button.callback = self.button_callback
                self.add_item(button)
        
        # Add quit button with better styling
        quit_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Quit Game",
            row=3,
            custom_id="ttt_quit",
            emoji="🚫"
        )
        quit_button.callback = self.quit_callback
        self.add_item(quit_button)

    async def start_move_timer(self):
        """Start the move timer."""
        while not self.game.winner and not self.game.is_draw:
            try:
                current_time = discord.utils.utcnow()
                
                # Update the message with current time left (but not too frequently)
                if self.message and (current_time - self.last_update).total_seconds() >= 1:
                    await self.message.edit(embed=self.game.get_board_embed(), view=self)
                    self.last_update = current_time
                
                # Check if time has run out
                if self.game.get_time_left() <= 0:
                    # Time's up - other player wins
                    self.game.winner = self.game.player2 if self.game.current_player == self.game.player1 else self.game.player1
                    for item in self.children:
                        item.disabled = True
                    if self.message:
                        await self.message.edit(embed=self.game.get_board_embed(), view=self)
                    await self.cleanup_game(self.message)
                    break
                
                await asyncio.sleep(0.5)  # Check more frequently but update display less often
            except Exception as e:
                logger.error(f"Error in move timer: {str(e)}")
                break

    async def cleanup_game(self, interaction: discord.Interaction):
        """Clean up the game from active_games and update stats."""
        # Remove game from active games
        if self.game.player1.id in active_games:
            del active_games[self.game.player1.id]
        if self.game.player2.id in active_games:
            del active_games[self.game.player2.id]
            
        # Update stats in database
        try:
            guild_id = interaction.guild_id
            if self.game.winner:
                if self.game.quit_by:
                    # Handle quit case
                    update_tictactoe_stats(
                        self.supabase,
                        guild_id,
                        str(self.game.winner.id),
                        "win"
                    )
                    update_tictactoe_stats(
                        self.supabase,
                        guild_id,
                        str(self.game.quit_by.id),
                        "loss"
                    )
                else:
                    # Handle normal win case
                    update_tictactoe_stats(
                        self.supabase,
                        guild_id,
                        str(self.game.winner.id),
                        "win"
                    )
                    update_tictactoe_stats(
                        self.supabase,
                        guild_id,
                        str(self.game.player2.id if self.game.winner == self.game.player1 else self.game.player1.id),
                        "loss"
                    )
            else:  # Draw
                update_tictactoe_stats(
                    self.supabase,
                    guild_id,
                    str(self.game.player1.id),
                    "draw"
                )
                update_tictactoe_stats(
                    self.supabase,
                    guild_id,
                    str(self.game.player2.id),
                    "draw"
                )
        except Exception as e:
            logger.error(f"Failed to update Tic Tac Toe stats: {str(e)}")
            if isinstance(interaction, discord.Interaction):
                await interaction.channel.send("⚠️ There was an error updating the game stats.")
            else:
                await interaction.send("⚠️ There was an error updating the game stats.")

    async def button_callback(self, interaction: discord.Interaction):
        if interaction.user != self.game.current_player:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
            
        # Parse button position from the button's custom_id
        button = interaction.data.get("custom_id", "")
        if not button.startswith("ttt_"):
            return
            
        _, row, col = button.split("_")
        row, col = int(row), int(col)
        
        # Make move
        if self.game.make_move(row, col):
            # Update the board display
            await interaction.message.edit(embed=self.game.get_board_embed(), view=self)
            
            # If game is over, update stats and disable buttons
            if self.game.winner or self.game.is_draw:
                for item in self.children:
                    item.disabled = True
                await interaction.message.edit(view=self)
                
                # Clean up game and update stats
                await self.cleanup_game(interaction)
                    
        await interaction.response.defer()

    async def quit_callback(self, interaction: discord.Interaction):
        if interaction.user not in [self.game.player1, self.game.player2]:
            await interaction.response.send_message("You're not a player in this game!", ephemeral=True)
            return
            
        if self.game.quit_game(interaction.user):
            # Update the board display
            await interaction.message.edit(embed=self.game.get_board_embed(), view=self)
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)
            
            # Clean up game and update stats
            await self.cleanup_game(interaction)
                
        await interaction.response.defer()

    async def on_timeout(self):
        """Handle game timeout."""
        if not self.game.winner and not self.game.is_draw:
            # If game times out, it's a draw
            self.game.is_draw = True
            for item in self.children:
                item.disabled = True
            
            # Clean up game and update stats
            try:
                guild_id = self.game.player1.guild.id
                update_tictactoe_stats(
                    self.game.player1.client.supabase,
                    guild_id,
                    str(self.game.player1.id),
                    "draw"
                )
                update_tictactoe_stats(
                    self.game.player1.client.supabase,
                    guild_id,
                    str(self.game.player2.id),
                    "draw"
                )
            except Exception as e:
                logger.error(f"Failed to update Tic Tac Toe stats on timeout: {str(e)}")
            
            # Remove game from active games
            if self.game.player1.id in active_games:
                del active_games[self.game.player1.id]
            if self.game.player2.id in active_games:
                del active_games[self.game.player2.id]

class GameInviteView(discord.ui.View):
    def __init__(self, host, opponent, channel, timeout=60):
        super().__init__(timeout=timeout)
        self.host = host
        self.opponent = opponent
        self.channel = channel
        self.accepted = False
        self.denied = False
        self.message = None
        self.start_time = discord.utils.utcnow()

    def get_time_left(self):
        elapsed = (discord.utils.utcnow() - self.start_time).total_seconds()
        return max(0, self.timeout - elapsed)

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("This invitation is not for you!", ephemeral=True)
            return
            
        self.accepted = True
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message("Challenge accepted! Starting the game...", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, emoji="❌")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("This invitation is not for you!", ephemeral=True)
            return
            
        self.denied = True
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message("Challenge declined!", ephemeral=True)
        self.stop()

    async def on_timeout(self):
        if not self.accepted and not self.denied:
            for item in self.children:
                item.disabled = True
            if self.message:
                await self.message.edit(view=self)
            await self.channel.send(f"{self.host.mention}, {self.opponent.mention} did not respond to your game invitation in time.")

def setup(bot, supabase):
    @bot.tree.command(name="tictactoe", description="Play Tic Tac Toe with another user!")
    @app_commands.describe(opponent="The user you want to play against")
    async def tictactoe(interaction: discord.Interaction, opponent: discord.Member):
        # Prevent self-play
        if interaction.user.id == opponent.id:
            await interaction.response.send_message("❌ You can't play against yourself!", ephemeral=True)
            return
            
        # Prevent playing with bots
        if opponent.bot:
            await interaction.response.send_message("❌ You can't play Tic Tac Toe against bots (yet 😉).", ephemeral=True)
            return
            
        # Check if either player is already in a game
        if interaction.user.id in active_games or opponent.id in active_games:
            await interaction.response.send_message("❌ One of the players is already in a game!", ephemeral=True)
            return
            
        # Create invitation embed with better styling
        embed = discord.Embed(
            title="🎮 Tic Tac Toe Challenge",
            description=f"{opponent.mention}, you've been challenged to a game of Tic Tac Toe!",
            color=0x3498db
        )
        embed.add_field(
            name="Game Details",
            value=f"**Host:** {interaction.user.mention}\n"
                  f"**Channel:** {interaction.channel.mention}\n"
                  f"**Server:** {interaction.guild.name}\n"
                  f"**Time Limit:** 60 seconds to respond\n"
                  f"**Move Timeout:** 15 seconds per move",
            inline=False
        )
        
        # Create invitation view
        view = GameInviteView(interaction.user, opponent, interaction.channel)
        
        # Try to send DM first
        try:
            # Defer the interaction first
            await interaction.response.defer(ephemeral=True)
            
            # Send DM to opponent
            message = await opponent.send(embed=embed, view=view)
            view.message = message
            
            # Send confirmation to the host
            await interaction.followup.send(f"✅ Game invitation sent to {opponent.mention}'s DMs!", ephemeral=True)
            
        except discord.Forbidden:
            # If DM fails, send in channel
            message = await interaction.response.send_message(embed=embed, view=view)
            view.message = message
        
        # Wait for response
        try:
            await view.wait()
            
            if view.accepted:
                # Start the game
                game = TicTacToeGame(interaction.user, opponent)
                active_games[interaction.user.id] = game
                active_games[opponent.id] = game
                
                game_view = TicTacToeView(game, supabase)
                message = await interaction.channel.send(
                    f"🎮 {interaction.user.mention} vs {opponent.mention}\n"
                    f"{interaction.user.mention} goes first!",
                    embed=game.get_board_embed(),
                    view=game_view
                )
                game_view.message = message
                asyncio.create_task(game_view.start_move_timer())
            elif view.denied:
                await interaction.channel.send(f"❌ {interaction.user.mention}, {opponent.mention} declined your game invitation.")
                
        except Exception as e:
            logger.error(f"Error in game invitation: {str(e)}")
            await interaction.channel.send("❌ An error occurred while processing the game invitation.")

    @bot.tree.command(name="tictactoe-stats", description="Check your Tic Tac Toe stats or stats of another user")
    @app_commands.describe(member="Mention a user to check their stats (optional)")
    async def tictactoe_stats(interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer(ephemeral=True)
        
        guild_id = interaction.guild_id
        user_id = str(member.id if member else interaction.user.id)
        user_name = member.name if member else interaction.user.name
        
        try:
            stats = get_tictactoe_stats(supabase, guild_id, user_id)
            if stats:
                wins = stats.get("wins", 0)
                losses = stats.get("losses", 0)
                draws = stats.get("draws", 0)
                total_games = stats.get("total_games", 0)
                
                await interaction.followup.send(
                    f"📊 **{user_name}'s Tic Tac Toe Stats**\n\n"
                    f"🏆 Wins: {wins}\n"
                    f"❌ Losses: {losses}\n"
                    f"🤝 Draws: {draws}\n"
                    f"🎮 Total Games: {total_games}"
                )
            else:
                await interaction.followup.send(f"{user_name} hasn't played Tic Tac Toe yet!")
        except Exception as e:
            logger.error(f"Failed to get Tic Tac Toe stats: {str(e)}")
            await interaction.followup.send("⚠️ Could not retrieve stats due to a database error.")

    @bot.tree.command(name="tictactoe-lb", description="Show Tic Tac Toe leaderboard")
    async def tictactoe_leaderboard(interaction: discord.Interaction):
        await interaction.response.defer()
        
        guild_id = interaction.guild_id
        if not guild_id:
            await interaction.followup.send("This command can only be used in a server.")
            return
            
        try:
            leaderboard_data = get_tictactoe_leaderboard(supabase, guild_id, 10)
            
            if not leaderboard_data:
                await interaction.followup.send("No one has played Tic Tac Toe yet!")
                return
                
            # Create a nice-looking embed for the leaderboard
            embed = discord.Embed(
                title="🎮 Tic Tac Toe Leaderboard 🏆",
                description="Top 10 players ranked by win percentage",
                color=0x00ff00
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
                member = interaction.guild.get_member(user_id)
                display_name = member.display_name if member else f"Unknown Player"
                
                # Calculate win percentage
                wins = player_data.get("wins", 0)
                losses = player_data.get("losses", 0)
                draws = player_data.get("draws", 0)
                total = player_data.get("total_games", 0)
                win_rate = (wins / total * 100) if total > 0 else 0
                
                # Format medal for top 3
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`#{i}`"
                
                # Add player to the leaderboard text with better formatting
                leaderboard_text += f"**{medal} {display_name}**\n"
                leaderboard_text += f"┣ Win Rate: **{win_rate:.1f}%**\n"
                leaderboard_text += f"┣ W: **{wins}** ┃ L: **{losses}** ┃ D: **{draws}**\n"
                leaderboard_text += f"┗ Total Games: **{total}**\n\n"
            
            # Add the formatted text to the embed
            embed.description = f"Top 10 players ranked by win percentage\n\n{leaderboard_text}"
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to get Tic Tac Toe leaderboard: {str(e)}")
            await interaction.followup.send("⚠️ Could not retrieve the leaderboard due to an error.") 