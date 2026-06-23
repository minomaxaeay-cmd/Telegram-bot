# Currencies

Iron Dominion runs on a **four-currency economy**. Gold is the universal currency;
three medieval resources — **Iron**, **Grain**, **Faith** — add strategic depth to the
[army](units.md) economy. Each is a **closed, conservative** system: one declared
production [building](buildings.md) (source) and declared [sinks](economy.md), with only
zero-sum player-vs-player transfers (see [MG4](../balance_overhaul/MG4_closed_economy.txt)).

| Currency | Emoji | Source (building) | Main sinks | Role |
|---|---|---|---|---|
| Gold  | 💰 | [Gold Mine](ref_buildings/gold_mine.md) | buildings, recruitment, upkeep, alliance fee | universal currency |
| Iron  | ⛓️ | [Iron Mine](ref_buildings/iron_mine.md) | military recruitment (& siege) | forge your army |
| Grain | 🌾 | [Farm](ref_buildings/farm.md) | army **food upkeep** every tick | feed your army |
| Faith | ✝️ | [Chapel](ref_buildings/chapel.md) | [Blessings](blessings.md) | temporary buffs |

> **Buildings cost only Gold.** The new currencies attach to the army economy, so the
> exponential gold building-cost curve (and the [progression](progression.md) horizon)
> is unchanged. See [Buildings](buildings.md).

## Starting stockpile
A new lord begins with **1000** gold, **100** Iron, **200** Grain, **0** Faith
(`config.STARTING_IRON/GRAIN/FAITH`; gold is the `users.gold` default). The small Iron
and Grain buffers let you field a first army before your production buildings catch up.

## Iron ⛓️ — forge your army
Produced by the [Iron Mine](ref_buildings/iron_mine.md) (`iron_mine_level × 2`/min).
Spent — **with** gold — to recruit armoured [units](units.md). Peasants (an unarmoured
levy) cost **no** iron; Man-at-Arms/Pikeman/Knight cost progressively more
(`config.IRON_COST_PER_UNIT`, ≈12% of the unit's gold cost; see `game_balance.iron_cost`).
Because the Iron Mine competes for [slots](buildings.md) with the Gold Mine, a big
armoured army forces a real economic trade-off.

## Grain 🌾 — feed your army
Produced by the [Farm](ref_buildings/farm.md) (`farm_level × 6`/min). Consumed **every
income tick** as **food upkeep** (`config.GRAIN_UPKEEP_PER_UNIT`: peasant 0.2,
man-at-arms 0.4, pikeman 0.5, knight 1.0, spy 0.3 per minute). If grain runs out, unfed
troops **starve** (desert) — bounded by `DESERTION_CAP` and unified with gold-upkeep
desertion (see [economy](economy.md)). So your army **size** is gated by your farms, not
just your gold.

## Faith ✝️ — devotion & blessings
Produced slowly by the [Chapel](ref_buildings/chapel.md) (`chapel_level × 0.5`/min).
Spent on [Blessings](blessings.md): temporary, hard-bounded buffs. Faith never grants
permanent power, so there is no power-creep / pay-to-win.

## See also
[Economy](economy.md) · [Buildings](buildings.md) · [Units](units.md) · [Blessings](blessings.md) · [Iron Mine](ref_buildings/iron_mine.md) · [Farm](ref_buildings/farm.md) · [Chapel](ref_buildings/chapel.md) · [Constants](ref_constants.md)

---
Source: `config.py` (CURRENCIES, STARTING_*, IRON_PER_MINE_LVL, GRAIN_PER_FARM_LVL, FAITH_PER_CHAPEL_LVL, IRON_COST_PER_UNIT, GRAIN_UPKEEP_PER_UNIT), `database.py` (income tick, spend_resources), `game_balance.py` (iron_cost).
