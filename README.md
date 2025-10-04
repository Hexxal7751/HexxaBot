# HexxaBot V6 🎮

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/Hexxal7751/HexxaBot)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/Discord.py-2.5.0+-green.svg)](https://discordpy.readthedocs.io/)
[![Supabase](https://img.shields.io/badge/Supabase-Database-orange.svg)](https://supabase.com/)
[![Version](https://img.shields.io/badge/Version-6.0.0-purple.svg)](https://github.com/Hexxal7751/HexxaBot/releases)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://hexxabot.onrender.com)

A feature-rich Discord bot with multiple mini-games, utilities, and comprehensive stats tracking. Built with Discord.py and Supabase for robust data persistence.

Read the online guide: https://hexxabot.netlify.app/guide

## 🚀 Features

[![Games](https://img.shields.io/badge/Games-6%20Mini--Games-red.svg)](https://github.com/Hexxal7751/HexxaBot#games-available)
[![Stats](https://img.shields.io/badge/Stats-Tracking-blue.svg)](https://github.com/Hexxal7751/HexxaBot#stats--leaderboards)
[![UI](https://img.shields.io/badge/UI-Interactive-green.svg)](https://github.com/Hexxal7751/HexxaBot#games-available)
[![Database](https://img.shields.io/badge/Database-Supabase-orange.svg)](https://supabase.com/)
[![Multi-Server](https://img.shields.io/badge/Multi--Server-Support-purple.svg)](https://github.com/Hexxal7751/HexxaBot#setup-instructions)
[![Admin](https://img.shields.io/badge/Admin-Tools-yellow.svg)](https://github.com/Hexxal7751/HexxaBot#admin-commands)

- **6 Mini-Games** with full stats tracking and leaderboards
- **Interactive UI** with buttons and real-time updates
- **Database Integration** with Supabase for persistent stats
- **Admin Tools** for server management
- **Utility Commands** for server information and fun activities
- **Multi-Server Support** with automatic table creation
- **Job System** with interactive interviews and timed challenges
- **Economy & Banking** with rebalanced `/work`, streaks, and payouts

## 🎮 Games Available

### 🃏 The Kidnapped Jack
[![Card Game](https://img.shields.io/badge/Card%20Game-Old%20Maid%20Variant-red.svg)](https://github.com/Hexxal7751/HexxaBot#-the-kidnapped-jack)
[![Players](https://img.shields.io/badge/Players-2--8-green.svg)](https://github.com/Hexxal7751/HexxaBot#-the-kidnapped-jack)
[![Stats](https://img.shields.io/badge/Stats-Tracked-blue.svg)](https://github.com/Hexxal7751/HexxaBot#-the-kidnapped-jack)

A strategic card game based on "Old Maid" where players try to avoid being left with the Jack of Hearts!

**How to Play:**
- 49 cards (standard deck minus 3 Jacks, keeping only Jack of Hearts)
- Players draw cards from each other and remove pairs
- Last player with the Jack of Hearts becomes "The Kidnapper"
- Custom nicknames for the Jack of Hearts add personality

**Commands:**
- `/kidnapped-jack [nickname]` - Start a new game (2-8 players)
- `/kidnapped-jack-stats [member]` - Check your or another player's stats
- `/kidnapped-jack-lb` - View the leaderboard

**Stats Tracked:**
- Games played, escapes, times as kidnapper
- Best game times and total play time

---

### ⚔️ Battle
[![Combat](https://img.shields.io/badge/Combat-Turn--Based-red.svg)](https://github.com/Hexxal7751/HexxaBot#-battle)
[![Modes](https://img.shields.io/badge/Modes-6%20Game%20Modes-green.svg)](https://github.com/Hexxal7751/HexxaBot#-battle)
[![Actions](https://img.shields.io/badge/Actions-5%20Combat%20Actions-blue.svg)](https://github.com/Hexxal7751/HexxaBot#-battle)
[![Strategy](https://img.shields.io/badge/Strategy-Deep%20Tactics-purple.svg)](https://github.com/Hexxal7751/HexxaBot#-battle)

Epic turn-based combat system with multiple game modes and strategic depth!

**Game Modes:**
- **Normal**: Standard battle with healing
- **No Healing**: Disabled healing for intense combat
- **Poison**: Both players lose 5 HP per turn
- **Blind**: Only see your own stats
- **Regen**: Both players heal 5 HP per turn
- **Stun**: Attacks can stun opponents (skip their turn)

**Actions Available:**
- 👊 **Punch**: 80% hit chance, 10 damage, 1 defense reduction
- 🦵 **Kick**: 60% hit chance, 20 damage, 3 defense reduction
- 🛡️ **Defend**: Gain 1-5 defense points
- 💚 **Heal**: Restore 20 HP (3 uses, disabled in No Healing mode)
- 🏃 **Run Away**: Surrender the battle

**Commands:**
- `/battle [opponent] [gamemode]` - Challenge someone to battle
- `/battle-lb` - View battle leaderboard

**Stats Tracked:**
- Wins, losses, total games
- Win rates and battle history

---

### 🎴 Flip & Find
[![Memory](https://img.shields.io/badge/Memory-Card%20Matching-red.svg)](https://github.com/Hexxal7751/HexxaBot#-flip--find)
[![Difficulty](https://img.shields.io/badge/Difficulty-4%20Levels-green.svg)](https://github.com/Hexxal7751/HexxaBot#-flip--find)
[![Star Cards](https://img.shields.io/badge/Star%20Cards-Special%20Items-blue.svg)](https://github.com/Hexxal7751/HexxaBot#-flip--find)
[![Timed](https://img.shields.io/badge/Timed-Modes%20Available-purple.svg)](https://github.com/Hexxal7751/HexxaBot#-flip--find)

Memory card matching game with multiple difficulties and special mechanics!

**Difficulties:**
- **Easy**: 4x4 grid, untimed, 8 pairs
- **Medium**: 4x4 grid, 90-second time limit, 8 pairs
- **Hard**: 5x5 grid, untimed, 12 pairs + 1 Star Card
- **Extreme**: 5x5 grid, 120-second time limit, 12 pairs + 1 Star Card

**Special Features:**
- ⭐ **Star Cards**: In Hard/Extreme modes, find the special star card for bonus points
- **Turn-based**: Players take turns flipping cards
- **Real-time**: Live updates and animations

**Commands:**
- `/flipnfind [opponent] [difficulty]` - Start a memory game
- `/flipnfind-stats [member]` - Check your stats by difficulty
- `/flipnfind-lb` - View leaderboard

**Stats Tracked:**
- Wins/losses per difficulty
- Best completion times and turn counts
- Star cards collected

---

### 🎮 Tic Tac Toe
[![Classic](https://img.shields.io/badge/Classic-X%27s%20%26%20O%27s-red.svg)](https://github.com/Hexxal7751/HexxaBot#-tic-tac-toe)
[![Interactive](https://img.shields.io/badge/Interactive-Button%20Grid-green.svg)](https://github.com/Hexxal7751/HexxaBot#-tic-tac-toe)
[![AI](https://img.shields.io/badge/AI-Bot%20Opponents-blue.svg)](https://github.com/Hexxal7751/HexxaBot#-tic-tac-toe)
[![Real-time](https://img.shields.io/badge/Real--time-Updates-purple.svg)](https://github.com/Hexxal7751/HexxaBot#-tic-tac-toe)

Classic X's and O's with modern Discord integration!

**Features:**
- Interactive 3x3 grid with buttons
- Turn timers and game timeouts
- Bot opponents with AI
- Real-time game state updates

**Commands:**
- `/tictactoe [opponent]` - Challenge someone to Tic Tac Toe
- `/tictactoe-stats [member]` - Check your stats
- `/tictactoe-lb` - View leaderboard

**Stats Tracked:**
- Wins, losses, draws
- Total games played

---

### 🎲 Rock Paper Scissors
[![Quick](https://img.shields.io/badge/Quick-Instant%20Play-red.svg)](https://github.com/Hexxal7751/HexxaBot#-rock-paper-scissors)
[![Simple](https://img.shields.io/badge/Simple-Easy%20to%20Learn-green.svg)](https://github.com/Hexxal7751/HexxaBot#-rock-paper-scissors)
[![Emoji](https://img.shields.io/badge/Emoji-Reactions-blue.svg)](https://github.com/Hexxal7751/HexxaBot#-rock-paper-scissors)
[![Leaderboard](https://img.shields.io/badge/Leaderboard-Rankings-purple.svg)](https://github.com/Hexxal7751/HexxaBot#-rock-paper-scissors)

Quick and simple RPS with stats tracking!

**Features:**
- Instant results with emoji reactions
- Win/loss tracking
- Leaderboard rankings

**Commands:**
- `/rps [choice]` - Play Rock Paper Scissors
- `/rps-stats [member]` - Check your stats
- `/rps-lb` - View leaderboard

**Choices:**
- 🪨 Rock
- 📄 Paper
- ✂️ Scissors

**Stats Tracked:**
- Wins, losses, ties
- Total games played

---

### 🔢 Guess Number
[![Logic](https://img.shields.io/badge/Logic-Number%20Guessing-red.svg)](https://github.com/Hexxal7751/HexxaBot#-guess-number)
[![Hints](https://img.shields.io/badge/Hints-Higher%2FLower-green.svg)](https://github.com/Hexxal7751/HexxaBot#-guess-number)
[![Attempts](https://img.shields.io/badge/Attempts-10%20Tries-blue.svg)](https://github.com/Hexxal7751/HexxaBot#-guess-number)
[![Patterns](https://img.shields.io/badge/Patterns-Tracking-purple.svg)](https://github.com/Hexxal7751/HexxaBot#-guess-number)

Number guessing game with hints and statistics!

**How to Play:**
- Bot picks a random number 1-100
- You have 10 attempts to guess
- Get hints (higher/lower) after each guess
- Track your guessing patterns

**Commands:**
- `/guess-num` - Start a new guessing game
- `/guess-num-stats [member]` - Check your stats
- `/guess-num-lb` - View leaderboard

**Stats Tracked:**
- Correct/incorrect guesses
- Guess patterns and gaps
- Total games played

---

## 🛠️ Utility Commands

[![Info](https://img.shields.io/badge/Info-Commands-blue.svg)](https://github.com/Hexxal7751/HexxaBot#information-commands)
[![Fun](https://img.shields.io/badge/Fun-Commands-green.svg)](https://github.com/Hexxal7751/HexxaBot#fun-commands)
[![Admin](https://img.shields.io/badge/Admin-Commands-red.svg)](https://github.com/Hexxal7751/HexxaBot#admin-commands)
[![Math](https://img.shields.io/badge/Math-Calculator-orange.svg)](https://github.com/Hexxal7751/HexxaBot#fun-commands)
[![Dice](https://img.shields.io/badge/Dice-Rolling-purple.svg)](https://github.com/Hexxal7751/HexxaBot#fun-commands)

### Information Commands
- `/ping` - Check bot latency and response time
- `/hey` - Say hello to the bot
- `/serverinfo` - Detailed server statistics and information
- `/userinfo [member]` - Comprehensive user profile and statistics

### Fun Commands
- `/math [operation] [a] [b]` - Basic arithmetic (add, subtract, multiply, divide)
- `/diceroll [dice] [modifier]` - Roll dice with notation (e.g., "2d20+5")
- `/coinflip` - Flip a coin with animation

### Admin Commands
- `/purge-data` - Remove data for users who left the server (Admin only)

---

## 📊 Stats & Leaderboards

[![Stats](https://img.shields.io/badge/Stats-Comprehensive%20Tracking-blue.svg)](https://github.com/Hexxal7751/HexxaBot#stats--leaderboards)
[![Leaderboards](https://img.shields.io/badge/Leaderboards-Top%2010-red.svg)](https://github.com/Hexxal7751/HexxaBot#stats--leaderboards)
[![Privacy](https://img.shields.io/badge/Privacy-User%20Control-green.svg)](https://github.com/Hexxal7751/HexxaBot#stats--leaderboards)
[![Server](https://img.shields.io/badge/Server-Specific-orange.svg)](https://github.com/Hexxal7751/HexxaBot#stats--leaderboards)

Every game includes comprehensive statistics tracking:

### Individual Stats
- **Games Played**: Total number of games
- **Win/Loss Records**: Performance tracking
- **Best Times**: Fastest completion times
- **Special Achievements**: Unique accomplishments per game

### Leaderboards
- **Server-specific**: Each server has its own leaderboard
- **Top 10 Rankings**: See the best players
- **Multiple Categories**: Different ranking criteria per game

### Data Management
- **Automatic Cleanup**: Remove data for users who leave
- **Privacy Focused**: Only track game-related statistics
- **Admin Controls**: Server administrators can manage data

---

## 🚀 Setup Instructions

[![Setup](https://img.shields.io/badge/Setup-Easy%20Installation-green.svg)](https://github.com/Hexxal7751/HexxaBot#setup-instructions)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Discord](https://img.shields.io/badge/Discord-Bot%20Token-purple.svg)](https://discord.com/developers/applications)
[![Supabase](https://img.shields.io/badge/Supabase-Database-orange.svg)](https://supabase.com/)
[![Dependencies](https://img.shields.io/badge/Dependencies-Auto%20Install-red.svg)](https://github.com/Hexxal7751/HexxaBot#setup-instructions)

### Prerequisites
- Python 3.8 or higher
- Discord Bot Token
- Supabase Account and Project

### 1. Clone the Repository
```bash
git clone <repository-url>
cd HexxaBot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
DISCORD_TOKEN=your_discord_bot_token_here
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_service_role_key_here
```

### 4. Discord Bot Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Create a bot and copy the token
5. Enable required intents:
   - Server Members Intent
   - Message Content Intent
6. Generate invite link with permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Read Message History

### 5. Supabase Setup
1. Create a new project at [Supabase](https://supabase.com)
2. Go to Settings → API
3. Copy the Project URL and Service Role Key
4. Go to SQL Editor
5. Run the SQL from `sql/initial.sql` to create the database tables

### 6. Run the Bot
```bash
python bot.py
```

### 7. Verify Installation
- Bot should appear online in Discord
- Slash commands should be available
- Check bot logs for any errors

---

## 📁 Project Structure

```
HexxaBot V6/
├── bot.py                 # Main bot file
├── commands/              # Game and utility commands
│   ├── __init__.py
│   ├── basic.py          # Utility commands
│   ├── job.py            # Job system & economy (/job, /work)
│   ├── moderation.py     # Moderation & data purge
│   ├── battle.py         # Battle game
│   ├── flipnfind.py      # Flip & Find game
│   ├── guess_number.py   # Guess Number game
│   ├── kidnapped_jack.py # The Kidnapped Jack game
│   ├── rps.py            # Rock Paper Scissors
│   └── tictactoe.py      # Tic Tac Toe game
├── utils/
│   ├── __init__.py
│   └── database.py       # Database functions
├── sql/
│   ├── initial.sql       # Database setup
│   ├── grant.sql         # Permissions
│   └── revoke.sql        # Permission removal
├── templates/
│   └── status_index_root.html
├── keep_alive.py         # Keeps bot running
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

---

## 🔧 Technical Details

[![Architecture](https://img.shields.io/badge/Architecture-Modular-blue.svg)](https://github.com/Hexxal7751/HexxaBot#technical-details)
[![Database](https://img.shields.io/badge/Database-PostgreSQL-orange.svg)](https://supabase.com/)
[![API](https://img.shields.io/badge/API-Discord.py-green.svg)](https://discordpy.readthedocs.io/)
[![Security](https://img.shields.io/badge/Security-Best%20Practices-red.svg)](https://github.com/Hexxal7751/HexxaBot#security--privacy)
[![Performance](https://img.shields.io/badge/Performance-Optimized-purple.svg)](https://github.com/Hexxal7751/HexxaBot#technical-details)

### Dependencies
- **discord.py**: Discord API wrapper
- **supabase**: Database client
- **python-dotenv**: Environment variable management
- **Flask**: Web server for keep-alive functionality

### Database Schema
Each game has its own stats table per server:
- `rps_stats_{guild_id}`
- `guess_number_stats_{guild_id}`
- `tictactoe_stats_{guild_id}`
- `battle_stats_{guild_id}`
- `flipnfind_stats_{guild_id}`
- `kidnapped_jack_stats_{guild_id}`

### Bot Intents
- **Server Members**: Required for user management
- **Message Content**: Required for command processing

### Command Structure
All commands use Discord's slash command system with:
- Proper parameter validation
- Error handling and logging
- Ephemeral responses for privacy
- Interactive UI components

---

## 🛡️ Security & Privacy

[![Security](https://img.shields.io/badge/Security-Protected-red.svg)](https://github.com/Hexxal7751/HexxaBot#security--privacy)
[![Privacy](https://img.shields.io/badge/Privacy-First-green.svg)](https://github.com/Hexxal7751/HexxaBot#security--privacy)
[![GDPR](https://img.shields.io/badge/GDPR-Compliant-blue.svg)](https://github.com/Hexxal7751/HexxaBot#security--privacy)
[![Data](https://img.shields.io/badge/Data-Minimal%20Collection-orange.svg)](https://github.com/Hexxal7751/HexxaBot#security--privacy)
[![Isolation](https://img.shields.io/badge/Isolation-Server%20Specific-purple.svg)](https://github.com/Hexxal7751/HexxaBot#security--privacy)

### Data Protection
- **Minimal Data Collection**: Only game-related statistics
- **Server Isolation**: Data is separated by server
- **User Control**: Users can check their own data
- **Admin Controls**: Server admins can manage data

### Permissions
- **Least Privilege**: Bot only requests necessary permissions
- **Admin Commands**: Restricted to server administrators
- **User Privacy**: Personal stats are private by default

---

## 🐛 Troubleshooting

[![Support](https://img.shields.io/badge/Support-Help%20Available-blue.svg)](https://github.com/Hexxal7751/HexxaBot#troubleshooting)
[![Issues](https://img.shields.io/badge/Issues-Common%20Solutions-green.svg)](https://github.com/Hexxal7751/HexxaBot#troubleshooting)
[![Debug](https://img.shields.io/badge/Debug-Logging-red.svg)](https://github.com/Hexxal7751/HexxaBot#troubleshooting)
[![Setup](https://img.shields.io/badge/Setup-Verification-orange.svg)](https://github.com/Hexxal7751/HexxaBot#troubleshooting)

### Common Issues

**Bot not responding to commands:**
- Check if bot has proper permissions
- Verify slash commands are synced
- Check bot logs for errors

**Database connection issues:**
- Verify Supabase credentials
- Check network connectivity
- Ensure SQL tables are created

**Games not working:**
- Check if all dependencies are installed
- Verify bot has message permissions
- Check for any error messages in logs

### Getting Help
1. Check the bot logs for error messages
2. Verify all setup steps are completed
3. Ensure environment variables are correct
4. Check Discord and Supabase documentation

---

## 📈 Future Features

[![Roadmap](https://img.shields.io/badge/Roadmap-Active%20Development-blue.svg)](https://github.com/Hexxal7751/HexxaBot#future-features)
[![Features](https://img.shields.io/badge/Features-Planned-green.svg)](https://github.com/Hexxal7751/HexxaBot#future-features)
[![Tournaments](https://img.shields.io/badge/Tournaments-Coming%20Soon-red.svg)](https://github.com/Hexxal7751/HexxaBot#future-features)
[![Analytics](https://img.shields.io/badge/Analytics-Advanced%20Stats-orange.svg)](https://github.com/Hexxal7751/HexxaBot#future-features)
[![Mobile](https://img.shields.io/badge/Mobile-Web%20Dashboard-purple.svg)](https://github.com/Hexxal7751/HexxaBot#future-features)

- [ ] Additional game modes for existing games
- [ ] Tournament system
- [ ] Custom game settings
- [ ] Advanced statistics and analytics
- [ ] Integration with other Discord bots
- [ ] Mobile-friendly web dashboard

---

## 🤝 Contributing

[![Contributions](https://img.shields.io/badge/Contributions-Welcome-green.svg)](https://github.com/Hexxal7751/HexxaBot#contributing)
[![PRs](https://img.shields.io/badge/PRs-Welcome-blue.svg)](https://github.com/Hexxal7751/HexxaBot/pulls)
[![Issues](https://img.shields.io/badge/Issues-Welcome-red.svg)](https://github.com/Hexxal7751/HexxaBot/issues)
[![Code](https://img.shields.io/badge/Code-Quality-orange.svg)](https://github.com/Hexxal7751/HexxaBot#contributing)
[![Testing](https://img.shields.io/badge/Testing-Required-purple.svg)](https://github.com/Hexxal7751/HexxaBot#contributing)

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Open Source](https://img.shields.io/badge/Open%20Source-Yes-green.svg)](https://github.com/Hexxal7751/HexxaBot)
[![Free](https://img.shields.io/badge/Free-Forever-blue.svg)](https://github.com/Hexxal7751/HexxaBot)

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

[![Discord.py](https://img.shields.io/badge/Discord.py-Community-blue.svg)](https://discordpy.readthedocs.io/)
[![Supabase](https://img.shields.io/badge/Supabase-Team-orange.svg)](https://supabase.com/)
[![Contributors](https://img.shields.io/badge/Contributors-Thank%20You-green.svg)](https://github.com/Hexxal7751/HexxaBot/graphs/contributors)
[![Users](https://img.shields.io/badge/Users-Awesome-purple.svg)](https://github.com/Hexxal7751/HexxaBot)

- Discord.py community for the excellent library
- Supabase team for the powerful backend platform
- All contributors and users of HexxaBot

---

**Made with ❤️ for the Discord community**

---

## ✅ Quick Start (TL;DR)

1) Create `.env` in project root:

```env
DISCORD_TOKEN=your_discord_bot_token
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key
```

2) Install deps and run:

```bash
pip install -r requirements.txt
python bot.py
```

3) In Supabase SQL Editor, run the contents of `sql/initial.sql` (and see the Supabase section below for optional grant/revoke helpers).

---

## 🗄️ Supabase: Schema, RLS, and Policies

This bot uses per-guild tables created on demand by `create_guild_tables(guild_id)` defined in `sql/initial.sql`. Each game has its own `..._stats_{guild_id}` table, e.g. `rps_stats_1234567890`.

- Run `sql/initial.sql` once in Supabase SQL Editor to install the function and enable RLS with a permissive authenticated policy for each table.
- Optionally use `sql/grant.sql` and `sql/revoke.sql` to temporarily grant/revoke CREATE on `public` to `service_role` during migrations.

Important notes:

- The bot uses the Supabase Service Role key (`SUPABASE_KEY`). Treat it like a server secret. Do not expose it to clients or front-ends.
- RLS policies in `initial.sql` are permissive for the `authenticated` role to simplify server access. Since the bot uses the service role, it can bypass RLS, but keeping RLS enabled is still a good baseline for safety.
- Tables are created per guild the bot joins via `create_server_tables()` in `utils/database.py`, called from `on_ready` and `on_guild_join` in `bot.py`.

---

## 🔐 Security Hardening Checklist

- Bot permissions/intents in `bot.py`:
  - `Intents.members = True` and `Intents.message_content = True` are required for features and moderation. Only enable what you need in your application settings.
- Tokens and keys:
  - Keep `.env` out of version control (already in `.gitignore`).
  - Rotate `DISCORD_TOKEN` and `SUPABASE_KEY` if leaked.
- Supabase:
  - Never ship the service role key to a public front-end.
  - Consider restricting database network access (if using VPC/IP allowlists) and relying on server-side access only.
- Rate limiting & abuse:
  - Consider adding `app_commands.checks.cooldown` on high-traffic commands.
  - For message content features, validate and sanitize inputs before DB writes.
- Moderation cleanup (`/purge-data` in `commands/moderation.py`):
  - Uses `guild.fetch_member()` to verify membership accurately before deleting rows.
  - Requires Admin; modal confirmation required. Good defense against accidental deletion.

---

## 🧰 Developer Guide

- Commands are modular under `commands/` and registered in `bot.py` via `module.setup(bot, supabase)`.
- Database helpers live in `utils/database.py` and encapsulate per-game operations (create tables, get/update stats, leaderboards).
- Slash commands are synced on start in `on_ready()`.

Local tips:

- If slash commands don’t appear, ensure the bot has the correct scopes (applications.commands, bot), then wait a minute or re-run to sync.
- If table creation fails on startup, confirm you executed `sql/initial.sql` and your service role key is correct.

---

## 🚀 Deployment Notes

- `keep_alive.py` runs a small web server to keep the process alive on free hosts. For proper production (Docker/VM/Platform-as-a-Service), you may disable or ignore it.
- Recommended hosting: Railway, Fly.io, Render, or a VPS with systemd.
- Ensure environment variables are configured in your host.

Example Procfile (Render/Heroku-style):

```bash
worker: python bot.py
```

---

## 🧪 Testing and Maintenance

- Manually test each command after changes; look at logs for stack traces.
- Backup: Since tables are per-guild, consider scheduled exports from Supabase if you need backups.
- Data cleanup: Use `/purge-data` to remove rows for users who left a server.

---

## 🗺️ Current Feature Set

Games: `rps`, `guess_number`, `tictactoe`, `battle`, `flipnfind`, `kidnapped_jack`.

Utilities: `basic.py` contains `/ping`, `/serverinfo`, `/userinfo`, math, dice, and more.

Moderation: `/purge-data` (Admin-only; safe modal flow; membership-verified deletion).

Economy & Jobs (V6): `/job` for interactive interviews; `/work` mini-game with memorization + timed challenges; rebalanced payouts with streaks and timeouts.

Guide: https://hexxabot.netlify.app/guide

Note: The older “RPS Royale” feature was removed; code and DB functions have been cleaned up.

---

## 📜 Changelog (Highlights)

- 6.0.0
  - Launched interactive job system with timed interviews (`/job`)
  - Reworked `/work` flow with memorization + button challenge and timeouts
  - Improved timeout handling across views to prevent errors
  - Website refresh (landing copy, guide renamed to /guide)
  - `/help` now links to the new online guide

- 5.0.0
  - Added Kidnapped Jack game with stats and leaderboards.
  - Added moderation data purge command with safe confirmation and membership checks.
  - Enabled RLS and basic authenticated policies in `initial.sql` for new per-guild tables.
  - Removed deprecated RPS Royale feature and associated DB helpers.
