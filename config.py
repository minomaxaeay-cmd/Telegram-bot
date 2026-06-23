# config.py

# --- BOT CONFIGURATION ---
API_TOKEN = '8547383974:AAFR6HtTiKDBZu6lgPiRgfjypRZS59GL4yE'
SECRET_URL_PATH = "webhook_endpoint_x932k"
DB_NAME = "/home/tgbotstelegram02/mysite/myTelegramBots/IronDominion/medieval_war.db"
ADMIN_ID = 7293094714
ADMIN_TRIGGER = "/admin01"

# --- ASSETS ---
AVATAR_IDS = [
    "AgACAgQAAxkBAAIB6Gkg4paowPR90s7EhW-zw30LpxKiAAIwDGsb2tUJUcoH3tPLYne1AQADAgADeQADNgQ", # 1st
    "AgACAgQAAxkBAAIB_Gkg-kSLWkMtS0S0FCpNq4YY4c9IAAIUDGsbMbsIUVM8SpAZQ_tDAQADAgADeQADNgQ", # 2nd
    "AgACAgQAAxkBAAIB_2kg-oIjP3oMO-1cAAEYEX7-bj4cVwACFQxrGzG7CFECrRojbXAn3wEAAwIAA3kAAzYE", # 3rd
    "AgACAgQAAxkBAAICAmkg-pkT-VbfIpevV8VOeDDkiOFqAAIWDGsbMbsIUWtT21k-sjJsAQADAgADeQADNgQ", # 4th
    "AgACAgQAAxkBAAICBWkg-qtTIyVrwXvMsMN4Mxr49MfPAAIXDGsbMbsIUQhs8XZS1Z8cAQADAgADeQADNgQ", # 5th
    "AgACAgQAAxkBAAICCGkg-s0aCqk9Ou6jwbAy3NccMT2PAAIYDGsbMbsIUZqrqBjJWjhgAQADAgADeQADNgQ", # 6th
    "AgACAgQAAxkBAAICC2kg-uLwCAmCD5EnSyy5x_S0nWYLAAIZDGsbMbsIUUQJM-yJl-R_AQADAgADeQADNgQ", # 7th
    "AgACAgQAAxkBAAICDmkg-ve-b5sNkthLELeMiRBzRQGxAAIaDGsbMbsIUdzKug2SFIzuAQADAgADeQADNgQ", # 8th
    "AgACAgQAAxkBAAICEWkg-wu6EVhyuBJS7tAhK5nzMBwpAAIbDGsbMbsIUWTI_zkJAAGhOQEAAwIAA3kAAzYE", # 9th
    "AgACAgQAAxkBAAICFGkg-x9vJ_QRGhKMp8AoghlzaH33AAIcDGsbMbsIUSCtbjuIR72OAQADAgADeQADNgQ"  # 10th
]

# --- TRIBES ---
# Chosen permanently at account creation. REBALANCED (TASK 1): each tribe specializes
# in a DIFFERENT axis of the (now four-currency) economy, tuned via the race-then-battle
# simulation (criteria_evaluations/simulate_tribe_race.py) so no tribe dominates — the
# long-run win-rate spread across all tribes is held under TRIBE_SPREAD_CEILING (10%).
# Magnitudes here are the sim-tuned values (see balance_overhaul / wiki/ref_tribes).
TRIBES = {
    "highlander": {
        "name": "Highlanders 🪓",
        "desc": "+11% Combat Damage",
        "bonus_type": "combat",
        "value": 1.11
    },
    "merchant": {
        "name": "Merchants ⚖️",
        "desc": "+8% Gold Income",
        "bonus_type": "gold",
        "value": 1.08
    },
    "builder": {
        "name": "Builders 🔨",
        "desc": "-30% Building Cost",
        "bonus_type": "build",
        "value": 0.70
    },
    "ironborn": {
        "name": "Ironborn ⛓️",
        "desc": "-8% Army Upkeep",
        "bonus_type": "upkeep",
        "value": 0.92
    }
}

# --- GAME CONSTANTS ---
COMBAT_WIDTH = 40
MAX_ROUNDS = 25              # Increased to prevent battles ending in draws too often
ATTACK_COOLDOWN = 1800       # Increased to 30 Minutes
SPY_COOLDOWN = 600           # 10 Minutes between espionage missions on the same target
MAX_CHAT_LENGTH = 200
MAX_DM_LENGTH = 500
LOOT_PERCENTAGE = 0.30       # Winner steals 30% of exposed gold
SAFE_GOLD_PER_LEVEL = 1000   # Gold protected per Castle Level (Vault)

# --- NEWBIE PROTECTION ---
NEWBIE_PROTECTION_SECONDS = 86400   # 24h shield from being attacked/spied (and from attacking)

# --- ARMY UPKEEP (gold per unit per minute) ---
# Mine income must cover this; otherwise troops desert.
UPKEEP_PER_UNIT = {
    "peasant": 0.1,
    "man_at_arms": 0.5,
    "knight": 2.0,
    "pikeman": 1.0,
    "spy": 0.5
}
DESERTION_CAP = 0.10         # Max fraction of army lost to desertion in a single tick

# =============================================================================
# --- MULTI-CURRENCY ECONOMY (Iron / Grain / Faith) ---
# The economy is no longer single-resource. Gold remains the universal currency
# (buildings, base recruitment, loot), and three authentic medieval resources add
# strategic depth WITHOUT touching the gold building-horizon math (MG0/MG2/MG3):
#   IRON  ⛓️ — military material. Produced by the Iron Mine; spent (with gold) to
#               recruit/forge soldiers and to build siege engines.
#   GRAIN 🌾 — food. Produced by the Farm; consumed every tick as army FOOD UPKEEP.
#               Run out and unfed troops starve (desert), so army SIZE is gated by
#               your farms, not just your gold.
#   FAITH ✝️ — devotion/prestige. Produced slowly by the Chapel; spent on temporary,
#               hard-bounded Blessings (no permanent power creep / pay-to-win).
# Every currency is a CLOSED system (MG4): one declared SOURCE building, declared
# SINKS, and only zero-sum PvP transfers. See balance_overhaul/MG4 + wiki/currencies.md.
# =============================================================================
CURRENCIES = {
    "gold":  {"name": "Gold",  "emoji": "💰"},
    "iron":  {"name": "Iron",  "emoji": "⛓️"},
    "grain": {"name": "Grain", "emoji": "🌾"},
    "faith": {"name": "Faith", "emoji": "✝️"},
}

# New lords' starting stockpile of the new resources (gold endowment stays 1000 in
# the DB schema). Small buffers so a new lord can field a first army before they have
# built the matching production buildings — then production must catch up (a sink).
STARTING_IRON  = 100.0
STARTING_GRAIN = 200.0
STARTING_FAITH = 0.0

# PRODUCTION (per building level, per minute). DECLARED SOURCES (MG4).
# Tuned so that, at equal building level, gold and iron bind army growth at a similar
# rate (gold:iron unit-cost ratio ~10:1 ⇒ iron rate ~ gold rate / 10 * unit mix), and
# grain comfortably feeds a mine-sustainable army with a farm at comparable level.
IRON_PER_MINE_LVL    = 2.0    # Iron Mine: iron/min = iron_mine_level * 2
GRAIN_PER_FARM_LVL   = 6.0    # Farm:      grain/min = farm_level * 6
FAITH_PER_CHAPEL_LVL = 0.5    # Chapel:    faith/min = chapel_level * 0.5 (slow prestige)

# RECRUITMENT IRON COST (per unit). DECLARED SINK (MG4). Peasants are an unarmoured
# levy (no iron); spies need a little for tools; armoured troops need progressively
# more (≈12% of their gold cost — see game_balance.iron_cost()). Gold cost is unchanged.
IRON_COST_PER_UNIT = {
    "peasant":      0,
    "man_at_arms": 15,
    "pikeman":     30,
    "knight":      60,
    "spy":          5,
}

# FOOD (GRAIN) UPKEEP (gold-style, per unit per minute). DECLARED SINK (MG4).
# Knights (and their horses) eat the most; peasants the least. If a tick's grain
# production + stockpile cannot cover this, unfed troops STARVE (desert), bounded by
# DESERTION_CAP — exactly mirroring the gold-upkeep desertion rule.
GRAIN_UPKEEP_PER_UNIT = {
    "peasant":     0.2,
    "man_at_arms": 0.4,
    "pikeman":     0.5,
    "knight":      1.0,
    "spy":         0.3,
}

# --- BLESSINGS (Faith sink) ---
# Temporary, hard-bounded buffs bought with Faith. They expire (duration seconds),
# never stack with themselves, and are small enough not to break MG5 non-domination
# (the combat blessing equals the old Highlander magnitude, which MG5 already cleared).
# Only ONE blessing of each effect can be active. DECLARED SINK (MG4): Faith is spent
# and destroyed when a blessing is bought.
BLESSING_DEFS = {
    "zeal":    {"name": "Blessing of Zeal ⚔️",   "faith": 50, "duration": 3600,
                "effect": "combat", "value": 1.10,
                "desc": "+10% combat damage (attack & defend) for 1h"},
    "harvest": {"name": "Blessing of Plenty 🌾", "faith": 40, "duration": 3600,
                "effect": "grain",  "value": 1.25,
                "desc": "+25% Grain production for 1h"},
    "ward":    {"name": "Blessing of the Ward 🛡️", "faith": 60, "duration": 3600,
                "effect": "defense", "value": 0.90,
                "desc": "-10% incoming damage while defending for 1h"},
}

# =============================================================================
# --- SIEGE WARFARE (the centerpiece mechanism) ---
# Attacking a lord lets you choose RAID (instant field battle, unchanged) or SIEGE,
# a multi-phase assault that is the ONLY way to crack a fortified, walled lord.
#
#   PHASE 1 BOMBARDMENT : siege engines (funded per-assault from gold+iron+grain)
#                         batter the defender's WALLS. The Watchtower returns fire,
#                         destroying some engines. -> walls breached? (+ engines lost)
#   PHASE 2 FIELD BATTLE: the normal simulate_battle. If the walls were BREACHED the
#                         Watchtower fortification is nullified (you are inside).
#   PHASE 3 SACK/REPULSE: win + breach => bigger loot + breach renown; win + walls
#                         held => normal loot; loss => your forces & engines are gone.
#
# DESIGN: engines have ZERO field-combat value (they never enter simulate_battle), so
# a siege needs BOTH engines (break walls) AND a real army (win the field). This keeps
# the unit rock-paper-scissors (MG5) untouched and prevents an all-siege dominant build.
# Engines are CONSUMABLE: their gold+iron+grain cost is a DECLARED sink (MG4); survivors
# are not banked.
# =============================================================================
# Wall hit points scale with the defender's fortification buildings (MG6 coherence).
WALL_BASE            = 100    # every fief has a baseline palisade
WALL_PER_WATCHTOWER  = 60     # +60 wall HP per watchtower level
WALL_PER_CASTLE      = 25     # +25 wall HP per castle level

# Siege engines (consumable). wall_dmg = HP knocked off the wall per bombardment volley
# per engine; field_value 0 => excluded from the field battle. cost is gold/iron/grain.
SIEGE_ENGINES = {
    "battering_ram": {"name": "Battering Ram 🪵", "gold": 120, "iron": 20, "grain": 10, "wall_dmg": 25},
    "trebuchet":     {"name": "Trebuchet 🎯",     "gold": 300, "iron": 40, "grain": 20, "wall_dmg": 60},
}
BOMBARD_VOLLEYS          = 3      # bombardment rounds before the field battle
WT_ENGINE_KILLS_PER_LVL  = 0.20   # engines destroyed per watchtower level per volley

# Sack rewards when the walls are BREACHED and the attacker wins the field.
SIEGE_SACK_LOOT_PCT      = 0.50   # loot 50% of exposed gold (vs LOOT_PERCENTAGE 0.30)
SIEGE_SACK_VAULT_MULT    = 0.50   # breach halves the castle vault -> more gold exposed
SIEGE_BREACH_RENOWN_MULT = 1.5    # +50% renown for a successful breach-and-sack

# --- ALLIANCES ---
ALLIANCE_CREATE_COST = 2000  # Gold cost to found an alliance
MAX_ALLIANCE_MEMBERS = 10
ALLIANCE_TAG_LEN = 4         # Max characters in an alliance tag

# --- RENOWN (MG2 prestige track) ---
# Lifetime score from real combat. Grants a STUPIDLY SMALL, hard-capped income
# perk so it motivates long-term play without affecting balance (never touches
# combat stats). At the cap the perk is only +2.5% gold income.
RENOWN_PER_TIER      = 100     # renown points per perk tier
RENOWN_PERK_PER_TIER = 0.0005  # +0.05% income per tier
RENOWN_PERK_CAP      = 0.025   # hard cap: +2.5% income, ever
# Renown awarded per win, scaled by defender strength (anti newbie-farming):
RENOWN_WIN_DIVISOR   = 50      # renown_gain = max(1, defender_power // this)
RENOWN_HEIST_DIVISOR = 100     # renown_gain = max(1, stolen_gold // this)

# --- COMBAT BUILDINGS (MG6) ---
# Watchtower gives the DEFENDER a bounded damage-reduction in battle, so the
# buildings system and combat are coherent (your fief actually fortifies you).
# Hard-capped to prevent unbeatable turtling.
WATCHTOWER_DEF_BONUS_PER_LVL = 0.02   # -2% incoming damage per watchtower level
WATCHTOWER_DEF_CAP           = 0.30   # never more than -30% total

# Blacksmith "Forge": a symmetric, bounded army-wide damage multiplier (applies
# whether you attack or defend, so no turtling). It is a TECH AXIS / late-game
# gold-sink — once your army nears its sustainable cap, extra gold spent on the
# blacksmith makes your existing army stronger. NOTE: in a fixed-budget snapshot
# pure army still beats army+forge (building cost is exponential); the forge's
# value is as a long-run multiplier on an already-built army.
BLACKSMITH_DMG_PER_LVL = 0.02   # +2% army damage per blacksmith level
BLACKSMITH_DMG_CAP     = 0.25   # capped at +25%

# --- ESPIONAGE SYSTEM ---
SPY_CARRY_CAP = 50        # Max gold one spy can carry back
SPY_VAULT_CAP = 0.15      # (Legacy setting, overriden by new logic but kept for safety)
WATCHTOWER_DETECT = 35
BASE_DETECTION = 20
SABOTAGE_CHANCE = 30

# --- BUILDINGS ---
# MAX_BUILDING_LEVEL: hard cap on every building's level (MG0 prerequisite).
# Rationale (see balance_overhaul/MG0_prerequisites.txt + TUNABLE_ANALYSIS.txt):
# income is LINEAR in mine level (mine_lvl * 5/min) while upgrade cost is
# EXPONENTIAL (base * 1.6^level). Reaching gold_mine level 33 under the fastest
# possible path (all income reinvested, daily login) takes ~11.45 years, so this
# cap makes "maxing the parts that matter" (gold, and therefore army) impossible
# in under 10 years, by design.
MAX_BUILDING_LEVEL = 33

BUILDINGS = {
    "castle": {"name": "Castle 🏰", "cost": 500, "slots": 0, "req": [], "desc": "Increases Max Slots."},
    "gold_mine": {"name": "Gold Mine ⛏️", "cost": 100, "slots": 1, "req": ["castle:1"], "desc": "Generates Gold."},
    "iron_mine": {"name": "Iron Mine ⛓️", "cost": 150, "slots": 1, "req": ["castle:1"], "desc": "Generates Iron (forges your army)."},
    "farm": {"name": "Farm 🌾", "cost": 120, "slots": 1, "req": ["castle:1"], "desc": "Generates Grain (feeds your army)."},
    "chapel": {"name": "Chapel ✝️", "cost": 400, "slots": 1, "req": ["castle:2"], "desc": "Generates Faith (buy Blessings)."},
    "barracks": {"name": "Barracks ⚔️", "cost": 200, "slots": 2, "req": ["gold_mine:1"], "desc": "Unlocks infantry."},
    "blacksmith": {"name": "Blacksmith 🔨", "cost": 800, "slots": 2, "req": ["barracks:3"], "desc": "Unlocks Knights & forges your army (+dmg)."},
    "watchtower": {"name": "Watchtower 👁️", "cost": 300, "slots": 1, "req": ["castle:2"], "desc": "Fortifies your defense in battle (+espionage detection)."}
}

# --- UNITS ---
# MG1: combat stats are DERIVED from the parametric backbone in game_balance.py
# (cost x role-vector / stat-price), with documented exceptions for the
# rock-paper-scissors counters. `org` removed (never used by simulate_battle).
from . import game_balance

UNITS = {
    "peasant":     game_balance.build_unit("peasant",     "Peasant"),
    "man_at_arms": game_balance.build_unit("man_at_arms", "Man-at-Arms"),
    "knight":      game_balance.build_unit("knight",      "Knight"),
    "pikeman":     game_balance.build_unit("pikeman",     "Pikeman"),
    # spy is a non-combat exception (priced separately; excluded from battles).
    "spy": {"name": "Rogue", "cost": 200, "width": 0, "hp": 1, "soft_atk": 0,
            "hard_atk": 0, "piercing": 0, "armor": 0, "hard": 0, "combat_valid": False},
}

# --- STANCES ---
STANCE_STATS = {
    "standard":   {"atk": 1.0, "def": 1.0, "name": "Standard (Balanced)"},
    "aggressive": {"atk": 1.2, "def": 1.1, "name": "Aggressive (Charge)"}, 
    "defensive":  {"atk": 0.9, "def": 0.8, "name": "Defensive (Phalanx)"}, 
    "mobile":     {"atk": 1.0, "def": 1.0, "name": "Mobile (Skirmish)"}    
}