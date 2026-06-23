# Rogue (Spy)

The non-combat agent used for [espionage](../espionage.md). Rogues never fight in
[battles](../combat.md) — they scout, heist, and sabotage. Requires
[Castle](../ref_buildings/castle.md) Lv2.

## Stats
| Stat | Value |
|---|---|
| Cost | 200 gold |
| Upkeep | 0.5 gold/min |
| Width | 0 |
| Combat valid | **No** (excluded from `simulate_battle`) |

(Its combat stats are all 0/1 placeholders; it is priced separately, outside the
unit [backbone](../units.md).)

## Role
- Gate: requires [Castle](../ref_buildings/castle.md) Lv2.
- Sent on [espionage](../espionage.md) missions; survivors return based on the
  detection outcome tiers.
- A successful **heist** can grant [Renown](../renown.md).
- Also acts as **counter-intelligence**: your spy count raises your own detection
  score against enemy spies.

## See also
[Espionage](../espionage.md) · [Units](../units.md) · [Watchtower](../ref_buildings/watchtower.md) · [Renown](../renown.md)

---
Source: `config.py` (UNITS spy entry, UPKEEP_PER_UNIT), `game_logic.py` (`run_espionage`), `bot.py` (spy gate/flow).
