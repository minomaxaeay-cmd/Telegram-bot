# Units

Your army is made of unit types you recruit with [gold (and Iron)](currencies.md). Four
are combat units; the [Rogue/Spy](ref_units/spy.md) is non-combat (used for
[espionage](espionage.md)).

## Roster
| Unit | Gold | Iron | HP | Soft atk | Hard atk | Pierce | Armor | Hard | Width | Gold upkeep | Grain upkeep |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [Peasant](ref_units/peasant.md) | 20 | 0 | 15 | 2 | 0 | 0 | 0 | 0.0 | 1 | 0.1 | 0.2 |
| [Man-at-Arms](ref_units/man_at_arms.md) | 130 | 15 | 27 | 15 | 2 | 1 | 2 | 0.2 | 2 | 0.5 | 0.4 |
| [Pikeman](ref_units/pikeman.md) | 250 | 30 | 50 | 3 | 40 | 15 | 1 | 0.0 | 2 | 1.0 | 0.5 |
| [Knight](ref_units/knight.md) | 500 | 60 | 100 | 30 | 15 | 5 | 12 | 0.8 | 4 | 2.0 | 1.0 |
| [Rogue (Spy)](ref_units/spy.md) | 200 | 5 | — | — | — | — | — | — | 0 | 0.5 | 0.3 |

Combat stats are **derived** from a parametric backbone (`game_balance.py`): each stat =
`role_fraction * cost / stat_price`, with a few documented exceptions for the
counters (see [Architecture](arch_overview.md)). **Iron** cost is likewise backbone-derived
(`game_balance.iron_cost` ≈ 12% of gold cost; peasant = 0). See [Currencies](currencies.md).

## Recruitment & gates
Recruited in the ⚔️ Army menu, paying **gold + [Iron](currencies.md)** (peasant: no iron).
Access is gated by [buildings](buildings.md):
- **Peasant** — always available (your starter unit).
- **Man-at-Arms, Pikeman** — require a [Barracks](ref_buildings/barracks.md).
- **Knight** — requires a [Blacksmith](ref_buildings/blacksmith.md).
- **Spy** — requires [Castle](ref_buildings/castle.md) Lv2.

So your *optimal army depends on your buildings*.

## Rock-paper-scissors
The matchups below come from the offline combat simulator (`balance_sim.py` over the
real `simulate_battle`), not from a single source constant:
- **Knight** beats Man-at-Arms & Peasant, loses to **Pikeman**.
- **Man-at-Arms** beats Peasant & Pikeman, loses to **Knight**.
- **Pikeman** beats Knight (huge `hard_atk` 40), loses to **Man-at-Arms and Peasant**.
- **Peasant** is cheap chaff that counters the Pikeman; otherwise weak.

So: **Knight → Man-at-Arms → Pikeman → Knight**, plus Peasant → Pikeman. Every
unit has a counter; no unit wins every matchup.

## Sustaining an army
Units cost [upkeep](economy.md) every minute — **gold** (covered by your
[Gold Mine](ref_buildings/gold_mine.md)) **and Grain** (food, covered by your
[Farms](ref_buildings/farm.md)). Your max **sustainable** army is the *lower* of what
your gold and grain can feed; overreach on either and troops desert. Gold-sustainable
knights ≈ `floor(mine_level × 5 / 2)` (~2 at Lv1, ~82 at Lv33); grain adds a parallel
ceiling. Armoured units also need **[Iron](currencies.md)** up front to recruit. This
couples army size to your whole economy.

## See also
[Combat](combat.md) · [Buildings](buildings.md) · [Economy](economy.md) · [Currencies](currencies.md) · [Espionage](espionage.md) · [Stances](ref_stances/standard.md)

---
Source: `config.py` (UNITS via `game_balance`, UPKEEP_PER_UNIT, IRON_COST_PER_UNIT, GRAIN_UPKEEP_PER_UNIT), `game_balance.py` (backbone, iron_cost), `game_logic.py` (`simulate_battle`, `recruit_cost`), `bot.py` (recruit gates).
