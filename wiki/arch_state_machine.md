# State Machine

Multi-step interactions use a per-user **`state`** (stored in `users.state` as JSON).
`handle_text` routes free-text input based on the current state. **Most** menu buttons
clear state first (a global "escape hatch"), but 🍻 [Tavern](tavern.md) instead **sets**
the `chatting` state and 🔍 Search **sets** `search_player`. See [Commands](arch_commands.md).

## States and their flows
| State | Triggered by | Expects | Result |
|---|---|---|---|
| `chatting` | 🍻 [Tavern](tavern.md) | any text | posts to global chat; "🔙 Exit Tavern" leaves |
| `search_player` | 🔍 Search | `XXX-XXX` id | opens that lord's [profile](profiles.md) |
| `{action: dm_write, target_id}` | 💬 Message | text (≤500) | sends a private message |
| `{action: rename_profile}` | ✏️ Change Name | text (2–20) | updates `display_name` |
| `{action: spy_input, mission, target_id}` | [spy](espionage.md) mission | spy count | runs `run_espionage` |
| `{action: attack_select, …}` | ⚔️ [pre_attack](combat.md) | unit counts | builds the attack; `atk_final` resolves it |
| `{action: recruit_input, unit}` | recruit a [unit](units.md) | count | recruits if gold suffices (a [sink](economy.md)) |
| `alliance_create_name` → `{alliance_create_tag, name}` | found [alliance](alliances.md) | name then tag | creates the alliance (2000g) |
| `alliance_join` | join alliance | tag | joins by tag |
| `{action: admin_find_user}` → `{admin_add_gold, target_uid}` | admin | game id then amount | admin gold gift (out-of-economy) |
| `{action: admin_broadcast}` | [admin](admin.md) | text | sends to all setup-complete lords |
| `{action: admin_dm_find}` → `{admin_dm_send, target_uid}` | admin | game id then text | private message to one lord |
| `{action: admin_alliance_find}` → `{admin_alliance_send, alliance_id}` | admin | tag then text | message all [alliance](alliances.md) members |
| `{action: admin_ban_find}` | admin | game id | bans a lord (full lockout) |
| `{action: admin_unban_find}` | admin | game id | lifts a ban |
| `{action: admin_get_media}` | admin | media | replies with the media's `file_id` |
| `{action: admin_set_image, slot}` | admin | photo | swaps a [bot image](profiles.md) slot |

> Admin states are handled in `handle_text` (text) and `handle_admin_media` (media),
> each re-checking `config.ADMIN_ID`. See [Admin](admin.md).
>
> The [newbie-protection](protection.md) waiver uses **callbacks only**
> (`waive:<ctx>:<id>` / `waive_cancel`), not a text state — it is offered when a
> shielded lord attempts an offensive action.

## Notes
- State is JSON-encoded; `get_state`/`set_state` handle legacy plain strings.
- The attack flow keeps its working selection in state and edits its UI message
  in place via `refresh_attack_ui`.
- Setup (pre-`setup_complete`) intercepts text before menu routing so new lords
  must finish [tribe](ref_tribes/highlander.md)/avatar selection first.

## See also
[Commands](arch_commands.md) · [Architecture overview](arch_overview.md) · [Espionage](espionage.md) · [Combat](combat.md) · [Alliances](alliances.md)

---
Source: `bot.py` (`get_state`/`set_state`, `handle_text` state branches, `handle_admin_media`, attack/espionage/alliance/admin flows).
