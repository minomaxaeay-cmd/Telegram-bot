# Tribe: Ironborn ⛓️

One of four [tribes](../profiles.md) chosen at setup (permanent). The war-forge tribe.

| Field | Value |
|---|---|
| Bonus | -8% Army Gold Upkeep |
| `bonus_type` | upkeep |
| `value` | 0.92 |

## Effect
In the [income](../economy.md) tick, an Ironborn's **gold upkeep** for the whole army is
multiplied by **0.92** (−8%) before the net is applied. Their efficient forges and
disciplined logistics keep troops in the field cheaper, so they can sustain a **larger
standing army** on the same [Gold Mine](../ref_buildings/gold_mine.md) income — the
upkeep-rail mirror of the [Merchant](merchant.md)'s income bonus.

> Design note (TASK 1): an earlier version of this tribe boosted Iron *production*, but
> iron is a one-time recruitment cost (not upkeep), so over time every lord accumulates
> enough — the bonus gave no steady-state power. Re-themed to an upkeep reduction, which
> is sim-tuned to parity with the other tribes (win-rate spread < 10%).

## See also
[Economy](../economy.md) · [Currencies](../currencies.md) · [Units](../units.md) · [Highlander](highlander.md) · [Merchant](merchant.md) · [Builder](builder.md)

---
Source: `config.py` (TRIBES), `database.py` (income tick — Ironborn gold-upkeep multiplier).
