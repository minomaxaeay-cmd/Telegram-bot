# Database

SQLite database created/migrated by `database.init_db()` on startup. Row factory
is `sqlite3.Row`. `config.DB_NAME` is a hardcoded **absolute server path**
(`/home/tgbotstelegram02/mysite/myTelegramBots/IronDominion/medieval_war.db`); its
filename is `medieval_war.db`.

## Tables

### `users` (one row per lord)
| Column | Type / default | Notes |
|---|---|---|
| `user_id` | INTEGER PK | Telegram chat id |
| `game_id` | TEXT UNIQUE | `XXX-XXX` ([profile](profiles.md)) |
| `username` | TEXT | Telegram name |
| `display_name` | TEXT (base + migration) | chosen lord name |
| `tribe` | TEXT | [tribe](ref_tribes/highlander.md) key |
| `avatar_id` | TEXT | chosen avatar |
| `setup_complete` | INTEGER 0 | onboarding flag |
| `joined_date` | REAL | used by [protection](protection.md) |
| `gold` | REAL **DEFAULT 1000.0** | starting [endowment](economy.md) |
| `last_update` | REAL | for the [income](economy.md) tick |
| `state` | TEXT | [state machine](arch_state_machine.md) |
| `stance` | TEXT 'standard' (base + migration) | defensive [stance](ref_stances/standard.md) |
| `alliance_id` | INTEGER (migration) | [alliance](alliances.md) membership |
| `wins`, `losses` | INTEGER 0 (migration) | battle record |
| `season_score` | INTEGER 0 (migration) | [season](seasons.md) points |
| `renown` | INTEGER 0 (migration) | lifetime [Renown](renown.md) |
| `banned` | INTEGER 0 (base + migration) | admin full-lockout flag ([admin](admin.md)) |
| `protection_waived` | INTEGER 0 (base + migration) | player ended [newbie shield](protection.md) early |

### `buildings`
`(user_id, b_type, level)` — PK `(user_id, b_type)`. One row per [building](buildings.md) type.

### `units`
`(user_id, u_type, count)` — PK `(user_id, u_type)`. One row per [unit](units.md) type.

### `reports`
`(id PK AUTOINCREMENT, user_id, text, timestamp)` — **battle reports only**. Written
solely by the [combat](combat.md) resolver; [espionage](espionage.md) outcomes are
sent as live messages and are **not** stored here.

### `cooldowns`
`(user_id, target_id, timestamp)` — PK `(user_id, target_id)`. Attack cooldowns use
`target_id`; **[espionage](espionage.md)** cooldowns are namespaced as `-target_id`.

### `chat`
`(id PK, user_id, username, game_id, message, timestamp)` — the [Tavern](tavern.md).

### `alliances`
`(id PK, name UNIQUE, tag UNIQUE, leader_id, created_at)` — see [Alliances](alliances.md).

### `meta`
`(key PK, value)` — key/value store; holds `season`, `season_start`, and **`avatars`**
(a JSON list of the bot's [avatar](profiles.md) `file_id`s, seeded once from
`config.AVATAR_IDS`, swappable by the [admin](admin.md)).

### `hall_of_fame`
`(id PK, season, game_id, display_name, score, recorded_at)` — archived [season](seasons.md) champions.

## Migrations
New columns are added idempotently via `ALTER TABLE … ADD COLUMN` wrapped in
try/except: `display_name`, `stance`, `alliance_id`, `wins`, `losses`,
`season_score`, `renown`, **`banned`**, **`protection_waived`**. So upgrading an
existing DB is automatic on startup. The `meta.avatars` JSON list is also seeded on
startup via `INSERT OR IGNORE`.

## See also
[Architecture overview](arch_overview.md) · [Economy](economy.md) · [Seasons](seasons.md) · [Renown](renown.md) · [Alliances](alliances.md) · [Admin](admin.md)

---
Source: `database.py` (`init_db`, migrations, table accessors, `is_banned`/`set_banned`/`waive_protection`/`get_avatars`/`set_avatar`), `config.py` (DB_NAME, AVATAR_IDS).
