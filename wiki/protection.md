# Newbie Protection

New lords are shielded so they can establish a fief before facing PvP.

## The shield
- Duration: **`NEWBIE_PROTECTION_SECONDS` = 86400 (24 hours)** from joining.
- While protected, you **cannot be [attacked](combat.md) or [spied on](espionage.md)**.
- You also **cannot initiate** attacks or espionage while protected.
- The shield is time-based (it otherwise expires 24h after `joined_date`), **but a
  player can now end it early themselves** — see [Waiving early](#waiving-early).

## How it's enforced
`check_pvp_allowed(attacker, defender)` (in `bot.py`) blocks an offensive action if:
- the two are [alliance](alliances.md) members, or
- the attacker is still under protection, or
- the defender is still under protection.

`protection_remaining(user)` computes the time left from `joined_date` — and now
returns **0 immediately if the player has waived** (`users.protection_waived = 1`).

## Waiving early
There is **no standalone button**. Instead, when a *shielded* lord actually tries an
offensive action (⚔️ Attack or 🕵️ Espionage), `check_pvp_allowed` reports the block
code `self_shield`, and the bot offers an inline confirm (`send_waive_prompt`):

> 🛡️ NEWBIE PROTECTION ACTIVE — *Waiving lets you strike now, but your shield drops
> permanently, so other lords can attack and spy on you too.*
> **[⚔️ Waive Protection & Continue]  [🛡️ Keep My Shield]**

Confirming calls `database.waive_protection(user_id)` (sets `protection_waived = 1`),
re-validates (the target could still be shielded or an ally), and then proceeds
straight into the attack/espionage flow. This finally makes the long-standing
"Attacking ends your shield" wording **true**. Waiving is **permanent**.

## See also
[Combat](combat.md) · [Espionage](espionage.md) · [Alliances](alliances.md) · [Profiles](profiles.md)

---
Source: `config.py` (NEWBIE_PROTECTION_SECONDS), `bot.py` (`check_pvp_allowed`, `protection_remaining`, `send_waive_prompt`, `waive` callback), `database.py` (`waive_protection`, `protection_waived` column).
