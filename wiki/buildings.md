# Buildings

Buildings are the backbone of your fief. Each has a **level**, costs gold to
upgrade, consumes **slots**, and may require prerequisites. Managed in the
🏰 Fiefdom menu and built via `game_logic.can_build(...)`.

## The eight buildings
| Building | Base cost | Slots | Requires | Role |
|---|---|---|---|---|
| [Castle](ref_buildings/castle.md) | 500 | 0 | — | +5 max slots per level; [vault](economy.md) |
| [Gold Mine](ref_buildings/gold_mine.md) | 100 | 1 | castle Lv1 | [income](economy.md) = level × 5/min |
| [Iron Mine](ref_buildings/iron_mine.md) | 150 | 1 | castle Lv1 | [Iron](currencies.md) = level × 2/min |
| [Farm](ref_buildings/farm.md) | 120 | 1 | castle Lv1 | [Grain](currencies.md) = level × 6/min |
| [Chapel](ref_buildings/chapel.md) | 400 | 1 | castle Lv2 | [Faith](currencies.md) = level × 0.5/min |
| [Barracks](ref_buildings/barracks.md) | 200 | 2 | gold_mine Lv1 | unlocks man-at-arms & pikeman |
| [Blacksmith](ref_buildings/blacksmith.md) | 800 | 2 | barracks Lv3 | unlocks knights + [Forge](combat.md) buff |
| [Watchtower](ref_buildings/watchtower.md) | 300 | 1 | castle Lv2 | [fortify](combat.md) defense + [espionage](espionage.md) detection |

> **Buildings cost only Gold** (the formula below). The [Iron Mine / Farm / Chapel](currencies.md)
> produce the new currencies but are themselves bought with gold, so the gold
> [progression](progression.md) horizon is unchanged.

## Cost formula
```
cost = floor(base_cost * 1.6 ^ current_level)
if tribe == "builder": cost = floor(cost * 0.70)      # Builders -15%
```
Cost grows **exponentially** (×1.6 per level). See [progression](progression.md).

## Level cap
Every building is capped at **`MAX_BUILDING_LEVEL = 33`**. `can_build` refuses
upgrades at the cap ("Max level reached"), and the UI shows **MAX** instead of a
cost. The cap exists so the exponential curve is finite — maxing the gold mine
is estimated to take ~11.45 years (a `config.py` design figure, not a runtime value;
see [progression](progression.md)).

## Slots
Total capacity = `castle_level * 5`. Each building consumes its `slots` value ×
its level. You can't build/upgrade past your slot capacity — upgrade your
[Castle](ref_buildings/castle.md) for more room. This forces real trade-offs.

## Prerequisites
`can_build` checks the `req` chain (e.g. blacksmith needs barracks Lv3). The chain
is reachable from the starting castle Lv1 + gold_mine Lv1 that new lords receive.

## See also
[Economy](economy.md) · [Units](units.md) · [Combat](combat.md) · [Progression](progression.md) · [Constants](ref_constants.md)

---
Source: `config.py` (BUILDINGS, MAX_BUILDING_LEVEL), `game_logic.py` (`can_build`), `bot.py` (`view_city`, build callback), `database.py` (new-user seeding).
