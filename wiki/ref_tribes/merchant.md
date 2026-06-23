# Tribe: Merchants ⚖️

One of four [tribes](../profiles.md) chosen at setup (permanent). The economy tribe.

| Field | Value |
|---|---|
| Bonus | +8% Gold Income |
| `bonus_type` | gold |
| `value` | 1.08 |

## Effect
In the [income](../economy.md) tick, a Merchant's gold-mine income is multiplied by
**1.08** (+8%) before [upkeep](../economy.md) is subtracted. Compounds with mine
level and the [Renown](../renown.md) perk.

## See also
[Economy](../economy.md) · [Gold Mine](../ref_buildings/gold_mine.md) · [Highlander](highlander.md) · [Builder](builder.md)

---
Source: `config.py` (TRIBES), `database.py` (income tick merchant multiplier).
