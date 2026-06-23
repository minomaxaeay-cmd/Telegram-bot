# Iron Mine

Your military forge engine — the only in-loop source of [Iron](../currencies.md) ⛓️.

## Reference
| Property | Value |
|---|---|
| Base cost | 150 gold |
| Slots consumed | 1 (per level) |
| Prerequisite | [Castle](castle.md) Lv1 |
| Cost formula | `floor(150 * 1.6^level)` (Builders ×0.70) |
| Level cap | 33 |

New lords do **not** start with an Iron Mine — build one to sustain an armoured army.

## Effect
```
iron_per_minute = iron_mine_level * 2      # config.IRON_PER_MINE_LVL
```
- Accrues passively, **capped at 24h** offline (same tick as [gold](../economy.md)).
- Iron has **no upkeep** — it is a pure stockpile resource, spent on recruitment.

## Why it matters
Armoured [units](../units.md) (Man-at-Arms, Pikeman, Knight) cost **Iron** on top of
gold (`config.IRON_COST_PER_UNIT`). The Iron Mine competes for [slots](../buildings.md)
with the [Gold Mine](gold_mine.md) and [Farm](farm.md), so scaling a real army means
balancing gold income, iron output, and grain to feed them.

## See also
[Currencies](../currencies.md) · [Units](../units.md) · [Buildings](../buildings.md) · [Gold Mine](gold_mine.md) · [Farm](farm.md)

---
Source: `config.py` (BUILDINGS, IRON_PER_MINE_LVL, IRON_COST_PER_UNIT), `database.py` (income tick).
