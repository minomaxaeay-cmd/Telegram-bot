# Iron Dominion — Wiki

A complete, cross-linked reference for **Iron Dominion**, a Telegram medieval-war
strategy game. Mechanics, constants, stats and schema here are derived directly from
the game's source code (`config.py`, `game_balance.py`, `game_logic.py`,
`database.py`, `bot.py`). A few **balance figures** (unit win-rates, matchup outcomes,
the ~11.45-year max-out estimate) instead come from the offline simulator
(`balance_sim.py` / `balance_harness.py`) or design notes, and are labelled as such
where they appear.

> Tip: this is a graph wiki — keywords link to their own pages. See [GRAPH.md](GRAPH.md)
> for the full map of how pages connect.

## Core mechanics
- [Economy](economy.md) — gold, income, upkeep, desertion, vault, loot
- [Currencies](currencies.md) — Gold, Iron, Grain, Faith (the four-resource economy)
- [Combat](combat.md) — how battles are resolved
- [Siege](siege.md) — multi-phase assaults, walls & engines (Raid vs Siege)
- [Buildings](buildings.md) — your fief's structures
- [Units](units.md) — your army
- [Blessings](blessings.md) — temporary Faith-bought buffs
- [Espionage](espionage.md) — spies, heists, sabotage
- [Alliances](alliances.md) — banding together
- [Seasons](seasons.md) — leaderboard resets & Hall of Fame
- [Renown](renown.md) — lifetime prestige
- [Progression](progression.md) — the long game (design horizon)
- [Newbie Protection](protection.md) — the starting shield
- [Tavern](tavern.md) — global chat
- [Profiles](profiles.md) — your lord identity

## Reference (exact data)
- Units: [Peasant](ref_units/peasant.md) · [Man-at-Arms](ref_units/man_at_arms.md) · [Pikeman](ref_units/pikeman.md) · [Knight](ref_units/knight.md) · [Rogue/Spy](ref_units/spy.md)
- Buildings: [Castle](ref_buildings/castle.md) · [Gold Mine](ref_buildings/gold_mine.md) · [Iron Mine](ref_buildings/iron_mine.md) · [Farm](ref_buildings/farm.md) · [Chapel](ref_buildings/chapel.md) · [Barracks](ref_buildings/barracks.md) · [Blacksmith](ref_buildings/blacksmith.md) · [Watchtower](ref_buildings/watchtower.md)
- [Tribes](ref_tribes/highlander.md) · [Stances](ref_stances/standard.md) · [Constants](ref_constants.md)

## Under the hood
- [Architecture overview](arch_overview.md) · [Database](arch_database.md) · [Commands & callbacks](arch_commands.md) · [State machine](arch_state_machine.md)
- [Admin Console](admin.md) — operator tools (gold, broadcast, DMs, ban/unban, image swap, media ID, seasons)

---
Source: whole codebase. Build plan: `WIKI_MEGAPLAN.txt`; progress: `WIKI_PROGRESS.txt`.
