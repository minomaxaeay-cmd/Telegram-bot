# Profiles

Your lord identity and public card.

## Identity
- **Game ID:** a unique `XXX-XXX` code (letters/digits) generated at signup; used
  to search and message lords.
- **Display name:** set via "✏️ Change Name" (2–20 chars, sanitized). Falls back to
  your Telegram username if unset.
- **Avatar:** chosen from a preset image list during setup (seeded from the **10**
  `AVATAR_IDS`); changeable later via the profile's prev/next face buttons. The list
  is now stored in the database (`meta.avatars`, read via `database.get_avatars()`)
  and is **admin-swappable** at runtime \u2014 see the [Admin Console](admin.md) "Manage Bot
  Images" tool. Swapping a slot changes the selection carousels and future picks;
  lords who already chose that image keep their stored `file_id`.

## Profile card shows
Your **own** card (`show_my_profile`) shows: Lord name, Game ID,
[tribe](ref_tribes/highlander.md), join date, gold, [Castle](ref_buildings/castle.md)
level, army size, rogues, [stance](ref_stances/standard.md), **[Renown](renown.md)**,
and a **Power Score**.

> Note on counts: the profile's **army size** excludes [Rogues/Spies](ref_units/spy.md)
> (it counts only `combat_valid` units), whereas the 📊 Status snapshot
> (`show_status`) reports **Total Troops** including spies — so the two can differ.

When you view **another** lord (`send_profile_view`), the card deliberately hides
gold, army size, rogues and stance — it shows only their name, Game ID, tribe,
join date, Castle level, Renown and Power Score (plus their newbie-shield timer if
active). Revealing the hidden details is exactly what a Scout
[espionage](espionage.md) mission is for.

## Power Score
A rough strength index: the sum of all [building](buildings.md) levels, with the
Castle counted **double** (`calculate_power_score`). Concretely the code sums every
building's level and then adds `buildings.get('castle', 1)` again (the castle level,
falling back to 1 if absent) — so in practice the Castle contributes twice. It is a
display metric, not used in [combat](combat.md) resolution.

## Viewing other lords
Another lord's profile (via 🔍 Search or the [map](arch_commands.md)) offers
**⚔️ Attack**, **🕵️ Espionage**, and **💬 Message** — subject to
[newbie protection](protection.md) and [alliance](alliances.md) rules.

## See also
[Renown](renown.md) · [Tribes](ref_tribes/highlander.md) · [Combat](combat.md) · [Espionage](espionage.md) · [Tavern](tavern.md)

---
Source: `bot.py` (`show_my_profile`, `send_profile_view`, rename/avatar flows), `game_logic.py` (`calculate_power_score`), `database.py` (`generate_unique_id`).
