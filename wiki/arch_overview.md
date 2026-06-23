# Architecture Overview

Iron Dominion is a Telegram bot (pyTelegramBotAPI) backed by SQLite. The package
is `myTelegramBots/IronDominion/`.

## Modules
| Module | Responsibility |
|---|---|
| `config.py` | All tunables & data tables: API token, [tribes](ref_tribes/highlander.md), [units](units.md) (built from the backbone), [buildings](buildings.md), [stances](ref_stances/standard.md), and every [constant](ref_constants.md). |
| `game_balance.py` | The parametric **stat backbone** — derives unit combat stats from cost × role-vector ÷ stat-price, with documented exceptions. Imported by `config`. |
| `database.py` | SQLite access: schema/migrations (`init_db`), users/[economy](economy.md) tick, [buildings](buildings.md)/[units](units.md) queries, [alliances](alliances.md), [seasons](seasons.md)/[renown](renown.md) leaderboards. See [Database](arch_database.md). |
| `game_logic.py` | Pure game rules: `simulate_battle` ([combat](combat.md)), `run_espionage` ([espionage](espionage.md)), `can_build` ([buildings](buildings.md)), `calculate_power_score`, `get_tactical_bonus`. |
| `bot.py` | Telegram layer: command/menu/[callback](arch_commands.md) handlers, the [state machine](arch_state_machine.md), views, and all DB-writing actions. |

## Import graph
```
__init__.py -> config -> game_balance
            -> database -> config
            -> game_logic -> config
            -> bot -> config, database, game_logic
```
`game_balance` imports nothing from the package (no cycles).

## Dev tools (not part of the running bot)
- `balance_sim.py` — local-Python tournament/counter harness over the real `simulate_battle`.
- `balance_harness.py` — the MG7 self-correcting balance loop (design-time only).
- `balance_overhaul/` — the design specs (MG0–MG7) behind the current balance.
- A Snowflake `IRON_DOMINION_SIM` database is referenced as a server-side simulation
  equivalent in the design notes, but it is **external** to this repository and not
  part of the shipped bot — treat it as design-time only.

## See also
[Database](arch_database.md) · [Commands](arch_commands.md) · [State machine](arch_state_machine.md) · [Units](units.md) · [Combat](combat.md)

---
Source: package modules `config.py`, `game_balance.py`, `database.py`, `game_logic.py`, `bot.py`, `__init__.py`.
