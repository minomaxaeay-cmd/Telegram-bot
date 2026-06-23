# Espionage

Send [Rogues (Spies)](ref_units/spy.md) on covert missions against another lord.
Resolved by `game_logic.run_espionage(...)`. Requires spies (built at
[Castle](ref_buildings/castle.md) Lv2) and is subject to [newbie protection](protection.md)
and a per-target cooldown of **`SPY_COOLDOWN` = 600s (10 min)**.

## Detection vs attack
```
defense_score = def_spies * 1.0 + watchtower_level * 35 + 20      # WATCHTOWER_DETECT, BASE_DETECTION
attack_score  = spies_sent * uniform(0.8, 1.2)
ratio         = attack_score / max(defense_score, 1)
```
The defender's [Watchtower](ref_buildings/watchtower.md) and counter-spies raise
their detection.

## Outcome tiers (by ratio)
| ratio | Tier | Result |
|---|---|---|
| > 1.5 | 👻 Ghost | Success, **0 spies** lost, minimal alert |
| > 1.0 | Detected success | Success, **~20%** of spies lost (at least 1) |
| > 0.5 | Failed | **50%** of spies lost, target alerted |
| ≤ 0.5 | Disaster | **All** spies lost, your identity exposed |

## Missions
- **👁️ Scout** — reveals the target's gold, army, buildings and defensive stance.
- **💰 Heist** — steals gold:
  ```
  available = max(0, target_gold - castle_level * 1000)   # vault-protected (see Economy)
  stolen    = floor(min(surviving_spies * 50, available)) # SPY_CARRY_CAP = 50/spy
  ```
  A successful heist grants [Renown](renown.md) **only when gold is actually
  stolen** (`stolen_gold > 0`); a "successful" heist against a fully
  vault-locked treasury steals 0 and grants none. It is a zero-sum [economy](economy.md)
  transfer (clamped to the target's actual gold).
- **🔥 Sabotage** — a `random.randint(0, 100) < SABOTAGE_CHANCE` roll to destroy one
  level of a random non-Castle [building](buildings.md). Because `randint(0, 100)`
  is inclusive of both ends (101 outcomes), the true chance is 30/101 ≈ **29.7%**,
  not exactly 30%.

## See also
[Units](units.md) · [Combat](combat.md) · [Economy](economy.md) · [Watchtower](ref_buildings/watchtower.md) · [Renown](renown.md) · [Protection](protection.md)

---
Source: `game_logic.py` (`run_espionage`), `config.py` (SPY_CARRY_CAP, SPY_COOLDOWN, WATCHTOWER_DETECT, BASE_DETECTION, SABOTAGE_CHANCE), `bot.py` (spy menu/flow).
