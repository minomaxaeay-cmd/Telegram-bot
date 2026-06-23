# Admin Console

A hidden operator console for the bot owner. Opened with the slash trigger
**`/admin01`** (`config.ADMIN_TRIGGER`) and **ignored for everyone whose Telegram id
is not `config.ADMIN_ID`** — the handler simply returns for non-admins, and every
admin callback/state step re-checks the id ("double security").

## Opening it
Send `config.ADMIN_TRIGGER` (`/admin01`). The console is an inline keyboard:

| Button | Callback | Action |
|---|---|---|
| 💰 Send Gold to Player | `admin:start_gold` | Out-of-economy gold gift by [Game ID](profiles.md) |
| 📢 Broadcast to All | `admin:broadcast` | Message every setup-complete lord |
| ✉️ Message a Player | `admin:msg_player` | Private message to one lord by Game ID |
| 🤝 Message an Alliance | `admin:msg_alliance` | Message every member of an [alliance](alliances.md) by tag |
| 🚫 Ban Player | `admin:ban` | Full lockout by Game ID |
| ✅ Unban Player | `admin:unban` | Lift a ban by Game ID |
| 🖼️ Manage Bot Images | `admin:images` | Swap the bot's [avatar images](profiles.md) |
| 🆔 Get Media ID | `admin:get_media` | Reply with the `file_id` of any media you send |
| 🏆 Start New Season | `admin:new_season` | Archive top 3 + reset the [season](seasons.md) board |

## Send Gold
`admin:start_gold` → enter a Game ID → enter an amount. The gold is **minted**
(an out-of-loop [economy](economy.md) source, MG4) and the recipient is notified.
States: `admin_find_user` → `admin_add_gold`.

## Broadcast / Direct messages
- **Broadcast** (`admin_broadcast`): the next text is sent to every **setup-complete,
  non-banned** lord (via `database.get_all_user_ids`) as a **📢 ROYAL DECREE**.
- **Message a Player** (`admin_dm_find` → `admin_dm_send`): find by Game ID, then the
  next text is delivered as a **👑 MESSAGE FROM THE CROWN**.
- **Message an Alliance** (`admin_alliance_find` → `admin_alliance_send`): find by
  **tag**, then the text is sent to every member (`database.get_alliance_members`).

All sends are wrapped in try/except, so unreachable lords (who blocked the bot) are
counted and skipped; the admin gets a delivered/unreachable tally.

> **Game-ID lookups resolve set-up lords only.** Send Gold, Message a Player, and
> Ban/Unban all use `database.get_user_by_game_id`, which filters `setup_complete = 1`
> — a lord who hasn't finished onboarding can't be targeted by Game ID.

## Ban / Unban (full lockout)
- **Ban** (`admin_ban_find`): sets `users.banned = 1` for the target. You **cannot ban
  yourself** (the `ADMIN_ID` is exempt). The banned lord is notified.
- **Unban** (`admin_unban_find`): clears the flag.

A banned lord is fully locked out: `start`, `handle_text`, and `handle_callbacks`
all refuse banned users (the admin is never locked out). Enforced via
`database.is_banned`.

## Get Media ID
`admin:get_media` (state `admin_get_media`) → send any **photo / document / video /
animation** and the bot replies with its Telegram **`file_id`**. This is how you
obtain the IDs used as bot avatars (see [Profiles](profiles.md) / `AVATAR_IDS`).
Handled by the admin-only media handler `handle_admin_media`.

## Manage Bot Images
`admin:images` opens a **carousel that looks exactly like the player avatar picker**
(`⬅️` / `✅ Replace This Image` / `➡️`, "Image X of N", with the current `file_id`
shown). Navigation edits the photo in place (`aimg:move:<i>`).

Pressing **✅ Replace This Image** (`aimg:sel:<i>`) opens a **new prompt** (with an
**❌ Cancel** button, `aimg:cancel`) asking you to *send the new photo*. The photo you
send replaces that slot (state `admin_set_image`), and it is used from then on
instead of the previous image.

Image swaps are **persisted** in the `meta` table as a JSON list under key `avatars`
(seeded once from `config.AVATAR_IDS`), so they survive bot restarts. The bot always
reads the live list via `database.get_avatars()`; `database.set_avatar(index, file_id)`
performs the swap. Lords who already picked an avatar keep their stored `file_id`; the
swap affects the selection carousels and future picks.

## Start New Season
`admin:new_season` → confirm/cancel. See [Seasons](seasons.md).

## See also
[Commands & callbacks](arch_commands.md) · [State machine](arch_state_machine.md) · [Database](arch_database.md) · [Profiles](profiles.md) · [Protection](protection.md) · [Seasons](seasons.md) · [Alliances](alliances.md)

---
Source: `bot.py` (`admin_panel`, admin callbacks, admin state flows in `handle_text`, `handle_admin_media`, `send_admin_image_view`, ban checks), `database.py` (`is_banned`, `set_banned`, `get_all_user_ids`, `get_avatars`, `set_avatar`), `config.py` (`ADMIN_ID`, `ADMIN_TRIGGER`, `AVATAR_IDS`).
