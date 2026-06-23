# Barracks

Unlocks your core [infantry](../units.md) — the gateway from peasant rabble to a
real army.

## Reference
| Property | Value |
|---|---|
| Base cost | 200 gold |
| Slots consumed | 2 (per level) |
| Prerequisite | [Gold Mine](gold_mine.md) Lv1 |
| Cost formula | `floor(200 * 1.6^level)` (Builders ×0.70) |
| Level cap | 33 |

## Effect
- **Unlocks recruitment** of [Man-at-Arms](../ref_units/man_at_arms.md) and
  [Pikeman](../ref_units/pikeman.md) (requires Barracks Lv1).
- Is itself a **prerequisite** for the [Blacksmith](blacksmith.md) (needs Barracks Lv3).

## See also
[Buildings](../buildings.md) · [Units](../units.md) · [Man-at-Arms](../ref_units/man_at_arms.md) · [Pikeman](../ref_units/pikeman.md) · [Blacksmith](blacksmith.md)

---
Source: `config.py` (BUILDINGS), `bot.py` (recruit gates).
