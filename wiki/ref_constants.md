# Constants Reference

Every **gameplay** constant in `config.py`, with its value and meaning. Grouped by
system. (Operator/asset settings — `ADMIN_ID`, `ADMIN_TRIGGER`, `API_TOKEN`,
`AVATAR_IDS` — are not gameplay tunables; see [Admin & assets](#admin--assets) below.)

## Combat
| Constant | Value | Meaning |
|---|---|---|
| `COMBAT_WIDTH` | 40 | Frontline width per side (see [combat](combat.md)) |
| `MAX_ROUNDS` | 25 | Max rounds before value-based resolution |
| `WATCHTOWER_DEF_BONUS_PER_LVL` | 0.02 | Defender damage reduction per [watchtower](ref_buildings/watchtower.md) level |
| `WATCHTOWER_DEF_CAP` | 0.30 | Max watchtower damage reduction |
| `BLACKSMITH_DMG_PER_LVL` | 0.02 | Army damage bonus per [blacksmith](ref_buildings/blacksmith.md) level |
| `BLACKSMITH_DMG_CAP` | 0.25 | Max Forge bonus |

## Economy
| Constant | Value | Meaning |
|---|---|---|
| starting gold | 1000 | New-lord [endowment](economy.md) (`users.gold` default) |
| `STARTING_IRON` | 100 | New-lord [Iron](currencies.md) stockpile |
| `STARTING_GRAIN` | 200 | New-lord [Grain](currencies.md) stockpile |
| `STARTING_FAITH` | 0 | New-lord [Faith](currencies.md) stockpile |
| mine income | level × 5 / min | [Gold Mine](ref_buildings/gold_mine.md) income |
| `IRON_PER_MINE_LVL` | 2 | [Iron Mine](ref_buildings/iron_mine.md) iron/min per level |
| `GRAIN_PER_FARM_LVL` | 6 | [Farm](ref_buildings/farm.md) grain/min per level |
| `FAITH_PER_CHAPEL_LVL` | 0.5 | [Chapel](ref_buildings/chapel.md) faith/min per level |
| offline cap | 86400 s | Income accrual capped at 24h |
| `LOOT_PERCENTAGE` | 0.30 | Fraction of exposed gold looted on a win |
| `SAFE_GOLD_PER_LEVEL` | 1000 | Vault gold protected per [castle](ref_buildings/castle.md) level |
| `DESERTION_CAP` | 0.10 | Max army fraction lost to desertion per tick (gold OR grain) |
| `UPKEEP_PER_UNIT` | peasant .1, man_at_arms .5, pikeman 1.0, knight 2.0, spy .5 | Gold/min per unit |
| `GRAIN_UPKEEP_PER_UNIT` | peasant .2, man_at_arms .4, pikeman .5, knight 1.0, spy .3 | [Grain](currencies.md)/min per unit (food) |
| `IRON_COST_PER_UNIT` | peasant 0, man_at_arms 15, pikeman 30, knight 60, spy 5 | [Iron](currencies.md) recruit cost per unit |

## Blessings (Faith sink)
| Blessing | Faith | Duration | Effect |
|---|---|---|---|
| Zeal ⚔️ | 50 | 3600 s | +10% combat damage |
| Plenty 🌾 | 40 | 3600 s | +25% grain production |
| Ward 🛡️ | 60 | 3600 s | −10% incoming damage (defending) |

See [Blessings](blessings.md) and [Currencies](currencies.md) (`config.BLESSING_DEFS`).

## Siege ([siege](siege.md))
| Constant | Value | Meaning |
|---|---|---|
| `WALL_BASE` | 100 | Baseline wall HP every fief has |
| `WALL_PER_WATCHTOWER` | 60 | +wall HP per [watchtower](ref_buildings/watchtower.md) level |
| `WALL_PER_CASTLE` | 25 | +wall HP per [castle](ref_buildings/castle.md) level |
| `SIEGE_ENGINES` | ram 120💰/20⛓️/10🌾 dmg25; trebuchet 300💰/40⛓️/20🌾 dmg60 | engine costs + wall damage |
| `BOMBARD_VOLLEYS` | 3 | bombardment rounds before the field battle |
| `WT_ENGINE_KILLS_PER_LVL` | 0.20 | engines destroyed per watchtower level per volley |
| `SIEGE_SACK_LOOT_PCT` | 0.50 | exposed-gold looted on a breach-and-sack |
| `SIEGE_SACK_VAULT_MULT` | 0.50 | vault multiplier on a breach (halved → more exposed) |
| `SIEGE_BREACH_RENOWN_MULT` | 1.5 | renown multiplier for a successful breach |

## Buildings
| Constant | Value | Meaning |
|---|---|---|
| `MAX_BUILDING_LEVEL` | 33 | Hard level cap on all [buildings](buildings.md) |
| cost formula | `base × 1.6^level` | Exponential upgrade cost |
| Builder discount | ×0.70 | [Builder](ref_tribes/builder.md) tribe cost reduction |
| slots | `castle_level × 5` | Total slot capacity |

## Renown
| Constant | Value | Meaning |
|---|---|---|
| `RENOWN_PER_TIER` | 100 | [Renown](renown.md) per perk tier |
| `RENOWN_PERK_PER_TIER` | 0.0005 | +0.05% income per tier |
| `RENOWN_PERK_CAP` | 0.025 | Max +2.5% income |
| `RENOWN_WIN_DIVISOR` | 50 | Win renown = defeated_value // 50 |
| `RENOWN_HEIST_DIVISOR` | 100 | Heist renown = stolen // 100 |

## Espionage
| Constant | Value | Meaning |
|---|---|---|
| `SPY_CARRY_CAP` | 50 | Max gold one spy heists |
| `SPY_COOLDOWN` | 600 s | Cooldown per target ([espionage](espionage.md)) |
| `WATCHTOWER_DETECT` | 35 | Detection per watchtower level |
| `BASE_DETECTION` | 20 | Flat detection score |
| `SABOTAGE_CHANCE` | 30 | Sabotage threshold; rolled as `randint(0,100) < 30`, so ~29.7% chance to destroy a building level |

## Cooldowns, protection, social
| Constant | Value | Meaning |
|---|---|---|
| `ATTACK_COOLDOWN` | 1800 s | 30-min cooldown per attack target |
| `NEWBIE_PROTECTION_SECONDS` | 86400 | 24h [shield](protection.md) |
| `MAX_CHAT_LENGTH` | 200 | [Tavern](tavern.md) message length |
| `MAX_DM_LENGTH` | 500 | Private message length |

## Alliances
| Constant | Value | Meaning |
|---|---|---|
| `ALLIANCE_CREATE_COST` | 2000 | Gold to found an [alliance](alliances.md) |
| `MAX_ALLIANCE_MEMBERS` | 10 | Member cap |
| `ALLIANCE_TAG_LEN` | 4 | Max tag length |

## Tribes
| Tribe | Value | Effect |
|---|---|---|
| [Highlander](ref_tribes/highlander.md) | 1.11 | +11% combat damage |
| [Merchant](ref_tribes/merchant.md) | 1.08 | +8% gold income |
| [Builder](ref_tribes/builder.md) | 0.70 | −30% building cost |
| [Ironborn](ref_tribes/ironborn.md) | 0.92 | −8% army gold upkeep |

## Admin & assets
Not gameplay tunables, but defined in `config.py`:
| Setting | Meaning |
|---|---|
| `ADMIN_ID` | Telegram id of the bot owner ([Admin Console](admin.md)) |
| `ADMIN_TRIGGER` | Slash trigger that opens the [admin console](admin.md) (`/admin01`) |
| `API_TOKEN` | Telegram Bot API token |
| `AVATAR_IDS` | Seed list of [avatar](profiles.md) `file_id`s (runtime list lives in `meta.avatars`, admin-swappable) |

## See also
[00_INDEX](00_INDEX.md) · [Economy](economy.md) · [Combat](combat.md) · [Buildings](buildings.md)

---
Source: `config.py` (all constants), `database.py` (starting gold default, `meta.avatars`).
