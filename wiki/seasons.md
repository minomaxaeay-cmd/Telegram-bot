# Seasons

Iron Dominion runs in **seasons** — competitive periods tracked on the
[leaderboard](#leaderboard) that reset, while your kingdom (gold, buildings, army,
[Renown](renown.md)) persists.

## Season score & leaderboard
- Winning a [battle](combat.md) grants **+10 season_score** points (and a win
  record); losing adds a loss. This applies to **whoever wins** — a lord who is
  attacked and **successfully defends** earns the win, the +10 points, and
  [Renown](renown.md) just like a winning attacker (`record_battle_result` is called
  for the victor of either side). Stored per user.
- The 🏆 Leaderboard ranks lords by `season_score` (ties broken by **`wins`**, both
  descending) for the **current season**.

## Starting a new season (admin)
`start_new_season()` (admin console):
1. Archives the current top 3 into the **Hall of Fame** (`hall_of_fame` table).
2. **Resets** `season_score`, `wins`, `losses` for all users.
3. Increments the season number in `meta`.

> Kingdoms are **not** reset — gold, [buildings](buildings.md), [army](units.md),
> and **[Renown](renown.md) are untouched** (Renown is lifetime, spanning seasons).

## See also
[Renown](renown.md) · [Combat](combat.md) · [Profiles](profiles.md) · [Architecture: Database](arch_database.md)

---
Source: `database.py` (`record_battle_result`, `get_leaderboard`, `start_new_season`, `get_hall_of_fame`, `meta`), `bot.py` (admin console, leaderboard view).
