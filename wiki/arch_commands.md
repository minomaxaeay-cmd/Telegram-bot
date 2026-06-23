# Commands & Callbacks

How the [bot](arch_overview.md) UI maps to actions.

## Slash commands
- **`/start`** — onboarding ([tribe](ref_tribes/highlander.md) → avatar) for new lords; otherwise a welcome. Refuses [banned](admin.md) users.
- **`/admin01`** (`config.ADMIN_TRIGGER`) — [admin console](admin.md); ignored unless sender is `config.ADMIN_ID`.

## Bottom menu buttons (reply keyboard)
Handled in `handle_text`. Most buttons **clear state** first (a global escape hatch)
then open a view — **except** 🍻 Tavern, which **sets** the `chatting`
[state](arch_state_machine.md), and 🔍 Search Player, which **sets** the
`search_player` state:
| Button | Action |
|---|---|
| 🏰 Fiefdom | `view_city` ([buildings](buildings.md)) |
| ⚔️ Army | `view_army` ([units](units.md) + [stance](ref_stances/standard.md)) |
| 🗺️ War Map | `view_map` (random targets) |
| 📜 Reports | recent [battle](combat.md) reports (from the `reports` table) |
| 👤 My Profile | `show_my_profile` ([profiles](profiles.md)) |
| 🍻 Tavern (Global Chat) | `enter_tavern` ([tavern](tavern.md)) |
| 🤝 Alliance | `view_alliance` ([alliances](alliances.md)) |
| 🏆 Leaderboard | `view_leaderboard` ([seasons](seasons.md)) |
| 🔍 Search Player | sets `search_player` state |
| 📊 Status | `show_status` (quick snapshot) |

> Note: [espionage](espionage.md) outcomes (scout/heist/sabotage results and the
> alerts sent to the target) are delivered as **live Telegram messages** — they are
> **not** written to the `reports` table, so they never appear in 📜 Reports. Only
> [battle](combat.md) resolution writes reports.

## Inline callbacks (`handle_callbacks`, split on `:`)
> Banned users are refused at the top of `handle_callbacks` (the admin is exempt).
- **admin:** `start_gold`, `broadcast`, `msg_player`, `msg_alliance`, `ban`, `unban`, `get_media`, `images`, `new_season`, `new_season_confirm`, `new_season_cancel` ([admin](admin.md))
- **admin images:** `aimg:move:<i>`, `aimg:sel:<i>`, `aimg:cancel`, `aimg:close` ([admin](admin.md), admin-only)
- **protection waive:** `waive:<attack|spy>:<id>`, `waive_cancel` ([protection](protection.md))
- **setup:** `tribe:<key>`, `av:move:<i>`, `av:sel:<i>`
- **refresh:** `city`, `army`, `map`, `leaderboard`, `renown`
- **alliance:** `create`, `join`, `leave`
- **build:**`<key>` — upgrade a [building](buildings.md) via `can_build` (shows MAX at cap)
- **recruit:**`<key>` — start recruiting a [unit](units.md) (gated)
- **set_stance:**`<stance>` — set defensive [stance](ref_stances/standard.md)
- **profile:**`<id>`, **dm:**`<id>`, **dm_cancel**, **edit:** `name`/`av_prev`/`av_next`/`close`
- **spy_menu:**`<id>`, **spy_run:**`<mission>:<id>` ([espionage](espionage.md))
- **Attack flow:** `pre_attack:<id>`, `atk_hint`, `atk_inc:<unit>:<delta>`, `atk_set:<unit>`,
  `atk_tactics`, `atk_back`, `atk_cancel`, `atk_final:<stance>` ([combat](combat.md))
- **reports_clear**, **ignore/none**

## Media handler (`handle_admin_media`)
An admin-only handler for `content_types=['photo','document','video','animation']`.
Driven by admin state: `admin_get_media` replies with the media's `file_id`;
`admin_set_image` replaces a [bot image](profiles.md) slot with the sent photo. See
[Admin](admin.md).

## See also
[State machine](arch_state_machine.md) · [Architecture overview](arch_overview.md) · [Combat](combat.md) · [Espionage](espionage.md) · [Profiles](profiles.md) · [Admin](admin.md)

---
Source: `bot.py` (command handlers, `handle_text` menu/state routing, `handle_callbacks`, `handle_admin_media`).
