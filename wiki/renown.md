# Renown

**Renown** is a lifetime prestige score — it only ever goes up, and (unlike
[season](seasons.md) score) it is **never reset**. It is the long-term "your
effort is never wasted" track.

## Earning Renown
- **Win a [battle](combat.md):** `renown_gain = max(1, defeated_army_value // 50)`
  (`RENOWN_WIN_DIVISOR`). Scaled by the **defeated army's gold value**, so beating
  real opponents pays and farming tiny armies does not. "Winning" applies to either
  side: a successful **defender** earns this too (scaled by the defeated *attacker's*
  army), alongside their win record and +10 [season](seasons.md) points.
- **Successful [heist](espionage.md):** `renown_gain = max(1, stolen_gold // 100)`
  (`RENOWN_HEIST_DIVISOR`). Awarded **only when gold is actually stolen**
  (`stolen_gold > 0`) — a successful heist against a fully vault-locked treasury
  steals 0 and grants no renown.

Shown on your [profile](profiles.md) and on a dedicated **Renown leaderboard**.

## The perk (tiny, capped)
Renown grants a *stupidly small*, hard-capped [income](economy.md) bonus — it
never touches combat:
```
tier  = renown // 100                                  # RENOWN_PER_TIER
bonus = min(tier * 0.0005, 0.025)                      # +0.05%/tier, cap +2.5%
income *= (1 + bonus)
```
At the absolute cap it is only **+2.5%** income, so it motivates long play without
unbalancing anything.

## See also
[Economy](economy.md) · [Combat](combat.md) · [Espionage](espionage.md) · [Seasons](seasons.md) · [Progression](progression.md)

---
Source: `config.py` (RENOWN_PER_TIER, RENOWN_PERK_PER_TIER, RENOWN_PERK_CAP, RENOWN_WIN_DIVISOR, RENOWN_HEIST_DIVISOR), `database.py` (`record_battle_result`, `award_renown`, income perk, `get_renown_leaderboard`), `bot.py` (renown awards, profile/leaderboard).
