# Castle

The heart of your fief. Provides **building slots** and the gold **vault**, and
gates [spies](../ref_units/spy.md) and the [Watchtower](watchtower.md).

## Reference
| Property | Value |
|---|---|
| Base cost | 500 gold |
| Slots consumed | 0 |
| Prerequisite | none |
| Cost formula | `floor(500 * 1.6^level)` (Builders ×0.70) |
| Level cap | 33 |

New lords start with **Castle Lv1**.

## Effects
- **Max slots = `castle_level * 5`** — every level adds 5 [building](../buildings.md)
  slots, letting you build/upgrade more.
- **Vault:** protects `castle_level * 1000` gold (`SAFE_GOLD_PER_LEVEL`) from
  [looting](../economy.md) and [heists](../espionage.md).
- **Gates:** [Watchtower](watchtower.md) needs Castle Lv2; [Spies](../ref_units/spy.md)
  need Castle Lv2.
- Counts **double** toward [Power Score](../profiles.md) (`calculate_power_score`
  adds the castle level a second time, with a flat-`1` fallback if absent).

## See also
[Buildings](../buildings.md) · [Economy](../economy.md) · [Watchtower](watchtower.md) · [Profiles](../profiles.md)

---
Source: `config.py` (BUILDINGS, SAFE_GOLD_PER_LEVEL), `game_logic.py` (`can_build` slots, `calculate_power_score`).
