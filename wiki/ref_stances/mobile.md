# Stance: Mobile (Skirmish)

One of four [combat](../combat.md) stances.

| Multiplier | Value |
|---|---|
| `atk` (damage dealt) | 1.0 |
| `def` (damage taken) | 1.0 |

Statistically identical to [Standard](standard.md) in raw multipliers — its
distinction is purely in the **tactical triangle**.

## Tactical triangle
**Aggressive > Mobile > Defensive > Aggressive** (+15% to the winner; directional,
evaluated per attack — only the side whose stance counters the other gets it).
- Mobile **beats [Defensive](defensive.md)** (+15% vs Defensive).
- Mobile **is beaten by [Aggressive](aggressive.md)** (Aggressive gets +15% vs Mobile).

## See also
[Combat](../combat.md) · [Defensive](defensive.md) · [Aggressive](aggressive.md) · [Standard](standard.md)

---
Source: `config.py` (STANCE_STATS), `game_logic.py` (`get_tactical_bonus`).
