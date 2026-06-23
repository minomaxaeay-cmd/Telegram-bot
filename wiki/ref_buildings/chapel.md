# Chapel

The seat of devotion — the only in-loop source of [Faith](../currencies.md) ✝️, which
funds temporary [Blessings](../blessings.md).

## Reference
| Property | Value |
|---|---|
| Base cost | 400 gold |
| Slots consumed | 1 (per level) |
| Prerequisite | [Castle](castle.md) Lv2 |
| Cost formula | `floor(400 * 1.6^level)` (Builders ×0.70) |
| Level cap | 33 |

## Effect
```
faith_per_minute = chapel_level * 0.5      # config.FAITH_PER_CHAPEL_LVL
```
- A **slow** prestige resource (half the rate constant of iron, a quarter of grain).
- Accrues passively, **capped at 24h** offline. No upkeep.

## Why it matters
Faith buys [Blessings](../blessings.md) — temporary, hard-bounded buffs (combat, grain,
defence). Because blessings expire and never stack with themselves, Faith adds an agency
axis for long-term players **without** permanent power-creep or pay-to-win.

## See also
[Currencies](../currencies.md) · [Blessings](../blessings.md) · [Buildings](../buildings.md) · [Castle](castle.md)

---
Source: `config.py` (BUILDINGS, FAITH_PER_CHAPEL_LVL, BLESSING_DEFS), `database.py` (income tick, buy_blessing).
