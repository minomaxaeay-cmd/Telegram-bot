# Blacksmith

Unlocks [Knights](../ref_units/knight.md) and **forges** your whole army — a combat
tech axis.

## Reference
| Property | Value |
|---|---|
| Base cost | 800 gold |
| Slots consumed | 2 (per level) |
| Prerequisite | [Barracks](barracks.md) Lv3 |
| Cost formula | `floor(800 * 1.6^level)` (Builders ×0.70) |
| Level cap | 33 |

## Effects
- **Unlocks [Knight](../ref_units/knight.md) recruitment** (requires Blacksmith Lv1).
- **Forge (MG6):** multiplies *your* army's outgoing [combat](../combat.md) damage by
  ```
  1 + min(BLACKSMITH_DMG_PER_LVL * level, BLACKSMITH_DMG_CAP)
    = 1 + min(0.02 * level, 0.25)        # up to +25%
  ```
  It is **symmetric** (applies whether you attack or defend), so it never encourages
  turtling. It's best understood as a **late-game multiplier / gold-sink**: in a
  fixed-budget snapshot, pure army still beats army+forge (building cost is
  exponential), but once your army is at its sustainable cap, extra gold in the
  Blacksmith makes that army stronger.

## See also
[Buildings](../buildings.md) · [Combat](../combat.md) · [Knight](../ref_units/knight.md) · [Barracks](barracks.md) · [Progression](../progression.md)

---
Source: `config.py` (BUILDINGS, BLACKSMITH_DMG_PER_LVL, BLACKSMITH_DMG_CAP), `game_logic.py` (`simulate_battle` forge), `bot.py` (knight gate).
