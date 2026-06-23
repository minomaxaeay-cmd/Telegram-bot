# Tribe: Builders 🔨

One of four [tribes](../profiles.md) chosen at setup (permanent). The construction tribe.

| Field | Value |
|---|---|
| Bonus | -30% Building Cost |
| `bonus_type` | build |
| `value` | 0.70 |

## Effect
In `can_build`, a Builder's [building](../buildings.md) upgrade cost is multiplied by
**0.70** (−30%) after the base `floor(base * 1.6^level)`. Speeds up the whole
[progression](../progression.md) curve — a tempo/infrastructure edge (sim-tuned, TASK 1).

## See also
[Buildings](../buildings.md) · [Progression](../progression.md) · [Highlander](highlander.md) · [Merchant](merchant.md)

---
Source: `config.py` (TRIBES), `game_logic.py` (`can_build` builder discount).
