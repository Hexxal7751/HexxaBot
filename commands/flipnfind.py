import discord
import random
import asyncio
import logging
import time
from discord import app_commands
from utils.database import get_flipnfind_stats, update_flipnfind_stats, get_flipnfind_leaderboard, create_flipnfind_table
from collections import defaultdict

logger = logging.getLogger(__name__)

# Game state storage
active_games = {}

# Constants
GRID_SIZE = 4  # 4x4 grid = 8 pairs
CARD_EMOJIS = ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐵", "🐔", "🦄", "🐙", "🦉", "🦖", "🦕", "🦋", "🐲", "🦓", "🦒", "🦛", "🦘", "🦡", "🦦", "🦥", "🦨", "🦩", "🦚", "🦜", "🦢", "🦩", "🦚", "🦜"]
TURN_TIMEOUT = 30  # Increased for better UX
TIMED_MODE_DURATION = 90  # Increased for more fun
INVITE_TIMEOUT = 60
STAR_CARD_EMOJI = "⭐"

# Cooldown tracking
default_cooldowns = defaultdict(float)

# --- Only the relevant changes are shown below ---
# 1. Update constants and difficulty definitions
DIFFICULTY_CONFIG = {
    "easy": {"grid": 4, "timed": False, "time_limit": None},
    "medium": {"grid": 4, "timed": True, "time_limit": 90},
    "hard": {"grid": 5, "timed": False, "time_limit": None},
    "extreme": {"grid": 5, "timed": True, "time_limit": 120},
}

class FlipnFindGame:
    def __init__(self, p1, p2, difficulty="easy"):
        config = DIFFICULTY_CONFIG[difficulty]
        self.players = [p1, p2]
        self.scores = {p1.id: 0, p2.id: 0}
        self.star_cards = {p1.id: 0, p2.id: 0}
        self.current_player = p1
        self.difficulty = difficulty
        self.grid_size = config["grid"]
        self.timed = config["timed"]
        self.time_limit = config["time_limit"]
        self.winner = None
        self.running = True
        self.start_time = time.time()
        self.turns = 0
        self.board = self._create_board()
        self.first_selection = None
        self.is_processing = False
        self.last_action_desc = "The game has started!"

    def _create_board(self):
        total_cells = self.grid_size * self.grid_size
        pair_count = total_cells // 2
        emojis = random.sample(CARD_EMOJIS, pair_count) * 2
        # Only add star card in Hard/Extreme (5x5)
        if self.grid_size == 5:
            emojis.append(STAR_CARD_EMOJI)
        random.shuffle(emojis)
        board = []
        for r in range(self.grid_size):
            row = []
            for c in range(self.grid_size):
                emoji = emojis.pop()
                row.append({'emoji': emoji, 'revealed': False, 'matched': False, 'star_claimed': False})
            board.append(row)
        return board

    def flip_card(self, row, col):
        card = self.board[row][col]
        if card['revealed'] or card['matched'] or card.get('star_claimed', False):
            return None
        card['revealed'] = True
        # Only process star card in Hard/Extreme
        if self.grid_size == 5 and card['emoji'] == STAR_CARD_EMOJI:
            card['star_claimed'] = True
            self.star_cards[self.current_player.id] += 1
            self.last_action_desc = f"🌟 {self.current_player.mention} found the Star Card! Turn ends."
            return "star_card"
        if not self.first_selection:
            self.first_selection = (row, col)
            self.last_action_desc = f"{self.current_player.mention} flipped a card. What's the match?"
            return "first_card"
        else:
            self.turns += 1
            return self.check_match(row, col)

    def check_match(self, r2, c2):
        r1, c1 = self.first_selection
        card1 = self.board[r1][c1]
        card2 = self.board[r2][c2]
        if card1['emoji'] == card2['emoji']:
            card1['matched'] = True
            card2['matched'] = True
            self.scores[self.current_player.id] += 1
            self.first_selection = None
            self.last_action_desc = f"🎉 **Match found!** {self.current_player.mention} gets another turn."
            if self.is_game_over():
                self.end_game()
            return "match"
        else:
            self.last_action_desc = f"❌ **No match!** It's now the other player's turn."
            return "no_match"

    def hide_cards(self, r2, c2):
        r1, c1 = self.first_selection
        self.board[r1][c1]['revealed'] = False
        self.board[r2][c2]['revealed'] = False
        self.first_selection = None

    def next_turn(self):
        self.current_player = self.players[1] if self.current_player == self.players[0] else self.players[0]

    def is_game_over(self):
        for row in self.board:
            for card in row:
                if not card['matched'] and not card.get('star_claimed', False):
                    return False
        return True

    def end_game(self, reason="completed"):
        if not self.running: return
        self.running = False
        p1_score = self.scores[self.players[0].id]
        p2_score = self.scores[self.players[1].id]
        if p1_score > p2_score:
            self.winner = self.players[0]
        elif p2_score > p1_score:
            self.winner = self.players[1]
        else:
            self.winner = None

    def total_star_cards(self):
        return self.star_cards[self.players[0].id] + self.star_cards[self.players[1].id]

class FlipnFindView(discord.ui.View):
    def __init__(self, game: FlipnFindGame, supabase, channel, bot):
        super().__init__(timeout=None)
        self.game = game
        self.supabase = supabase
        self.channel = channel
        self.bot = bot
        self.message = None
        self._turn_event = asyncio.Event()
        self._turn_loop_task = asyncio.create_task(self.turn_loop())
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        for r in range(self.game.grid_size):
            for c in range(self.game.grid_size):
                button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="❓", row=r, custom_id=f"flip_{r}_{c}")
                button.callback = self.button_callback
                self.add_item(button)
        # Place the quit button on the last row
        quit_button = discord.ui.Button(label="Quit", style=discord.ButtonStyle.danger, row=self.game.grid_size if self.game.grid_size < 5 else 4, custom_id="quit")
        quit_button.callback = self.quit_callback
        self.add_item(quit_button)

    def _update_buttons_state(self, disable_all=False):
        for r in range(self.game.grid_size):
            for c in range(self.game.grid_size):
                idx = r * self.game.grid_size + c
                button = self.children[idx]
                card = self.game.board[r][c]
                if card['matched']:
                    button.style = discord.ButtonStyle.success
                    button.label = card['emoji']
                    button.disabled = True
                elif card['revealed']:
                    button.style = discord.ButtonStyle.primary
                    button.label = card['emoji']
                    button.disabled = True if disable_all else False
                else:
                    button.style = discord.ButtonStyle.secondary
                    button.label = "❓"
                    button.disabled = disable_all
        # Quit button is always enabled unless game is over
        self.children[-1].disabled = not self.game.running

    async def update_view(self, interaction: discord.Interaction = None, timeout_left=None, disable_all=False):
        embed = self.create_embed(timeout_left)
        self._update_buttons_state(disable_all=disable_all)
        try:
            if interaction and not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=self)
            elif self.message:
                await self.message.edit(embed=embed, view=self)
        except discord.NotFound:
            self.game.end_game("message_deleted")

    def create_embed(self, timeout_left=None):
        p1, p2 = self.game.players
        embed = discord.Embed(title="🎴 Flip & Find", color=discord.Color.blue())
        embed.description = self.game.last_action_desc
        if self.game.grid_size == 5:
            embed.add_field(name=f"__Player 1:__ {p1.display_name}", value=f"**Pairs: {self.game.scores[p1.id]}**\n🌟 Star Cards: {self.game.star_cards[p1.id]}", inline=True)
            embed.add_field(name=f"__Player 2:__ {p2.display_name}", value=f"**Pairs: {self.game.scores[p2.id]}**\n🌟 Star Cards: {self.game.star_cards[p2.id]}", inline=True)
        else:
            embed.add_field(name=f"__Player 1:__ {p1.display_name}", value=f"**Pairs: {self.game.scores[p1.id]}**", inline=True)
            embed.add_field(name=f"__Player 2:__ {p2.display_name}", value=f"**Pairs: {self.game.scores[p2.id]}**", inline=True)
        embed.add_field(name="Grid Size", value=f"{self.game.grid_size}x{self.game.grid_size}", inline=True)
        if self.game.running:
            embed.add_field(name="Current Turn", value=self.game.current_player.mention, inline=False)
            footer_text = f"Difficulty: {self.game.difficulty.title()} | Grid: {self.game.grid_size}x{self.game.grid_size}"
            if self.game.timed:
                footer_text += f" | Time Limit: {self.game.time_limit}s"
            if timeout_left is not None:
                footer_text += f" | Time left: {timeout_left}s ⏳"
            embed.set_footer(text=footer_text)
        else:
            if self.game.winner:
                embed.description = f"🎉 **{self.game.winner.mention} wins the game!**"
            else:
                embed.description = "🤝 **It's a tie!**"
            embed.color = discord.Color.gold()
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.game.current_player.id:
            return True
        elif interaction.data.get("custom_id") == "quit" and interaction.user.id in [p.id for p in self.game.players]:
            return True
        else:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return False

    async def turn_loop(self):
        # For Medium/Extreme, also start a total game timer
        total_timer_task = None
        if self.game.timed:
            total_timer_task = asyncio.create_task(self.total_game_timer())
        while self.game.running:
            self._turn_event.clear()
            timeout = 30  # 30s per turn
            try:
                await asyncio.wait_for(self._turn_event.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                if not self.game.running: break
                self.game.last_action_desc = f"⏰ {self.game.current_player.mention} ran out of time!"
                other_player = self.game.players[1] if self.game.current_player == self.game.players[0] else self.game.players[0]
                self.game.winner = other_player
                self.game.end_game("timeout")
                await self.finish_game()
                break
        if total_timer_task:
            total_timer_task.cancel()

    async def total_game_timer(self):
        # Only for Medium/Extreme
        await asyncio.sleep(self.game.time_limit)
        if not self.game.running:
            return
        # Time's up! Decide winner by pairs
        p1, p2 = self.game.players
        s1 = self.game.scores[p1.id]
        s2 = self.game.scores[p2.id]
        if s1 > s2:
            self.game.winner = p1
        elif s2 > s1:
            self.game.winner = p2
        else:
            self.game.winner = None
        self.game.last_action_desc = f"⏰ Total game time expired!"
        self.game.end_game("total_time")
        await self.finish_game()

    async def button_callback(self, interaction: discord.Interaction):
        if self.game.is_processing: return await interaction.response.send_message("Please wait...", ephemeral=True)
        self.game.is_processing = True
        custom_id = interaction.data["custom_id"]
        _, r_str, c_str = custom_id.split('_')
        r, c = int(r_str), int(c_str)
        result = self.game.flip_card(r, c)
        if result == "star_card":
            await self.update_view(interaction, disable_all=True)
            await asyncio.sleep(1.2)
            self.game.board[r][c]['revealed'] = False
            await self.update_view()
            self.game.next_turn()
            self._turn_event.set()
        elif result == "first_card":
            await self.update_view(interaction)
        elif result == "match":
            await self.update_view(interaction)
            if self.game.is_game_over():
                await self.finish_game()
        elif result == "no_match":
            await self.update_view(interaction, disable_all=True)
            await asyncio.sleep(1.5)
            self.game.hide_cards(r, c)
            self.game.next_turn()
            self._turn_event.set()
            await self.update_view()
        self.game.is_processing = False

    async def quit_callback(self, interaction: discord.Interaction):
        if interaction.user not in self.game.players:
            return await interaction.response.send_message("You are not in this game.", ephemeral=True)
        
        self.game.last_action_desc = f"🚫 {interaction.user.mention} has quit the game."
        self.game.winner = self.game.players[1] if interaction.user == self.game.players[0] else self.game.players[0]
        self.game.end_game("quit")
        await self.finish_game(interaction)

    async def finish_game(self, interaction: discord.Interaction = None):
        self._turn_loop_task.cancel()
        for child in self.children:
            child.disabled = True
        await self.update_view(interaction)
        guild_id = self.channel.guild.id
        game_time = time.time() - self.game.start_time
        p1 = self.game.players[0]
        p2 = self.game.players[1]
        create_flipnfind_table(self.supabase, guild_id)
        if self.game.winner:
            winner = self.game.winner
            loser = p2 if winner.id == p1.id else p1
            if not winner.bot:
                update_flipnfind_stats(self.supabase, guild_id, f"{winner.id}_{self.game.difficulty}", "win", game_time, self.game.turns, star_cards=self.game.star_cards[winner.id])
            if not loser.bot:
                update_flipnfind_stats(self.supabase, guild_id, f"{loser.id}_{self.game.difficulty}", "loss", game_time, self.game.turns, star_cards=self.game.star_cards[loser.id])
        else:
            if not p1.bot: update_flipnfind_stats(self.supabase, guild_id, f"{p1.id}_{self.game.difficulty}", "loss", game_time, self.game.turns, star_cards=self.game.star_cards[p1.id])
            if not p2.bot: update_flipnfind_stats(self.supabase, guild_id, f"{p2.id}_{self.game.difficulty}", "loss", game_time, self.game.turns, star_cards=self.game.star_cards[p2.id])
        active_games.pop(p1.id, None)
        active_games.pop(p2.id, None)

def setup(bot, supabase):
    @bot.tree.command(name="flipnfind", description="Play Flip & Find with another user!")
    @app_commands.describe(opponent="The user you want to play against", difficulty="Choose difficulty: Easy, Medium, Hard, Extreme")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Easy (4x4, untimed)", value="easy"),
        app_commands.Choice(name="Medium (4x4, 90s)", value="medium"),
        app_commands.Choice(name="Hard (5x5, untimed)", value="hard"),
        app_commands.Choice(name="Extreme (5x5, 120s)", value="extreme"),
    ])
    async def flipnfind(interaction: discord.Interaction, opponent: discord.Member, difficulty: app_commands.Choice[str] = None):
        if opponent.bot:
            await interaction.response.send_message("❌ You cannot play Flip & Find against bots (yet 😉). Please choose a human opponent.", ephemeral=True)
            return
        if opponent.id == interaction.user.id or interaction.user.id in active_games or opponent.id in active_games:
            await interaction.response.send_message("❌ Cannot start game. You or your opponent may already be in a game.", ephemeral=True)
            return
        chosen = difficulty.value if difficulty else "easy"
        config = DIFFICULTY_CONFIG[chosen]
        grid_size = config["grid"]
        time_limit = config["time_limit"]
        is_timed = config["timed"]
        channel = interaction.channel
        async def start_game():
            p1 = interaction.user
            p2 = opponent
            active_games[p1.id] = True
            active_games[p2.id] = True
            game = FlipnFindGame(p1, p2, chosen)
            view = FlipnFindView(game, supabase, channel, bot)
            msg = await channel.send(embed=view.create_embed(), view=view)
            view.message = msg
        if opponent.bot:
            await start_game()
        else:
            invite_view = discord.ui.View(timeout=INVITE_TIMEOUT)
            accepted = asyncio.Event()
            invite_expired = False
            async def accept_callback(ctx: discord.Interaction):
                if ctx.user.id != opponent.id:
                    return await ctx.response.send_message("This invite isn't for you!", ephemeral=True)
                for item in invite_view.children: item.disabled = True
                await ctx.response.edit_message(embed=invite_embed, view=invite_view)
                try:
                    await ctx.user.send(f"Starting challenge with {interaction.user.display_name}! Good luck! 🎴", silent=True)
                except Exception:
                    pass
                accepted.set()
            async def decline_callback(ctx: discord.Interaction):
                if ctx.user.id != opponent.id:
                    return await ctx.response.send_message("This invite isn't for you!", ephemeral=True)
                for item in invite_view.children: item.disabled = True
                await ctx.response.edit_message(content=f"{opponent.mention} declined the challenge.", embed=None, view=None)
                accepted.clear()
            accept_btn = discord.ui.Button(label="Accept", style=discord.ButtonStyle.success)
            decline_btn = discord.ui.Button(label="Decline", style=discord.ButtonStyle.danger)
            accept_btn.callback = accept_callback
            decline_btn.callback = decline_callback
            invite_view.add_item(accept_btn)
            invite_view.add_item(decline_btn)
            invite_embed = discord.Embed(
                title="🎴 Flip & Find Challenge!",
                description=(
                    f"**Challenger:** {interaction.user.mention}\n"
                    f"**Opponent:** {opponent.mention}\n"
                    f"**Difficulty:** {chosen.title()}\n"
                    f"**Grid Size:** {grid_size}x{grid_size}\n"
                    + (f"**Time Limit:** {time_limit}s\n" if is_timed else "") +
                    f"**Channel:** {channel.mention}\n\n"
                    f"You have {INVITE_TIMEOUT} seconds to accept or decline."
                ),
                color=discord.Color.orange()
            )
            invite_embed.set_footer(text="Click Accept to play, Decline to refuse.")
            try:
                await opponent.send(embed=invite_embed, view=invite_view)
                await interaction.response.send_message(f"✅ Invitation sent to {opponent.mention}'s DMs!", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message(f"⚠️ Couldn't DM {opponent.mention}. Sending invite in this channel.", embed=invite_embed, view=invite_view)
            try:
                await asyncio.wait_for(accepted.wait(), timeout=INVITE_TIMEOUT)
                if accepted.is_set():
                    await start_game()
            except asyncio.TimeoutError:
                invite_expired = True
                for item in invite_view.children: item.disabled = True
                await channel.send(f"⏰ {opponent.mention} did not respond in time. Challenge expired.")

    @bot.tree.command(name="flipnfind-stats", description="Check your Flip & Find stats")
    @app_commands.describe(member="The user to check stats for (optional)")
    async def flipnfind_stats(interaction: discord.Interaction, member: discord.Member = None):
        target_user = member or interaction.user
        guild_id = interaction.guild_id
        stats_by_diff = {}
        total = {"wins": 0, "losses": 0, "total_games": 0, "best_time": None, "best_turns": None, "star_cards": 0}
        for diff in DIFFICULTY_CONFIG.keys():
            stats = get_flipnfind_stats(supabase, guild_id, f"{target_user.id}_{diff}")
            stats_by_diff[diff] = stats or {"wins": 0, "losses": 0, "total_games": 0, "best_time": None, "best_turns": None, "star_cards": 0}
            total["wins"] += stats_by_diff[diff]["wins"]
            total["losses"] += stats_by_diff[diff]["losses"]
            total["total_games"] += stats_by_diff[diff]["total_games"]
            total["star_cards"] += stats_by_diff[diff].get("star_cards", 0)
            if stats_by_diff[diff]["best_time"] is not None:
                if total["best_time"] is None or stats_by_diff[diff]["best_time"] < total["best_time"]:
                    total["best_time"] = stats_by_diff[diff]["best_time"]
            if stats_by_diff[diff]["best_turns"] is not None:
                if total["best_turns"] is None or stats_by_diff[diff]["best_turns"] < total["best_turns"]:
                    total["best_turns"] = stats_by_diff[diff]["best_turns"]
        embed = discord.Embed(title=f"📊 {target_user.display_name}'s Flip & Find Stats", color=discord.Color.blue())
        embed.set_thumbnail(url=target_user.display_avatar.url)
        for diff, label in zip(DIFFICULTY_CONFIG.keys(), ["Easy", "Medium", "Hard", "Extreme"]):
            s = stats_by_diff[diff]
            if diff in ("hard", "extreme"):
                embed.add_field(name=f"{label}", value=f"🏆 Wins: {s['wins']}\n❌ Losses: {s['losses']}\n🎮 Games: {s['total_games']}\n🌟 Star Cards: {s.get('star_cards', 0)}\n" + (f"⚡ Best Time: {s['best_time']:.1f}s\n" if s['best_time'] else "") + (f"🎯 Best Turns: {s['best_turns']}" if s['best_turns'] else ""), inline=False)
            else:
                embed.add_field(name=f"{label}", value=f"🏆 Wins: {s['wins']}\n❌ Losses: {s['losses']}\n🎮 Games: {s['total_games']}\n" + (f"⚡ Best Time: {s['best_time']:.1f}s\n" if s['best_time'] else "") + (f"🎯 Best Turns: {s['best_turns']}" if s['best_turns'] else ""), inline=False)
        embed.add_field(name="Total", value=f"🏆 Wins: {total['wins']}\n❌ Losses: {total['losses']}\n🎮 Games: {total['total_games']}\n🌟 Star Cards: {total['star_cards']}\n" + (f"⚡ Best Time: {total['best_time']:.1f}s\n" if total['best_time'] else "") + (f"🎯 Best Turns: {total['best_turns']}" if total['best_turns'] else ""), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="flipnfind-lb", description="Show the Flip & Find leaderboard")
    async def flipnfind_leaderboard(interaction: discord.Interaction):
        await interaction.response.defer()
        leaderboard_data = get_flipnfind_leaderboard(supabase, interaction.guild_id, 10)
        if not leaderboard_data:
            return await interaction.followup.send("No one has played Flip & Find yet!")
        embed = discord.Embed(title="🎴 Flip & Find Leaderboard", color=discord.Color.gold())
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        lines = []
        for i, entry in enumerate(leaderboard_data):
            try:
                member = await interaction.guild.fetch_member(int(entry['user_id']))
                name = member.display_name
            except (discord.NotFound, discord.HTTPException):
                name = f"User ({entry['user_id'][-4:]})"
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"**#{i+1}**"
            lines.append(f"{medal} **{name}** — Wins: {entry.get('wins', 0)} | 🌟 Star Cards: {entry.get('star_cards', 0)}")
        embed.description = "\n".join(lines)
        await interaction.followup.send(embed=embed) 