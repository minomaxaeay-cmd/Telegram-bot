# Stance: Aggressive (Charge)

One of four [combat](../combat.md) stances.

| Multiplier | Value |
|---|---|
| `atk` (damage dealt) | 1.2 |
| `def` (damage taken) | 1.1 |

High damage output (+20%) at the cost of taking more damage (+10%). Glass-cannon.

## Tactical triangle
**Aggressive > Mobile > Defensive > Aggressive** (+15% to the winner; directional,
evaluated per attack — only the side whose stance counters the other gets it).
- Aggressive **beats [Mobile](mobile.md)** (+15% vs Mobile).
- Aggressive **is beaten by [Defensive](defensive.md)** (Defensive gets +15% vs Aggressive).

## See also
[Combat](../combat.md) · [Mobile](mobile.md) · [Defensive](defensive.md) · [Standard](standard.md)

---
Source: `config.py` (STANCE_STATS), `game_logic.py` (`get_tactical_bonus`).
