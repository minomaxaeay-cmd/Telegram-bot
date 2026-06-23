# Stance: Defensive (Phalanx)

One of four [combat](../combat.md) stances.

| Multiplier | Value |
|---|---|
| `atk` (damage dealt) | 0.9 |
| `def` (damage taken) | 0.8 |

Trades output (−10% damage) for survivability (takes only 80% damage). The turtle
stance.

## Tactical triangle
**Aggressive > Mobile > Defensive > Aggressive** (+15% to the winner; directional,
evaluated per attack — only the side whose stance counters the other gets it).
- Defensive **beats [Aggressive](aggressive.md)** (+15% vs Aggressive).
- Defensive **is beaten by [Mobile](mobile.md)** (Mobile gets +15% vs Defensive).

## See also
[Combat](../combat.md) · [Aggressive](aggressive.md) · [Mobile](mobile.md) · [Standard](standard.md)

---
Source: `config.py` (STANCE_STATS), `game_logic.py` (`get_tactical_bonus`).
