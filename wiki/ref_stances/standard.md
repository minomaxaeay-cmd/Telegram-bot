# Stance: Standard (Balanced)

One of four [combat](../combat.md) stances. Set defensively in the ⚔️ Army menu;
chosen per-attack by the attacker.

| Multiplier | Value |
|---|---|
| `atk` (damage dealt) | 1.0 |
| `def` (damage taken) | 1.0 |

The neutral baseline — no damage bonus or penalty. Still participates in the
**tactical triangle** (see below) but is itself outside it (no tactical bonus
vs/against any stance).

## Tactical triangle
`get_tactical_bonus`: **Aggressive > Mobile > Defensive > Aggressive**, winner gets
**+15%** damage. The bonus is **directional** and evaluated per attack — only the side
whose stance *counters* the other's gets it. Because this is a strict 3-cycle, mutual
countering is impossible, so **at most one side** ever receives the +15%. Standard
neither gives nor receives a tactical bonus.

## See also
[Combat](../combat.md) · [Aggressive](aggressive.md) · [Defensive](defensive.md) · [Mobile](mobile.md)

---
Source: `config.py` (STANCE_STATS), `game_logic.py` (`get_tactical_bonus`).
