# Peasant

The cheapest [unit](../units.md) — your starting fodder, available with no
building. Soft, numerous, and a niche counter to [Pikemen](pikeman.md).

## Stats
| Stat | Value |
|---|---|
| Cost | 20 gold |
| HP | 15 |
| Soft attack | 2 |
| Hard attack | 0 |
| Piercing | 0 |
| Armor | 0 |
| Hardness (`hard`) | 0.0 (fully soft target) |
| Width | 1 |
| Upkeep | 0.1 gold/min |
| Combat valid | Yes |

> HP 15 is a **documented backbone exception** (the formula would give ~7). The
> offline combat simulator (`balance_sim.py`) showed 15 is needed for peasants to
> fulfil their anti-pikeman role without creating a "screen" exploit; these are
> simulator findings, not source constants.

## Role & counters
- Always recruitable (no [building](../buildings.md) gate) — your day-one army.
- **Counters [Pikemen](pikeman.md)** at equal gold (swarm of cheap soft bodies).
- Loses to [Man-at-Arms](man_at_arms.md) and [Knights](knight.md); beats little else.
- Width 1 means many peasants fit on the 40-wide [frontline](../combat.md).

## See also
[Units](../units.md) · [Combat](../combat.md) · [Pikeman](pikeman.md) · [Economy](../economy.md)

---
Source: `game_balance.py` (backbone + peasant.hp exception), `config.py` (UNITS, UPKEEP_PER_UNIT).
