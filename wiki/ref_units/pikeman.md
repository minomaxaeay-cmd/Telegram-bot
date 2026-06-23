# Pikeman

The anti-armor specialist — built to **counter [Knights](knight.md)**. Requires a
[Barracks](../ref_buildings/barracks.md).

## Stats
| Stat | Value |
|---|---|
| Cost | 250 gold |
| HP | 50 |
| Soft attack | 3 |
| Hard attack | **40** |
| Piercing | **15** |
| Armor | 1 |
| Hardness (`hard`) | 0.0 |
| Width | 2 |
| Upkeep | 1.0 gold/min |
| Combat valid | Yes |

> `hard_atk = 40` and `piercing = 15` are **documented backbone exceptions** — the
> anti-knight counter spike and the armor-bypass that define the unit's role.

## Role & counters
- Gate: requires [Barracks](../ref_buildings/barracks.md) Lv1.
- **Beats [Knights](knight.md)**: huge `hard_atk` (40) shreds hard targets, and
  `piercing` 15 bypasses the knight's armor 12 (no halving) — see [combat](../combat.md).
- **Loses to [Man-at-Arms](man_at_arms.md) and [Peasants](peasant.md)** (it has
  almost no soft attack, so soft swarms beat it).

## See also
[Units](../units.md) · [Combat](../combat.md) · [Knight](knight.md) · [Man-at-Arms](man_at_arms.md) · [Peasant](peasant.md)

---
Source: `game_balance.py` (backbone + pikeman exceptions), `config.py` (UNITS, UPKEEP_PER_UNIT).
