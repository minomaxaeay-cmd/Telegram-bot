# Alliances

Lords can band together into alliances for protection and prestige.

## Founding & joining
- **Found:** costs **`ALLIANCE_CREATE_COST` = 2000 gold** (a declared [economy](economy.md)
  sink — the fee is destroyed). You choose a name (3–24 chars) and a **tag**
  (2–`ALLIANCE_TAG_LEN`=4 letters/numbers). The founder becomes leader.
- **Join:** by alliance **tag**. Capacity is **`MAX_ALLIANCE_MEMBERS` = 10**.
- **Leave / Disband:** members leave freely; if the **leader** leaves, the alliance
  is **disbanded** for everyone.

## Effect
Alliance members **cannot [attack](combat.md) or [spy on](espionage.md)** each
other — `check_pvp_allowed` blocks any offensive action between allies (see also
[newbie protection](protection.md)).

## See also
[Combat](combat.md) · [Espionage](espionage.md) · [Economy](economy.md) · [Protection](protection.md) · [Profiles](profiles.md)

---
Source: `config.py` (ALLIANCE_CREATE_COST, MAX_ALLIANCE_MEMBERS, ALLIANCE_TAG_LEN), `database.py` (`create_alliance`, `join_alliance`, `leave_alliance`), `bot.py` (`check_pvp_allowed`, alliance views).
