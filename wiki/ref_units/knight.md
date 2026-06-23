# Knight

The heavy shock unit — durable, hard-hitting, armored. The strongest generalist,
but hard-countered by [Pikemen](pikeman.md). Requires a
[Blacksmith](../ref_buildings/blacksmith.md).

## Stats
| Stat | Value |
|---|---|
| Cost | 500 gold |
| HP | 100 |
| Soft attack | 30 |
| Hard attack | 15 |
| Piercing | 5 |
| Armor | **12** |
| Hardness (`hard`) | 0.8 (mostly hard target) |
| Width | 4 |
| Upkeep | 2.0 gold/min |
| Combat valid | Yes |

> `armor = 12` and `piercing = 5` are **documented backbone exceptions**, tuned so
> Knights are tough but [Pikemen](pikeman.md) (piercing 15) still reliably counter them.

## Role & counters
- Gate: requires [Blacksmith](../ref_buildings/blacksmith.md) Lv1.
- **Beats [Man-at-Arms](man_at_arms.md) and [Peasants](peasant.md)** decisively.
- **Loses to [Pikemen](pikeman.md)** (their hard attack + piercing).
- Width 4 → only ~10 knights fit the 40-wide [frontline](../combat.md) at once.
- Highest [upkeep](../economy.md) (2.0/min): a knight army demands a strong
  [Gold Mine](../ref_buildings/gold_mine.md) or it deserts.

## See also
[Units](../units.md) · [Combat](../combat.md) · [Pikeman](pikeman.md) · [Blacksmith](../ref_buildings/blacksmith.md) · [Economy](../economy.md)

---
Source: `game_balance.py` (backbone + knight exceptions), `config.py` (UNITS, UPKEEP_PER_UNIT), `bot.py` (recruit gate).
