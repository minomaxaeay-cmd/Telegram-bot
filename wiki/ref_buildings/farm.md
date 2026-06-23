# Farm

Your breadbasket — the only in-loop source of [Grain](../currencies.md) 🌾, the food
that keeps your [army](../units.md) from starving.

## Reference
| Property | Value |
|---|---|
| Base cost | 120 gold |
| Slots consumed | 1 (per level) |
| Prerequisite | [Castle](castle.md) Lv1 |
| Cost formula | `floor(120 * 1.6^level)` (Builders ×0.70) |
| Level cap | 33 |

New lords do **not** start with a Farm (they carry a small grain buffer instead).

## Effect
```
grain_per_minute = farm_level * 6          # config.GRAIN_PER_FARM_LVL
```
- Accrues passively, **capped at 24h** offline.
- Boosted **+25%** while a [Blessing of Plenty](../blessings.md) is active.

## Why it matters
Every [unit](../units.md) eats **Grain** each tick as **food upkeep**
(`config.GRAIN_UPKEEP_PER_UNIT`). If your farms can't feed your army, unfed troops
**starve** (desert), bounded by `DESERTION_CAP` and unified with the gold-upkeep
desertion rule (see [economy](../economy.md)). So your army **size** is gated by your
farms as much as your [Gold Mine](gold_mine.md).

## See also
[Currencies](../currencies.md) · [Economy](../economy.md) · [Units](../units.md) · [Buildings](../buildings.md) · [Blessings](../blessings.md)

---
Source: `config.py` (BUILDINGS, GRAIN_PER_FARM_LVL, GRAIN_UPKEEP_PER_UNIT), `database.py` (income tick, starvation desertion).
