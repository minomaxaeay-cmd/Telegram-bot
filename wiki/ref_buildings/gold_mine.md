# Gold Mine

Your economic engine — the only in-loop source of [gold](../economy.md).

## Reference
| Property | Value |
|---|---|
| Base cost | 100 gold |
| Slots consumed | 1 (per level) |
| Prerequisite | [Castle](castle.md) Lv1 |
| Cost formula | `floor(100 * 1.6^level)` (Builders ×0.70) |
| Level cap | 33 |

New lords start with **Gold Mine Lv1**.

## Effect
```
income_per_minute = gold_mine_level * 5
```
- Accrues passively, **capped at 24h** offline (see [economy](../economy.md)).
- Amplified by the [Merchant](../ref_tribes/merchant.md) tribe (+8%) and the tiny
  [Renown](../renown.md) perk (≤ +2.5%).
- **Linear** income vs **exponential** cost → drives the [progression](../progression.md)
  curve; the fastest path to Lv33 is estimated at ~11.45 years (a `config.py` design
  comment, not a runtime value).

## Why it matters
Mine level sets your **max sustainable [army](../units.md)** (income must cover
[upkeep](../economy.md) or troops desert). Sustainable knights = `floor(level × 5 / 2)`:
~2 at Lv1, ~82 at Lv33.

## See also
[Economy](../economy.md) · [Progression](../progression.md) · [Units](../units.md) · [Buildings](../buildings.md) · [Merchant](../ref_tribes/merchant.md)

---
Source: `config.py` (BUILDINGS), `database.py` (income tick).
