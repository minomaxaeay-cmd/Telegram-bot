# Watchtower

A defensive structure: it **fortifies you in [battle](../combat.md)** and boosts
your [espionage](../espionage.md) detection.

## Reference
| Property | Value |
|---|---|
| Base cost | 300 gold |
| Slots consumed | 1 (per level) |
| Prerequisite | [Castle](castle.md) Lv2 |
| Cost formula | `floor(300 * 1.6^level)` (Builders ×0.70) |
| Level cap | 33 |

## Effects
- **Fortification (MG6):** as the *defender*, you take reduced [combat](../combat.md)
  damage:
  ```
  reduction = min(WATCHTOWER_DEF_BONUS_PER_LVL * level, WATCHTOWER_DEF_CAP)
            = min(0.02 * level, 0.30)        # up to -30% incoming damage
  ```
  Hard-capped at 30% so defense can't become unbeatable (anti-turtle).
- **Walls & counter-fire ([Siege](../siege.md)):** the watchtower adds
  `WALL_PER_WATCHTOWER (60) * level` wall hit points, and during a siege bombardment it
  destroys `floor(0.20 * level)` attacking engines per volley. So a high watchtower makes
  you far harder to **breach** — but if breached, the fortification above is nullified.
- **Espionage detection:** adds `WATCHTOWER_DETECT (35) * level` to your
  [defense score](../espionage.md) against enemy spies.

> Note: the Watchtower's gold cost is exponential, so as a *pure* combat investment
> it rarely beats spending the same gold on army; its main value is espionage
> defense plus a modest home-defense edge.

## See also
[Combat](../combat.md) · [Espionage](../espionage.md) · [Buildings](../buildings.md) · [Castle](castle.md)

---
Source: `config.py` (BUILDINGS, WATCHTOWER_DEF_*, WATCHTOWER_DETECT), `game_logic.py` (`simulate_battle` fort, `run_espionage`).
