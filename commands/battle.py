import discord
import random
import asyncio
import logging
import time
from discord import app_commands
from utils.database import get_battle_stats, update_battle_stats, get_battle_leaderboard
from collections import defaultdict

logger = logging.getLogger(__name__)

# Game state storage
active_battles = {}

# Constants
MAX_HP = 100
MAX_DEF = 5
MAX_HEALS = 3
HEAL_AMOUNT = 20
PUNCH_DAMAGE = 10
PUNCH_CRIT_DAMAGE = 20
KICK_DAMAGE = 20
KICK_CRIT_DAMAGE = 40
PUNCH_HIT_CHANCE = 0.8
PUNCH_CRIT_CHANCE = 0.2
KICK_HIT_CHANCE = 0.6
KICK_CRIT_CHANCE = 0.125
DEFEND_MIN = 1
DEFEND_MAX = 5
TURN_TIMEOUT = 20
POISON_AMOUNT = 5
REGEN_AMOUNT = 5
STUN_CHANCE = 0.25  # 25% chance to stun on attack

# Cooldown tracking
default_cooldowns = defaultdict(float)

# Custom messages
PUNCH_MESSAGES = [
    "👊 {attacker} lands a solid punch on {defender}!",
    "👊 {attacker} throws a quick jab at {defender}!",
    "👊 {attacker} swings a punch at {defender}!",
]
PUNCH_MISS_MESSAGES = [
    "👊 {attacker} swings and misses!",
    "👊 {attacker} tries to punch, but {defender} dodges!",
]
PUNCH_CRIT_MESSAGES = [
    "💥 {attacker} delivers a CRITICAL punch! Massive damage!",
    "💥 {attacker} lands a devastating critical punch on {defender}!",
]
KICK_MESSAGES = [
    "🦵 {attacker} kicks {defender} hard!",
    "🦵 {attacker} lands a strong kick on {defender}!",
]
KICK_MISS_MESSAGES = [
    "🦵 {attacker} tries to kick, but {defender} dodges!",
    "🦵 {attacker} misses the kick!",
]
KICK_CRIT_MESSAGES = [
    "🔥 {attacker} lands a devastating CRITICAL kick!",
    "🔥 {attacker} delivers a CRITICAL kick to {defender}!",
]
DEFEND_MESSAGES = [
    "🛡️ {player} braces for impact and increases their defense by {amount}!",
    "🛡️ {player} fortifies their stance, gaining {amount} defense!",
]
HEAL_MESSAGES = [
    "💚 {player} takes a breather and heals {amount} HP!",
    "💚 {player} patches up and recovers {amount} HP!",
]
RUN_MESSAGES = [
    "🏃 {player} flees the battlefield! {opponent} wins by default!",
    "🏃 {player} runs away! {opponent} claims victory!",
]
TIMEOUT_MESSAGES = [
    "⏰ {player} took too long! {opponent} wins by timeout!",
    "⏰ {player} was too slow! {opponent} wins by default!",
]
WIN_MESSAGES = [
    "🎉 {winner} is victorious!",
    "🏆 {winner} wins the battle!",
]
LOSE_MESSAGES = [
    "💀 {loser} has been defeated!",
    "😵 {loser} couldn't keep up!",
]

class BattlePlayer:
    def __init__(self, user, is_bot=False):
        self.user = user
        self.is_bot = is_bot
        self.hp = MAX_HP
        self.defense = 0
        self.heals = MAX_HEALS
        self.last_action = None
        self.last_action_result = None
        self.stunned = False  # For stun mode

    def is_alive(self):
        return self.hp > 0

    def heal(self):
        if self.heals > 0 and self.hp < MAX_HP:
            healed = min(HEAL_AMOUNT, MAX_HP - self.hp)
            self.hp += healed
            self.heals -= 1
            return healed
        return 0

    def defend(self):
        gain = random.randint(DEFEND_MIN, DEFEND_MAX)
        new_def = min(self.defense + gain, MAX_DEF)
        actual_gain = new_def - self.defense
        self.defense = new_def
        return actual_gain

    def take_damage(self, dmg, def_reduction):
        reduced = min(self.defense, dmg)
        dmg_taken = max(0, dmg - reduced)
        self.hp -= dmg_taken
        self.defense = max(0, self.defense - def_reduction)
        return dmg_taken, reduced

    def can_heal(self, gamemode):
        return self.heals > 0 and self.hp < MAX_HP and gamemode != "nohealing"

class BattleGame:
    def __init__(self, player1, player2, gamemode="normal"):
        self.players = [player1, player2]
        self.turn = 0  # 0 or 1
        self.gamemode = gamemode
        self.winner = None
        self.loser = None
        self.running = True
        self.timeout_task = None
        self.last_action_desc = ""
        self.last_action_result = ""
        self.turn_start_time = None
        self.history = []  # List of (desc, timestamp)

    def current(self):
        return self.players[self.turn]

    def opponent(self):
        return self.players[1 - self.turn]

    def next_turn(self):
        self.turn = 1 - self.turn
        self.turn_start_time = asyncio.get_event_loop().time()

    def is_over(self):
        return not all(p.is_alive() for p in self.players) or not self.running

    def end(self, winner, loser, reason="win"):
        self.winner = winner
        self.loser = loser
        self.running = False
        self.last_action_result = reason

    def get_status_embed(self, timeout_left=None):
        p1, p2 = self.players
        embed = discord.Embed(
            title="⚔️ Battle!",
            color=discord.Color.red() if self.is_over() else discord.Color.blurple()
        )
        def hp_bar(hp):
            hp = max(0, hp)  # Never show negative HP
            hearts = "❤️" * (hp // 10) + "🖤" * ((MAX_HP - hp) // 10)
            return f"{hearts} ({hp}/{MAX_HP})"
        def def_bar(defense):
            shields = "🛡️" * defense + "⚪" * (MAX_DEF - defense)
            return f"{shields} ({defense}/{MAX_DEF})"
        def heal_bar(heals):
            return f"{'💚' * heals}{'⬜' * (MAX_HEALS - heals)} ({heals}/{MAX_HEALS})"
        # Blind mode: only show current player's stats
        if self.gamemode == "blind":
            current = self.current()
            embed.add_field(name=f"{current.user.display_name}", value=f"HP: {hp_bar(current.hp)}\nDEF: {def_bar(current.defense)}\nHeals: {heal_bar(current.heals)}", inline=True)
            embed.add_field(name="Opponent", value="❓ Stats are hidden in Blind Mode!", inline=True)
        else:
            embed.add_field(name=f"{p1.user.display_name}", value=f"HP: {hp_bar(p1.hp)}\nDEF: {def_bar(p1.defense)}\nHeals: {heal_bar(p1.heals)}", inline=True)
            embed.add_field(name=f"{p2.user.display_name}", value=f"HP: {hp_bar(p2.hp)}\nDEF: {def_bar(p2.defense)}\nHeals: {heal_bar(p2.heals)}", inline=True)
        if self.is_over() and self.winner is not None and self.loser is not None:
            result_msg = random.choice(WIN_MESSAGES).format(winner=self.winner.user.mention) + "\n" + \
                         random.choice(LOSE_MESSAGES).format(loser=self.loser.user.mention) + "\n" + \
                         f"Reason: {self.last_action_result}"
            embed.add_field(name="Result", value=result_msg, inline=False)
            # Add stats
            embed.add_field(name="Stats", value=f"{self.winner.user.mention}: {getattr(self.winner, 'final_wins', '?')}W/{getattr(self.winner, 'final_losses', '?')}L\n{self.loser.user.mention}: {getattr(self.loser, 'final_wins', '?')}W/{getattr(self.loser, 'final_losses', '?')}L", inline=False)
        else:
            turn_text = f"It's {self.current().user.mention}'s turn!"
            if self.gamemode == "stun" and self.current().stunned:
                turn_text += " (Stunned, skips turn!)"
            embed.add_field(name="Turn", value=turn_text, inline=False)
            if timeout_left is not None:
                hourglasses = "⏳" * (timeout_left // 2)
                footer = f"{timeout_left}s left | {hourglasses}"
                if timeout_left <= 5:
                    footer += "  ⚠️ Hurry up!"
                embed.set_footer(text=footer)
        if self.last_action_desc:
            embed.description = self.last_action_desc
        # Add mode info
        if self.gamemode in ["poison", "regen", "stun", "blind"]:
            mode_desc = {
                "poison": "☠️ Poison Mode: Both players lose 5 HP after every turn.",
                "regen": "💧 Regen Mode: Both players heal 5 HP after every turn.",
                "stun": "⚡ Stun Mode: Attacks have a chance to stun the opponent (skip their next turn).",
                "blind": "👁️ Blind Mode: You can only see your own stats!"
            }[self.gamemode]
            embed.add_field(name="Game Mode", value=mode_desc, inline=False)
        return embed

class BattleView(discord.ui.View):
    def __init__(self, game, ctx, supabase, interaction, bot):
        super().__init__(timeout=None)
        self.game = game
        self.ctx = ctx
        self.supabase = supabase
        self.interaction = interaction
        self.bot = bot
        self.message = None
        self.turn_task = None
        self.timeout_left = TURN_TIMEOUT
        self.update_lock = asyncio.Lock()
        self.running = True
        self._timeout_task = None
        self._turn_event = asyncio.Event()
        self._turn_event.set()
        self._turn_loop_task = asyncio.create_task(self.turn_loop())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Allow both players to run away at any time
        if not self.game.running:
            await interaction.response.send_message("The battle is over!", ephemeral=True)
            return False
        # Only allow the current player to interact for other actions
        if interaction.data.get("custom_id", "").endswith("run"):
            if interaction.user.id not in [self.game.players[0].user.id, self.game.players[1].user.id]:
                await interaction.response.send_message("You're not a player in this game!", ephemeral=True)
                return False
            return True
        if interaction.user.id != self.game.current().user.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return False
        return True

    async def turn_loop(self):
        while self.game.running:
            self.timeout_left = TURN_TIMEOUT
            self._turn_event.clear()
            # Stun mode: skip turn if stunned
            if self.game.gamemode == "stun" and self.game.current().stunned:
                self.game.last_action_desc = f"⚡ {self.game.current().user.mention} is stunned and skips their turn!"
                self.game.current().stunned = False
                await self.update_message()
                await asyncio.sleep(1)
                self.game.next_turn()
                continue
            for i in range(TURN_TIMEOUT):
                await asyncio.sleep(1)
                self.timeout_left -= 1
                if not self.game.running:
                    return
                if self._turn_event.is_set():
                    break
                await self.update_message()
            if not self._turn_event.is_set() and self.game.running:
                # Timeout
                loser = self.game.current()
                winner = self.game.opponent()
                self.game.end(winner, loser, reason="timeout")
                await self.finish_battle()
                return
            await self.update_message()
            if self.game.is_over():
                await self.finish_battle()
                return
            # Bot turn if needed
            if self.game.current().is_bot and self.game.running:
                await asyncio.sleep(1) # Short delay for bot "thinking"
                await self.bot_turn()

    async def update_message(self):
        if self.message and self.running:
            try:
                await self.message.edit(embed=self.game.get_status_embed(timeout_left=self.timeout_left), view=self)
            except (discord.NotFound, discord.HTTPException) as e:
                logger.warning(f"Failed to update battle message: {e}")
                self.running = False # Stop loops if message is gone

    async def finish_battle(self):
        if not self.running:
            return
        self.running = False
        if self._turn_loop_task:
            self._turn_loop_task.cancel()
        for item in self.children:
            item.disabled = True
        await self.update_message()
        # Update stats
        guild_id = self.interaction.guild_id
        if self.game.winner and self.game.loser:
            update_battle_stats(self.supabase, guild_id, str(self.game.winner.user.id), "win")
            update_battle_stats(self.supabase, guild_id, str(self.game.loser.user.id), "loss")
            # Fetch updated stats for both players
            winner_stats = get_battle_stats(self.supabase, guild_id, str(self.game.winner.user.id))
            loser_stats = get_battle_stats(self.supabase, guild_id, str(self.game.loser.user.id))
            self.game.winner.final_wins = winner_stats["wins"] if winner_stats else "?"
            self.game.winner.final_losses = winner_stats["losses"] if winner_stats else "?"
            self.game.loser.final_wins = loser_stats["wins"] if loser_stats else "?"
            self.game.loser.final_losses = loser_stats["losses"] if loser_stats else "?"
        
        await self.update_message() # Final update with stats
        
        # Remove from active battles
        for p in self.game.players:
            active_battles.pop(p.user.id, None)

    async def bot_turn(self):
        if not self.game.running:
            return

        bot_player = self.game.current()
        is_main_bot = bot_player.user.id == self.bot.user.id

        # More advanced logic for the main bot
        if is_main_bot:
            # Heal if HP is below 20% and has heals
            if bot_player.hp < 20 and bot_player.can_heal(self.game.gamemode):
                await self.process_action("heal", None)
            # Defend if defense is low and HP is not critical
            elif bot_player.defense < 1 and bot_player.hp > 50:
                 await self.process_action("defend", None)
            # Otherwise, mostly attack
            else:
                action = random.choices(["punch", "kick"], weights=[0.6, 0.4], k=1)[0]
                await self.process_action(action, None)
        else: # Simple logic for other bots
            if bot_player.can_heal(self.game.gamemode) and bot_player.hp < 50 and random.random() < 0.7:
                await self.process_action("heal", None)
            else:
                action = random.choices(["punch", "kick", "defend"], [0.5, 0.3, 0.2])[0]
                await self.process_action(action, None)

    async def process_action(self, action, interaction):
        # Prevent further actions if game is over
        if self.game.is_over() or not self.running:
            if interaction:
                await interaction.response.send_message("The battle is already over!", ephemeral=True)
            return
        player = self.game.current()
        opp = self.game.opponent()
        desc = ""
        result = ""
        # Check if the current player is the main bot for boosted stats
        is_main_bot = player.is_bot and player.user.id == self.bot.user.id
        punch_crit_chance = PUNCH_CRIT_CHANCE * 2 if is_main_bot else PUNCH_CRIT_CHANCE
        kick_crit_chance = KICK_CRIT_CHANCE * 2 if is_main_bot else KICK_CRIT_CHANCE
        stunned = False
        if action == "punch":
            if random.random() < PUNCH_HIT_CHANCE:
                crit = random.random() < punch_crit_chance
                dmg = PUNCH_CRIT_DAMAGE if crit else PUNCH_DAMAGE
                def_red = 1
                dmg_taken, reduced = opp.take_damage(dmg, def_red)
                if crit:
                    desc = random.choice(PUNCH_CRIT_MESSAGES).format(attacker=player.user.mention, defender=opp.user.mention)
                else:
                    desc = random.choice(PUNCH_MESSAGES).format(attacker=player.user.mention, defender=opp.user.mention)
                # Stun mode: chance to stun
                if self.game.gamemode == "stun" and random.random() < STUN_CHANCE:
                    opp.stunned = True
                    desc += f"\n⚡ {opp.user.mention} is stunned and will skip their next turn!"
            else:
                desc = random.choice(PUNCH_MISS_MESSAGES).format(attacker=player.user.mention, defender=opp.user.mention)
        elif action == "kick":
            if random.random() < KICK_HIT_CHANCE:
                crit = random.random() < kick_crit_chance
                dmg = KICK_CRIT_DAMAGE if crit else KICK_DAMAGE
                def_red = 3
                dmg_taken, reduced = opp.take_damage(dmg, def_red)
                if crit:
                    desc = random.choice(KICK_CRIT_MESSAGES).format(attacker=player.user.mention, defender=opp.user.mention)
                else:
                    desc = random.choice(KICK_MESSAGES).format(attacker=player.user.mention, defender=opp.user.mention)
                # Stun mode: chance to stun
                if self.game.gamemode == "stun" and random.random() < STUN_CHANCE:
                    opp.stunned = True
                    desc += f"\n⚡ {opp.user.mention} is stunned and will skip their next turn!"
            else:
                desc = random.choice(KICK_MISS_MESSAGES).format(attacker=player.user.mention, defender=opp.user.mention)
        elif action == "defend":
            gain = player.defend()
            desc = random.choice(DEFEND_MESSAGES).format(player=player.user.mention, amount=gain)
        elif action == "heal":
            if self.game.gamemode == "nohealing":
                desc = f"❌ Healing is disabled in this gamemode!"
            elif player.heals > 0 and player.hp < MAX_HP:
                healed = player.heal()
                desc = random.choice(HEAL_MESSAGES).format(player=player.user.mention, amount=healed)
            else:
                desc = f"❌ No heals left or already at max HP!"
        elif action == "run":
            # Allow either player to run away at any time
            if interaction and interaction.user.id not in [self.game.players[0].user.id, self.game.players[1].user.id]:
                await interaction.response.send_message("You're not a player in this game!", ephemeral=True)
                return
            self.game.end(self.game.opponent(), player, reason=random.choice(RUN_MESSAGES).format(player=player.user.mention, opponent=opp.user.mention))
            desc = f"🏃 {player.user.mention} ran away! {opp.user.mention} wins!"
        self.game.last_action_desc = desc
        self.game.history.append((desc, time.time()))
        # Poison mode: lose HP after every turn
        if self.game.gamemode == "poison":
            for p in self.game.players:
                p.hp = max(0, p.hp - POISON_AMOUNT)
        # Regen mode: heal HP after every turn
        if self.game.gamemode == "regen":
            for p in self.game.players:
                p.hp = min(MAX_HP, p.hp + REGEN_AMOUNT)
        # Check for game over
        if not opp.is_alive():
            self.game.end(player, opp, reason="knockout")
        self._turn_event.set()
        # This needs to happen before finish_battle but after the event is set
        await self.update_message()
        if self.game.is_over():
            await self.finish_battle()
        else:
            self.game.next_turn()

    @discord.ui.button(label="👊 Punch", style=discord.ButtonStyle.primary)
    async def punch(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_action("punch", interaction)
        if not interaction.is_expired() and not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except Exception:
                pass

    @discord.ui.button(label="🦵 Kick", style=discord.ButtonStyle.primary)
    async def kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_action("kick", interaction)
        if not interaction.is_expired() and not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except Exception:
                pass

    @discord.ui.button(label="🛡️ Defend", style=discord.ButtonStyle.secondary)
    async def defend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_action("defend", interaction)
        if not interaction.is_expired() and not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except Exception:
                pass

    @discord.ui.button(label="💚 Heal", style=discord.ButtonStyle.success)
    async def heal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_action("heal", interaction)
        if not interaction.is_expired() and not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except Exception:
                pass

    @discord.ui.button(label="🏃 Run Away", style=discord.ButtonStyle.danger, custom_id="run")
    async def run(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_action("run", interaction)
        if not interaction.is_expired() and not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except Exception:
                pass

def setup(bot, supabase):
    @bot.tree.command(name="battle", description="Challenge another user or the bot to a battle!")
    @app_commands.describe(opponent="The user you want to battle", gamemode="Game mode: normal, nohealing, poison, blind, regen, stun")
    @app_commands.choices(gamemode=[
        app_commands.Choice(name="Normal", value="normal"),
        app_commands.Choice(name="No Healing", value="nohealing"),
        app_commands.Choice(name="Poison", value="poison"),
        app_commands.Choice(name="Blind", value="blind"),
        app_commands.Choice(name="Regen", value="regen"),
        app_commands.Choice(name="Stun", value="stun"),
    ])
    async def battle(interaction: discord.Interaction, opponent: discord.Member, gamemode: app_commands.Choice[str] = None):
        # Cooldown check
        now = time.time()
        if default_cooldowns[interaction.user.id] > now:
            wait = int(default_cooldowns[interaction.user.id] - now)
            await interaction.response.send_message(f"⏳ Please wait {wait}s before starting another battle.", ephemeral=True)
            return
        default_cooldowns[interaction.user.id] = now + 30
        gamemode_val = gamemode.value if gamemode else "normal"
        if opponent.id == interaction.user.id:
            await interaction.response.send_message("❌ You can't battle yourself!", ephemeral=True)
            return
        if interaction.user.id in active_battles or opponent.id in active_battles:
            await interaction.response.send_message("❌ One of the players is already in a battle!", ephemeral=True)
            return
        # Unified battle start for PvP and PvE
        is_bot_opponent = opponent.bot
        if is_bot_opponent:
            # Directly start the battle with the bot
            p1 = BattlePlayer(interaction.user)
            p2 = BattlePlayer(opponent, is_bot=True)
            game = BattleGame(p1, p2, gamemode=gamemode_val)
            active_battles[interaction.user.id] = game
            active_battles[opponent.id] = game # Also add bot to active battles
            view = BattleView(game, None, supabase, interaction, bot)
            await interaction.response.send_message(embed=game.get_status_embed(timeout_left=TURN_TIMEOUT), view=view)
            view.message = await interaction.original_response()
        else:
            # PvP: send challenge, wait for accept
            class BattleInviteView(discord.ui.View):
                def __init__(self, challenger, challenged, timeout=60):
                    super().__init__(timeout=timeout)
                    self.challenger = challenger
                    self.challenged = challenged
                    self.accepted = False
                    self.timed_out = False
                    self.responded = False
                @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
                async def accept(self, interaction2: discord.Interaction, button: discord.ui.Button):
                    if self.timed_out or self.responded:
                        await interaction2.response.send_message("This invitation has already expired or been responded to.", ephemeral=True)
                        return
                    if interaction2.user.id != self.challenged.id:
                        await interaction2.response.send_message("This invite isn't for you!", ephemeral=True)
                        return
                    self.accepted = True
                    self.responded = True
                    self.stop()
                    await interaction2.response.send_message("Battle accepted!", ephemeral=True)
                @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
                async def decline(self, interaction2: discord.Interaction, button: discord.ui.Button):
                    if self.timed_out or self.responded:
                        await interaction2.response.send_message("This invitation has already expired or been responded to.", ephemeral=True)
                        return
                    if interaction2.user.id != self.challenged.id:
                        await interaction2.response.send_message("This invite isn't for you!", ephemeral=True)
                        return
                    self.responded = True
                    self.stop()
                    await interaction2.response.send_message("Battle declined!", ephemeral=True)
            invite_view = BattleInviteView(interaction.user, opponent, timeout=60)
            # Build detailed embed
            embed = discord.Embed(
                title="⚔️ Battle Invitation!",
                description=f"You have been challenged to a battle!",
                color=discord.Color.orange()
            )
            embed.add_field(name="Challenger", value=interaction.user.mention, inline=True)
            embed.add_field(name="Match Type", value=f"{gamemode_val.title()}", inline=True)
            embed.add_field(name="Server", value=interaction.guild.name, inline=True)
            embed.add_field(name="Channel", value=interaction.channel.mention, inline=True)
            mode_desc = {
                "poison": "☠️ Poison Mode: Both players lose 5 HP after every turn.",
                "regen": "💧 Regen Mode: Both players heal 5 HP after every turn.",
                "stun": "⚡ Stun Mode: Attacks have a chance to stun the opponent (skip their next turn).",
                "blind": "👁️ Blind Mode: You can only see your own stats!",
                "nohealing": "🚫 No Healing: Healing is disabled.",
                "normal": "Standard battle rules."
            }.get(gamemode_val, "Standard battle rules.")
            embed.add_field(name="Game Mode", value=mode_desc, inline=False)
            embed.add_field(name="Instructions", value="Click **Accept** to start the battle, **Decline** to refuse. You have 60 seconds to respond.", inline=False)
            embed.set_footer(text=f"Battle started by {interaction.user.display_name}")
            # Try to send DM
            dm_sent = False
            try:
                dm_msg = await opponent.send(embed=embed, view=invite_view)
                dm_sent = True
                await interaction.response.send_message(f"✅ Battle invitation sent to {opponent.mention}'s DMs!", ephemeral=True)
            except discord.Forbidden:
                # DM failed, send in channel
                await interaction.response.send_message(f"⚠️ Couldn't DM {opponent.mention}. Sending invite here instead.", ephemeral=True)
                channel_msg = await interaction.channel.send(f"{opponent.mention}, you have been challenged to a battle by {interaction.user.mention}!", embed=embed, view=invite_view)
            # Wait for response or timeout
            await invite_view.wait()
            if invite_view.timed_out or not invite_view.accepted:
                # Timeout, declined, or cancelled
                if invite_view.timed_out:
                    timeout_msg = f"⏰ Battle invitation timed out. No response from {opponent.mention}."
                elif hasattr(invite_view, 'responded') and invite_view.responded:
                    timeout_msg = f"❌ Battle invitation was cancelled or declined."
                else:
                    timeout_msg = f"❌ {opponent.mention} declined the battle."
                if dm_sent:
                    try:
                        await opponent.send(timeout_msg)
                    except Exception:
                        pass
                await interaction.followup.send(timeout_msg, ephemeral=True)
                return
            # Accepted
            p1 = BattlePlayer(interaction.user)
            p2 = BattlePlayer(opponent)
            game = BattleGame(p1, p2, gamemode=gamemode_val)
            active_battles[interaction.user.id] = game
            active_battles[opponent.id] = game
            view = BattleView(game, None, supabase, interaction, bot)
            # Use followup for the message since we deferred for the invite
            msg = await interaction.followup.send(embed=game.get_status_embed(timeout_left=TURN_TIMEOUT), view=view, wait=True)
            view.message = msg

    @bot.tree.command(name="battle-lb", description="Show Battle game leaderboard")
    async def battle_leaderboard(interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = interaction.guild_id
        if not guild_id:
            await interaction.followup.send("This command can only be used in a server.")
            return
        try:
            leaderboard_data = get_battle_leaderboard(supabase, guild_id, 10)
            if not leaderboard_data:
                await interaction.followup.send("No one has played Battle yet!")
                return
            embed = discord.Embed(
                title="⚔️ Battle Leaderboard 🏆",
                description="Top 10 players ranked by wins",
                color=discord.Color.red()
            )
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            embed.set_author(name=interaction.guild.name)
            embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            leaderboard_text = ""
            bot_marks = set()
            for i, player_data in enumerate(leaderboard_data, 1):
                user_id = int(player_data.get("user_id", "0"))
                member = interaction.guild.get_member(user_id)
                is_bot = member.bot if member else False
                display_name = member.display_name if member else f"Unknown Player"
                wins = player_data.get("wins", 0)
                losses = player_data.get("losses", 0)
                total = player_data.get("total_games", 0)
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`#{i}`"
                mark = " 🤖" if is_bot else ""
                if is_bot:
                    bot_marks.add(i)
                leaderboard_text += f"**{medal} {display_name}{mark}**\n"
                leaderboard_text += f"┣ Wins: **{wins}** ┃ Losses: **{losses}**\n"
                leaderboard_text += f"┗ Total Games: **{total}**\n\n"
            embed.description = f"Top 10 players ranked by wins\n\n{leaderboard_text}"
            if bot_marks:
                bot_indices = ", ".join(f"#{idx}" for idx in sorted(bot_marks))
                embed.add_field(name="Bot Players", value=f"Players marked with 🤖 are bots.", inline=False)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to get Battle leaderboard: {str(e)}")
            await interaction.followup.send("⚠️ Could not retrieve the leaderboard due to an error.") 