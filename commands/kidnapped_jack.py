import discord
import random
import asyncio
import logging
import time
from discord import app_commands
from utils.database import get_kidnapped_jack_stats, update_kidnapped_jack_stats, get_kidnapped_jack_leaderboard, create_kidnapped_jack_table
from collections import defaultdict

logger = logging.getLogger(__name__)

# Game state storage
active_games = {}

# Constants
MIN_PLAYERS = 2
MAX_PLAYERS = 10
TURN_TIMEOUT = 30
INVITE_TIMEOUT = 60

# Cooldown tracking
default_cooldowns = defaultdict(float)

# Card emojis and representations
CARD_EMOJIS = {
    'A': '🂡', '2': '🂢', '3': '🂣', '4': '🂤', '5': '🂥', '6': '🂦', '7': '🂧', '8': '🂨', '9': '🂩', '10': '🂪', 'J': '🂫', 'Q': '🂭', 'K': '🂮'
}

SUIT_EMOJIS = {
    'hearts': '♥️', 'diamonds': '♦️', 'clubs': '♣️', 'spades': '♠️'
}

# Special Jack of Hearts emoji
JACK_OF_HEARTS_EMOJI = '🂻'

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.is_jack_of_hearts = (rank == 'J' and suit == 'hearts')
    
    def __str__(self):
        if self.is_jack_of_hearts:
            return f"{JACK_OF_HEARTS_EMOJI} Jack of Hearts"
        return f"{CARD_EMOJIS.get(self.rank, self.rank)}{SUIT_EMOJIS[self.suit]} {self.rank} of {self.suit.title()}"
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self):
        return hash((self.rank, self.suit))

class KidnappedJackPlayer:
    def __init__(self, user):
        self.user = user
        self.hand = []
        self.eliminated = False
        self.is_kidnapper = False
        self.win_place = 0  # 0 = not won yet, 1 = first place, etc.
    
    def add_card(self, card):
        self.hand.append(card)
    
    def remove_card(self, card):
        if card in self.hand:
            self.hand.remove(card)
            return True
        return False
    
    def find_pairs(self):
        """Find and return all pairs in the player's hand"""
        pairs = []
        hand_copy = self.hand.copy()
        
        # Group cards by rank
        rank_groups = {}
        for card in hand_copy:
            if card.rank not in rank_groups:
                rank_groups[card.rank] = []
            rank_groups[card.rank].append(card)
        
        # Find pairs (same rank, different suits)
        for rank, cards in rank_groups.items():
            if len(cards) >= 2:
                # Sort by suit to ensure consistent pairing
                cards.sort(key=lambda c: c.suit)
                while len(cards) >= 2:
                    pair = [cards.pop(0), cards.pop(0)]
                    pairs.append(pair)
        
        return pairs
    
    def remove_pairs(self):
        """Remove all pairs from hand and return them"""
        pairs = self.find_pairs()
        removed_pairs = []
        
        for pair in pairs:
            for card in pair:
                self.hand.remove(card)
            removed_pairs.append(pair)
        
        return removed_pairs

class KidnappedJackGame:
    def __init__(self, players, jack_nickname="Jack of Hearts"):
        self.players = players
        self.current_player_index = 0
        self.jack_nickname = jack_nickname
        self.game_started = False
        self.game_over = False
        self.kidnapper = None
        self.deck = self._create_deck()
        self.game_history = []
        self.start_time = time.time()
        self.turn_start_time = None
        self.last_action = "Game created! Waiting for players to join..."
    
    def _create_deck(self):
        """Create a deck with all cards except other Jacks (only Jack of Hearts remains)"""
        deck = []
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        
        for suit in suits:
            for rank in ranks:
                # Only include Jack of Hearts, exclude other Jacks
                if rank == 'J' and suit != 'hearts':
                    continue
                deck.append(Card(rank, suit))
        
        return deck
    
    def deal_cards(self):
        """Deal all cards to players"""
        random.shuffle(self.deck)
        
        # Deal cards evenly
        cards_per_player = len(self.deck) // len(self.players)
        remainder = len(self.deck) % len(self.players)
        
        card_index = 0
        for i, player in enumerate(self.players):
            # Give extra cards to first few players if there's remainder
            extra_cards = 1 if i < remainder else 0
            for _ in range(cards_per_player + extra_cards):
                if card_index < len(self.deck):
                    player.add_card(self.deck[card_index])
                    card_index += 1
        
        # Remove initial pairs from all players
        self._remove_initial_pairs()
        self.game_started = True
        self.turn_start_time = time.time()
    
    def _remove_initial_pairs(self):
        """Remove all initial pairs from all players"""
        for player in self.players:
            pairs = player.remove_pairs()
            if pairs:
                pair_text = ", ".join([f"{pair[0].rank} of {pair[0].suit.title()}" for pair in pairs])
                self.game_history.append(f"🎉 {player.user.mention} removed pairs: {pair_text}")
    
    def get_current_player(self):
        return self.players[self.current_player_index]
    
    def get_next_player(self):
        """Get the next player who still has cards"""
        next_index = (self.current_player_index + 1) % len(self.players)
        attempts = 0
        
        while attempts < len(self.players):
            if not self.players[next_index].eliminated and len(self.players[next_index].hand) > 0:
                return self.players[next_index]
            next_index = (next_index + 1) % len(self.players)
            attempts += 1
        
        return None
    
    def draw_card(self, from_player_index):
        """Current player draws a card from another player"""
        current_player = self.get_current_player()
        from_player = self.players[from_player_index]
        
        if len(from_player.hand) == 0:
            return False, "That player has no cards left!"
        
        # Draw a random card
        drawn_card = random.choice(from_player.hand)
        from_player.remove_card(drawn_card)
        current_player.add_card(drawn_card)
        
        # Check if this creates a pair with reduced probability
        # Only 40% chance to automatically form pairs to make the game more challenging
        pair_chance = random.random()
        pairs_formed = False
        
        if pair_chance < 0.4:  # 40% chance to form pairs
            pairs = current_player.find_pairs()
            if pairs:
                # Remove the pair
                removed_pairs = current_player.remove_pairs()
                pair_text = ", ".join([f"{pair[0].rank}" for pair in removed_pairs])
                self.game_history.append(f"🎉 {current_player.user.mention} drew a card and made pairs: {pair_text}")
                pairs_formed = True
        
        if not pairs_formed:
            # Don't reveal which card was drawn to add mystery
            self.game_history.append(f"📤 {current_player.user.mention} drew a card from {from_player.user.mention}")
        
        # Check if from_player is eliminated
        if len(from_player.hand) == 0:
            from_player.eliminated = True
            # Register as winner/escapee
            if not hasattr(self, 'winners'):
                self.winners = []
            from_player.win_place = len(self.winners) + 1
            self.winners.append(from_player)
            suffix = self._get_ordinal_suffix(from_player.win_place) if hasattr(self, '_get_ordinal_suffix') else ['', 'st', 'nd', 'rd'][min(from_player.win_place,3)]
            self.game_history.append(f"🎉 {from_player.user.mention} escaped ({from_player.win_place}{suffix} place)!")
        
        # Check if game is over
        active_players = [p for p in self.players if not p.eliminated and len(p.hand) > 0]
        if len(active_players) == 1:
            self._end_game(active_players[0])
            return True, "Game over!"
        
        # Check if only one player has cards left
        players_with_cards = [p for p in self.players if len(p.hand) > 0]
        if len(players_with_cards) == 1:
            self._end_game(players_with_cards[0])
            return True, "Game over!"
        
        # Move to next player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        attempts = 0
        while (self.players[self.current_player_index].eliminated or 
               len(self.players[self.current_player_index].hand) == 0) and attempts < len(self.players):
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            attempts += 1
        
        self.turn_start_time = time.time()
        return True, "Card drawn successfully!"
    
    def _end_game(self, kidnapper):
        """End the game when only the kidnapper remains"""
        self.game_over = True
        
        # Register remaining player as Kidnapper (loser) and finalise placements
        if not hasattr(self, 'winners'):
            self.winners = []
        kidnapper.is_kidnapper = True
        self.kidnapper = kidnapper
        kidnapper.win_place = len(self.winners) + 1
        self.winners.append(kidnapper)
        self.game_history.append(f"💀 {kidnapper.user.mention} is the Kidnapper and loses!")
    
    def get_game_duration(self):
        """Get the total game duration in seconds"""
        return time.time() - self.start_time
    
    def get_turn_duration(self):
        """Get the current turn duration in seconds"""
        if self.turn_start_time:
            return time.time() - self.turn_start_time
        return 0

class KidnappedJackView(discord.ui.View):
    def __init__(self, game: KidnappedJackGame, supabase, channel, bot):
        super().__init__(timeout=None)
        self.game = game
        self.supabase = supabase
        self.channel = channel
        self.bot = bot
        self.message = None
        self._turn_task = None
        self._timeout_task = None
        self._build_buttons()
        # Start timeout timer for game start (2 minutes)
        self._start_timeout_timer()
    
    def disable_all_buttons(self):
        """Disable all buttons in the view"""
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    def _build_buttons(self):
        """Build the player selection buttons"""
        self.clear_items()
        
        if self.game.game_over:
            # Game is over - only show rematch button
            rematch_button = discord.ui.Button(label="🔄 Rematch", style=discord.ButtonStyle.success, custom_id="rematch")
            rematch_button.callback = self.rematch_callback
            self.add_item(rematch_button)
            return
            
        if not self.game.game_started:
            # Game hasn't started yet - clean layout
            if len(self.game.players) < MAX_PLAYERS:
                join_button = discord.ui.Button(label="➕ Join Game", style=discord.ButtonStyle.primary, custom_id="join")
                join_button.callback = self.join_game_callback
                self.add_item(join_button)
            
            if len(self.game.players) >= MIN_PLAYERS:
                start_button = discord.ui.Button(label="🎮 Start Game", style=discord.ButtonStyle.success, custom_id="start")
                start_button.callback = self.start_game_callback
                self.add_item(start_button)
            
            leave_button = discord.ui.Button(label="❌ Leave", style=discord.ButtonStyle.danger, custom_id="leave")
            leave_button.callback = self.leave_game_callback
            self.add_item(leave_button)
            
        else:
            # Game is in progress - organized player buttons
            current_player = self.game.get_current_player()
            available_players = []
            
            for i, player in enumerate(self.game.players):
                if player != current_player and not player.eliminated and len(player.hand) > 0:
                    available_players.append((i, player))
            
            # Sort players by their position in the game (host first, then in order of joining)
            available_players.sort(key=lambda x: x[0])
            
            # Add draw buttons in a grid
            buttons_per_row = min(3, len(available_players))
            for i, (player_index, player) in enumerate(available_players):
                button = discord.ui.Button(
                    label=f"🎴 {player.user.display_name}",
                    style=discord.ButtonStyle.primary,
                    custom_id=f"draw_{player_index}",
                    row=i // buttons_per_row
                )
                button.callback = self.draw_card_callback
                self.add_item(button)
            
            # Add quit button on a new row
            quit_button = discord.ui.Button(
                label="🚫 Quit Game", 
                style=discord.ButtonStyle.danger, 
                custom_id="quit",
                row=(len(available_players) + buttons_per_row - 1) // buttons_per_row
            )
            quit_button.callback = self.quit_game_callback
            self.add_item(quit_button)
    
    async def start_game_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.game.players[0].user.id:
            await interaction.response.send_message("Only the game host can start the game!", ephemeral=True)
            return
        
        if len(self.game.players) < MIN_PLAYERS:
            await interaction.response.send_message(f"Need at least {MIN_PLAYERS} players to start!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Cancel the timeout timer since game is starting
        self._cancel_timeout()
        
        self.game.deal_cards()
        self._build_buttons()
        await self.update_message(interaction)
    
    async def join_game_callback(self, interaction: discord.Interaction):
        if interaction.user.id in [p.user.id for p in self.game.players]:
            await interaction.response.send_message("You're already in this game!", ephemeral=True)
            return
        
        if len(self.game.players) >= MAX_PLAYERS:
            await interaction.response.send_message("Game is full!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Add player to game
        new_player = KidnappedJackPlayer(interaction.user)
        self.game.players.append(new_player)
        active_games[interaction.user.id] = self.game
        self.game.game_history.append(f" {interaction.user.mention} joined the game")
        
        self._build_buttons()
        await self.update_message(interaction)
    
    async def leave_game_callback(self, interaction: discord.Interaction):
        if interaction.user.id not in [p.user.id for p in self.game.players]:
            await interaction.response.send_message("You're not in this game!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Find the player to remove
        player_to_remove = None
        player_index = -1
        for i, player in enumerate(self.game.players):
            if player.user.id == interaction.user.id:
                player_to_remove = player
                player_index = i
                break
        
        if not player_to_remove:
            return
            
        was_host = (player_index == 0)  # Host is always the first player
        
        # Handle game state if game is in progress
        if self.game.game_started and not self.game.game_over:
            # If it's the current player's turn, move to next player
            if self.game.current_player_index == player_index:
                self.game.current_player_index = (self.game.current_player_index - 1) % len(self.game.players)
            elif self.game.current_player_index > player_index:
                self.game.current_player_index -= 1
                
            # Remove player's cards from the game
            if player_to_remove.hand:
                self.game.game_history.append(f"{player_to_remove.user.mention}'s cards were discarded")
        
        # Remove player from game
        self.game.players.remove(player_to_remove)
        active_games.pop(interaction.user.id, None)
        
        # If game is in progress, don't end it
        if self.game.game_started and not self.game.game_over:
            self.game.game_history.append(f"{player_to_remove.user.mention} left the game (cards discarded)")
            
            # Reassign host if needed
            if was_host and self.game.players:
                new_host = self.game.players[0]
                self.game.game_history.append(f"👑 {new_host.user.mention} is the new host!")
            
            # If only one player remains, they win
            if len([p for p in self.game.players if not p.eliminated]) == 1:
                winner = next((p for p in self.game.players if not p.eliminated), None)
                if winner:
                    winner.win_place = len([p for p in self.game.players if p.win_place > 0]) + 1
                    self.game._end_game(winner)
        else:
            # Game hasn't started yet
            self.game.game_history.append(f"{player_to_remove.user.mention} left the game")
            
            # Reassign host if needed
            if was_host and self.game.players:
                new_host = self.game.players[0]
                self.game.game_history.append(f"👑 {new_host.user.mention} is the new host!")
            
            # If not enough players, end game
            if len(self.game.players) < MIN_PLAYERS:
                self.game.game_over = True
                self.game.game_history.append("❌ Not enough players to start. Game ended.")
        
        # Disable all buttons if game is over
        if self.game.game_over:
            self.disable_all_buttons()
            await self.finish_game()
            
        self._build_buttons()
        await self.update_message(interaction)
    
    async def draw_card_callback(self, interaction: discord.Interaction):
        current_player = self.game.get_current_player()
        if interaction.user.id != current_player.user.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        custom_id = interaction.data["custom_id"]
        from_player_index = int(custom_id.split("_")[1])
        
        success, message = self.game.draw_card(from_player_index)
        
        if success:
            self._build_buttons()
            await self.update_message(interaction)
            
            # Check if game ended and update stats
            if self.game.game_over:
                await self.finish_game()
        else:
            await interaction.followup.send(message, ephemeral=True)
    
    async def quit_game_callback(self, interaction: discord.Interaction):
        if interaction.user.id not in [p.user.id for p in self.game.players]:
            await interaction.response.send_message("You're not in this game!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        self.game.game_over = True
        self.game.game_history.append(f"🚫 {interaction.user.mention} quit the game")
        self._build_buttons()
        await self.update_message(interaction)
        await self.finish_game()
    
    async def rematch_callback(self, interaction: discord.Interaction):
        # Check if the user is in the game
        if interaction.user.id not in [p.user.id for p in self.game.players]:
            await interaction.response.send_message("You're not in this game!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Create a new game with the same players
        new_game = KidnappedJackGame(self.game.players, self.game.jack_nickname)
        new_view = KidnappedJackView(new_game, self.supabase, self.channel, self.bot)
        
        # Clear old game state for all players
        for player in self.game.players:
            if player.user.id in active_games:
                del active_games[player.user.id]
        
        # Add all players to active games for the new game
        for player in new_game.players:
            active_games[player.user.id] = new_game
        
        # Send new game message
        try:
            embed = new_view.create_embed()
            msg = await self.channel.send(embed=embed, view=new_view)
            new_view.message = msg
            
            # Notify all players about the rematch (ephemeral)
            mention_list = " ".join([p.user.mention for p in new_game.players])
            await interaction.followup.send(
                f"🎮 New game created by {interaction.user.mention}! Check the new message above!", 
                ephemeral=True
            )
            
            # Send a non-ephemeral message to notify everyone
            notification = await interaction.followup.send(
                f"🎮 {interaction.user.mention} has started a new game! {mention_list}",
                wait=True
            )
            
            # Delete the notification after 10 seconds
            await asyncio.sleep(10)
            try:
                await notification.delete()
            except:
                pass
            
            # Clean up the old message
            if self.message:
                try:
                    await self.message.delete()
                except discord.NotFound:
                    pass
        except Exception as e:
            logger.error(f"Error creating rematch: {str(e)}")
            await interaction.followup.send("❌ Failed to create rematch. Please try again.", ephemeral=True)
    
    def _start_timeout_timer(self):
        """Start the 2-minute timeout timer for game start"""
        if not self.game.game_started:
            self._timeout_task = asyncio.create_task(self._handle_timeout())
    
    async def _handle_timeout(self):
        """Handle the timeout if no players join within 2 minutes"""
        try:
            await asyncio.sleep(120)  # 2 minutes
            
            # Check if game has started or if there are enough players
            if not self.game.game_started and len(self.game.players) < MIN_PLAYERS:
                # Timeout the game
                self.game.game_over = True
                self.game.game_history.append("⏰ Game timed out - not enough players joined within 2 minutes!")
                
                # Remove players from active games
                for player in self.game.players:
                    if player.user.id in active_games:
                        del active_games[player.user.id]
                
                # Update the message to show timeout
                embed = discord.Embed(
                    title="🃏 The Kidnapped Jack - Timed Out",
                    description="⏰ **Game Timed Out!**\n\nNot enough players joined within 2 minutes.\nUse `/kidnapped-jack` to start a new game!",
                    color=discord.Color.red()
                )
                embed.set_footer(text="Game timed out after 2 minutes")
                
                if self.message:
                    await self.message.edit(embed=embed, view=None)
                    
        except asyncio.CancelledError:
            # Timeout was cancelled (game started or players joined)
            pass
    
    def _cancel_timeout(self):
        """Cancel the timeout timer"""
        if self._timeout_task and not self._timeout_task.done():
            self._timeout_task.cancel()
    
    async def finish_game(self):
        """Finish the game and update stats"""
        if not self.game.game_over:
            return
        
        # Update stats for all players
        guild_id = self.channel.guild.id
        game_time = self.game.get_game_duration()
        
        # Make sure we have winners list
        if not hasattr(self.game, 'winners'):
            self.game.winners = []
            
        # Add any remaining players to winners list in order of elimination
        remaining_players = [p for p in self.game.players if p not in self.game.winners]
        remaining_players.sort(key=lambda p: len(p.hand))  # Sort by fewest cards first
        
        for i, player in enumerate(remaining_players, start=len(self.game.winners) + 1):
            player.win_place = i
            self.game.winners.append(player)
        
        # Update stats for all players
        for player in self.game.players:
            if hasattr(player.user, 'bot') and player.user.bot:
                continue
            
            try:
                if player.is_kidnapper:
                    update_kidnapped_jack_stats(
                        self.supabase, 
                        guild_id, 
                        str(player.user.id), 
                        "kidnapper", 
                        game_time,
                        player.win_place
                    )
                else:
                    update_kidnapped_jack_stats(
                        self.supabase, 
                        guild_id, 
                        str(player.user.id), 
                        "escape", 
                        game_time,
                        player.win_place
                    )
            except Exception as e:
                logger.error(f"Failed to update stats for {player.user.name}: {str(e)}")
        
        # Remove players from active games
        for player in self.game.players:
            active_games.pop(player.user.id, None)
            
        # Disable all buttons
        self.disable_all_buttons()
    
    async def update_message(self, interaction: discord.Interaction = None):
        embed = self.create_embed()
        self._build_buttons()
        
        try:
            if interaction and not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=self)
            elif self.message:
                await self.message.edit(embed=embed, view=self)
        except discord.NotFound:
            logger.warning("Game message not found during update")
    
    def create_embed(self):
        """Create a clean, organized embed for the game"""
        embed = discord.Embed(
            title="🃏 The Kidnapped Jack",
            color=discord.Color.purple()
        )
        
        # Add game status based on state
        if not self.game.game_started:
            embed.description = "**⏳ Waiting for players to join...**\n\n📝 **Game Rules:**\n• Draw cards from other players\n• Remove pairs automatically (sometimes!)\n• First to be eliminated wins as the Kidnapper!"
            
            # Player list with visual indicators
            if self.game.players:
                player_list = "\n".join([f"👤 {player.user.mention}" for player in self.game.players])
            else:
                player_list = "🚫 No players yet - Click **Join Game** to start!"
            
            embed.add_field(
                name=f"👥 Players ({len(self.game.players)}/{MAX_PLAYERS})",
                value=player_list,
                inline=False
            )
            
            # Visual game flow diagram
            embed.add_field(
                name="🔄 Game Flow",
                value="```\n1. Join Game → 2. Start Game → 3. Draw Cards → 4. First out wins!\n```",
                inline=False
            )
            
            # Warning about random clicking
            embed.add_field(
                name="⚠️ Important",
                value="**Think before you click!** First player to be eliminated wins as the Kidnapper!",
                inline=False
            )
            
        elif not self.game.game_over:
            # Game in progress with enhanced UI
            current_player = self.game.get_current_player()
            
            # Create a visual turn indicator
            turn_indicator = f"🎯 **{current_player.user.mention}'s Turn**\n👉 Choose a player to draw from below"
            embed.description = turn_indicator
            
            # Player status with card counts and visual indicators
            active_players = [p for p in self.game.players if not p.eliminated and len(p.hand) > 0]
            player_status = []
            
            # Show winners first
            if hasattr(self.game, 'winners') and self.game.winners:
                for winner in sorted(self.game.winners, key=lambda p: p.win_place):
                    if winner.is_kidnapper:
                        player_status.append(f"🥇 {winner.user.mention} - Kidnapper (1st place)")
                    else:
                        player_status.append(f"🏅 {winner.user.mention} - {winner.win_place}{self._get_ordinal_suffix(winner.win_place)} place")
                
                if active_players:
                    player_status.append("\n**Still in the game:**")
            
            # Then show active players
            for player in self.game.players:
                if player.eliminated:
                    continue
                    
                if player == current_player:
                    status = f"🎯 {player.user.mention} ({len(player.hand)} cards) ⭐"
                else:
                    status = f"🂴 {player.user.mention} ({len(player.hand)} cards)"
                player_status.append(status)
            
            embed.add_field(
                name=f"👥 Player Status ({len(active_players)} active)",
                value="\n".join(player_status) or "No active players",
                inline=False
            )
            
            # Game progress with visual bar
            total_cards = sum(len(p.hand) for p in self.game.players)
            progress_bar = "█" * min(10, total_cards // 5) + "░" * (10 - min(10, total_cards // 5))
            embed.add_field(
                name="📈 Game Progress",
                value=f"```\n[{progress_bar}] {total_cards} cards left\n```",
                inline=False
            )
            
            # Add game rules reminder
            embed.add_field(
                name="🎯 Goal",
                value="Be the **first** to get eliminated to win as the Kidnapper!",
                inline=False
            )
            
        else:  # Game over
            if hasattr(self.game, 'winners') and self.game.winners:
                # Sort winners by their placement
                winners = sorted(self.game.winners, key=lambda p: p.win_place)
                winner_text = []
                
                for i, winner in enumerate(winners, 1):
                    if i == 1:
                        winner_text.append(f"🥇 **{winner.user.mention}** - Kidnapper (1st place)")
                    else:
                        winner_text.append(f"{i}. {winner.user.mention}")
                
                embed.description = "🏆 **Game Over - Final Standings**\n" + "\n".join(winner_text)
            else:
                embed.description = "🎮 Game Over!"
            
            # Add game statistics
            embed.add_field(
                name="📊 Game Stats",
                value=f"⏱️ Game duration: {int(self.game.get_game_duration() // 60)}m {int(self.game.get_game_duration() % 60)}s",
                inline=False
            )
    
    def _get_ordinal_suffix(self, n):
        """Helper to get ordinal suffix (1st, 2nd, 3rd, etc.)"""
        if 11 <= (n % 100) <= 13:
            return 'th'
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        
    def create_embed(self):
        """Create a clean, organized embed for the game"""
        embed = discord.Embed(
            title=f"🎭 {self.game.jack_nickname} - Kidnapped Jack" if not self.game.game_over else f"🏁 Game Over - {self.game.jack_nickname}",
            color=discord.Color.red() if not self.game.game_over else discord.Color.green()
        )
        
        # Add game status based on game state
        if not self.game.game_started:
            # Lobby/join phase
            player_list = "\n".join([f"👤 {p.user.mention}" for p in self.game.players])
            embed.description = (
                f"🃏 **A game of Kidnapped Jack is starting!**\n"
                f"👥 Players: {len(self.game.players)}/{MAX_PLAYERS}\n"
                f"\n**Players Joined:**\n{player_list or 'No players yet!'}"
            )
            
            # Add game rules
            embed.add_field(
                name="🎯 How to Play",
                value=(
                    "1. Be the **first** to get rid of all your cards to win!\n"
                    "2. Take turns drawing cards from other players.\n"
                    "3. Make pairs to remove them from your hand.\n"
                    "4. Last player with cards loses as the Kidnapper!"
                ),
                inline=False
            )
            
            # Add join instructions
            embed.set_footer(text="🔵 Click 'Join Game' to play!")
            
        elif not self.game.game_over:
            # Game in progress
            current_player = self.game.get_current_player()
            turn_indicator = f"🎯 **{current_player.user.mention}'s Turn**\n👉 Choose a player to draw from below"
            embed.description = turn_indicator
            
            # Player status with card counts and visual indicators
            active_players = [p for p in self.game.players if not p.eliminated and len(p.hand) > 0]
            player_status = []
            
            if winner.is_kidnapper:
                label = f"💀 {winner.user.mention} - Kidnapper (Lost)"
            elif winner.win_place == 1:
                label = f"🏆 {winner.user.mention} - Winner (1st place)"
            else:
                suffix = self._get_ordinal_suffix(winner.win_place)
                label = f"🥈 {winner.user.mention} - {winner.win_place}{suffix} place"
                player_status.append(label) # in-progress block
                winner_text.append(label) # game-over block
                
            if active_players:
                player_status.append("\n**Still in the game:**")
            
            # Then show active players
            for player in self.game.players:
                if player.eliminated:
                    continue
                    
                if player == current_player:
                    status = f"🎯 {player.user.mention} ({len(player.hand)} cards) ⭐"
                else:
                    status = f"🂴 {player.user.mention} ({len(player.hand)} cards)"
                player_status.append(status)
            
            embed.add_field(
                name=f"👥 Player Status ({len(active_players)} active)",
                value="\n".join(player_status) or "No active players",
                inline=False
            )
            
            # Game progress with visual bar
            total_cards = sum(len(p.hand) for p in self.game.players)
            progress_bar = "█" * min(10, total_cards // 5) + "░" * (10 - min(10, total_cards // 5))
            embed.add_field(
                name="📈 Game Progress",
                value=f"```\n[{progress_bar}] {total_cards} cards left\n```",
                inline=False
            )
            
            # Add game rules reminder
            embed.add_field(
                name="🎯 Goal",
                value="Be the **first** to get eliminated to win as the Kidnapper!",
                inline=False
            )
            
            # Add recent actions if any
            if hasattr(self.game, 'game_history') and self.game.game_history:
                recent_actions = "\n".join(self.game.game_history[-3:])
                if len(self.game.game_history) > 3:
                    recent_actions = f"...\n{recent_actions}"
                
                embed.add_field(
                    name="📜 Recent Actions",
                    value=recent_actions,
                    inline=False
                )
            
            # Add footer with instructions
            embed.set_footer(text="🔵 Click on a player button to draw from them - Choose wisely!")
            
        else:  # Game over
            if hasattr(self.game, 'winners') and self.game.winners:
                # Sort winners by their placement
                winners = sorted(self.game.winners, key=lambda p: p.win_place)
                winner_text = []
                
                for i, winner in enumerate(winners, 1):
                    if winner.is_kidnapper:
                        winner_text.append(f"💀 {winner.user.mention} - Kidnapper (Lost)")
                    elif i == 1:
                        winner_text.append(f"🏆 {winner.user.mention} - Winner (1st place)")
                    else:
                        suffix = self._get_ordinal_suffix(i)
                        winner_text.append(f"{i}{suffix}. {winner.user.mention}")
                
                embed.description = "🏆 **Game Over - Final Standings**\n" + "\n".join(winner_text)
            else:
                embed.description = "🎮 Game Over!"
            
            # Add game statistics
            duration = self.game.get_game_duration()
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            total_players = len(self.game.players)
            
            # Add more varied tips and facts
            tips = [
                "🔍 Pro Tip: Keep track of which cards other players are collecting to predict their moves.",
                "🎲 Strategy: Try to get rid of high-value cards early to avoid being the last one holding them.",
                "🧠 Did You Know? The game gets more strategic with more players - try it with 5-6 players!",
                "⚡ Quick Tip: Pay attention to who's collecting which cards to avoid giving them a pair.",
                "🏆 Champion Move: The best players remember which cards have been played to make better decisions.",
                "🔄 Reminder: The first to get rid of all cards wins, while the last one becomes the Kidnapper!",
                "🤔 Think Ahead: Sometimes it's better to keep a card that's already been paired to block others.",
                "🎯 Expert Tip: Watch for players who are close to winning and try to block them.",
                "💡 Strategy: In the endgame, try to keep your hand size similar to others to avoid being targeted.",
                "🃏 Fun Fact: This game is actually adopted from the game 'Old Maid', but in some countries the game is altered with a twist!"
            ]
            
            # Select 3 random tips
            selected_tips = random.sample(tips, min(3, len(tips)))
            tips_text = "\n\n".join(selected_tips)
            embed.add_field(
                name="📊 Game Stats",
                value=f"⏱️ Game duration: {minutes}m {seconds}s",
                inline=False
            )
            
            # Add a fun fact or tip
            fun_facts = [
                "The Kidnapper wins by being the first to be eliminated!",
                "Did you know? The Kidnapper's goal is to get caught!",
                "Pro tip: Watch for players trying to get eliminated early!",
                "The best strategy changes based on how many players are left!",
                "Eliminating players with few cards first can be a good strategy!"
            ]
            
            embed.add_field(
                name="💡 Did You Know?",
                value=random.choice(fun_facts),
                inline=False
            )
            
            # Add footer with rematch instructions
            embed.set_footer(text="🔄 Click 'Rematch' to play again with the same players!")
        
        return embed

def setup(bot, supabase):
    @bot.tree.command(name="kidnapped-jack", description="Start a game of The Kidnapped Jack!")
    @app_commands.describe(
        jack_nickname="Custom nickname for the Jack of Hearts (optional)"
    )
    async def kidnapped_jack(interaction: discord.Interaction, jack_nickname: str = "Jack of Hearts"):
        # Check if user is already in a game
        if interaction.user.id in active_games:
            await interaction.response.send_message("❌ You're already in a game! Please finish your current game first.", ephemeral=True)
            return
        
        # Create new game
        host = KidnappedJackPlayer(interaction.user)
        game = KidnappedJackGame([host], jack_nickname)
        view = KidnappedJackView(game, supabase, interaction.channel, bot)
        
        # Add host to active games
        active_games[interaction.user.id] = game
        
        # Create embed
        embed = view.create_embed()
        
        # Send game message
        msg = await interaction.channel.send(embed=embed, view=view)
        view.message = msg
        
        await interaction.response.send_message(
            f"🎮 **The Kidnapped Jack** game created!\n"
            f"👑 Host: {interaction.user.mention}\n"
            f"🎴 {jack_nickname} is the target card!\n"
            f"📋 Other players can join by clicking the buttons below.",
            ephemeral=True
        )
    
    @bot.tree.command(name="kidnapped-jack-stats", description="Check your Kidnapped Jack stats")
    @app_commands.describe(member="The user to check stats for (optional)")
    async def kidnapped_jack_stats(interaction: discord.Interaction, member: discord.Member = None):
        target_user = member or interaction.user
        guild_id = interaction.guild_id
        
        try:
            stats = get_kidnapped_jack_stats(supabase, guild_id, str(target_user.id))
            
            if not stats:
                stats = {"games_played": 0, "escapes": 0, "kidnapper_count": 0}
            
            embed = discord.Embed(
                title=f"📊 {target_user.display_name}'s Kidnapped Jack Stats",
                color=discord.Color.purple()
            )
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            games_played = stats.get("games_played", 0)
            escapes = stats.get("escapes", 0)
            kidnapper_count = stats.get("kidnapper_count", 0)
            
            if games_played > 0:
                escape_rate = (escapes / games_played) * 100
                kidnapper_rate = (kidnapper_count / games_played) * 100
            else:
                escape_rate = 0
                kidnapper_rate = 0
            
            embed.add_field(
                name="🎮 Games Played",
                value=f"**{games_played}**",
                inline=True
            )
            embed.add_field(
                name="🏃 Escapes",
                value=f"**{escapes}** ({escape_rate:.1f}%)",
                inline=True
            )
            embed.add_field(
                name="😈 Times as Kidnapper",
                value=f"**{kidnapper_count}** ({kidnapper_rate:.1f}%)",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Failed to get Kidnapped Jack stats: {str(e)}")
            await interaction.response.send_message("⚠️ Could not retrieve stats due to an error.", ephemeral=True)
    
    @bot.tree.command(name="kidnapped-jack-lb", description="Show The Kidnapped Jack leaderboard")
    async def kidnapped_jack_leaderboard(interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = interaction.guild_id
        
        try:
            leaderboard_data = get_kidnapped_jack_leaderboard(supabase, guild_id, 10)
            
            if not leaderboard_data:
                await interaction.followup.send("No one has played The Kidnapped Jack yet!")
                return
            
            embed = discord.Embed(
                title="🃏 The Kidnapped Jack Leaderboard 🏆",
                description="Top 10 players ranked by escapes",
                color=discord.Color.purple()
            )
            
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            
            embed.set_author(name=interaction.guild.name)
            embed.set_footer(text=f"Requested by {interaction.user.name}")
            
            leaderboard_text = ""
            for i, player_data in enumerate(leaderboard_data, 1):
                user_id = int(player_data.get("user_id", "0"))
                member = interaction.guild.get_member(user_id)
                display_name = member.display_name if member else f"Unknown Player"
                
                games_played = player_data.get("games_played", 0)
                escapes = player_data.get("escapes", 0)
                kidnapper_count = player_data.get("kidnapper_count", 0)
                
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`#{i}`"
                
                leaderboard_text += f"**{medal} {display_name}**\n"
                leaderboard_text += f"┣ Escapes: **{escapes}** ┃ Games: **{games_played}**\n"
                leaderboard_text += f"┗ Kidnapper: **{kidnapper_count}** times\n\n"
            
            embed.description = f"Top 10 players ranked by escapes\n\n{leaderboard_text}"
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to get Kidnapped Jack leaderboard: {str(e)}")
            await interaction.followup.send("⚠️ Could not retrieve the leaderboard due to an error.") 