# Tribe: Highlanders 🪓

One of four [tribes](../profiles.md) chosen at setup (permanent). The combat tribe.

| Field | Value |
|---|---|
| Bonus | +11% Combat Damage |
| `bonus_type` | combat |
| `value` | 1.11 |

## Effect
In [combat](../combat.md), Highlander units have their `soft_atk` and `hard_atk`
multiplied by **1.11** when the army pool is built (`create_unit_pool`). Applies to
all your [units](../units.md), attacking or defending. Sim-tuned (TASK 1) so the combat
edge offsets the economic tribes' slightly larger armies (win-rate spread < 10%).

## See also
[Combat](../combat.md) · [Merchant](merchant.md) · [Builder](builder.md) · [Profiles](../profiles.md)

---
Source: `config.py` (TRIBES), `game_logic.py` (`simulate_battle` highlander bonus).
