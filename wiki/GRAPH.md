# Wiki Graph

The cross-reference map of the wiki — each line lists a page and the pages it
links to (its outgoing edges). Use with [00_INDEX.md](00_INDEX.md).

## Mechanics (Phase 1)
- 00_INDEX -> (all pages)
- economy -> buildings, units, combat, renown, progression, currencies, gold_mine, castle, merchant, constants
- currencies -> economy, buildings, units, blessings, siege, iron_mine, farm, chapel, constants
- blessings -> currencies, chapel, combat, economy
- siege -> combat, currencies, watchtower, economy, renown, constants
- combat -> units, buildings, economy, stances, renown, espionage, watchtower, blacksmith, blessings, siege, ref_units/*, ref_tribes/highlander
- buildings -> economy, units, combat, progression, currencies, constants, ref_buildings/*
- units -> combat, buildings, economy, currencies, espionage, stances, arch_overview, ref_units/*
- espionage -> units, combat, economy, watchtower, renown, protection, spy
- alliances -> combat, espionage, economy, protection, profiles
- seasons -> renown, combat, profiles, arch_database
- renown -> economy, combat, espionage, seasons, progression
- progression -> economy, buildings, units, renown, combat, gold_mine, barracks, blacksmith
- protection -> combat, espionage, alliances, profiles, admin
- tavern -> profiles, arch_commands, arch_state_machine
- profiles -> renown, tribes, combat, espionage, tavern, castle, admin

## Reference (Phase 2)
- ref_units/peasant -> units, combat, pikeman, economy
- ref_units/man_at_arms -> units, combat, knight, pikeman, barracks
- ref_units/pikeman -> units, combat, knight, man_at_arms, peasant
- ref_units/knight -> units, combat, pikeman, blacksmith, economy
- ref_units/spy -> espionage, units, watchtower, renown
- ref_buildings/castle -> buildings, economy, watchtower, profiles
- ref_buildings/gold_mine -> economy, progression, units, buildings, merchant
- ref_buildings/iron_mine -> currencies, units, buildings, gold_mine, farm
- ref_buildings/farm -> currencies, economy, units, buildings, blessings
- ref_buildings/chapel -> currencies, blessings, buildings, castle
- ref_buildings/barracks -> buildings, units, man_at_arms, pikeman, blacksmith
- ref_buildings/blacksmith -> buildings, combat, knight, barracks, progression
- ref_buildings/watchtower -> combat, espionage, buildings, castle
- ref_tribes/highlander -> combat, merchant, builder, profiles
- ref_tribes/merchant -> economy, gold_mine, highlander, builder
- ref_tribes/builder -> buildings, progression, highlander, merchant
- ref_tribes/ironborn -> economy, currencies, units, highlander, merchant
- ref_stances/{standard,aggressive,defensive,mobile} -> combat + each other
- ref_constants -> 00_INDEX, economy, combat, buildings (+ many inline)

## Architecture (Phase 3)
- arch_overview -> arch_database, arch_commands, arch_state_machine, units, combat, economy, buildings, ref_tribes/*
- arch_database -> arch_overview, economy, seasons, renown, alliances, profiles, protection, tavern, units, buildings, admin
- arch_commands -> arch_state_machine, arch_overview, combat, espionage, profiles, buildings, units, seasons, alliances, tavern, admin
- arch_state_machine -> arch_commands, arch_overview, espionage, combat, alliances, tavern, units, economy, profiles, admin
- admin -> arch_commands, arch_state_machine, arch_database, profiles, protection, seasons, alliances, economy

---
Source: the link footers of each wiki page (kept in sync as pages are added).
