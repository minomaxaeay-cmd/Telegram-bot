# database.py — Iron Dominion persistence (multi-currency economy, blessings, avatars).
# Co-authored with CoCo
import sqlite3
import time
import random
import string
import json
from . import config

def get_db():
    conn = sqlite3.connect(config.DB_NAME, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # 1. Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        game_id TEXT UNIQUE,
        username TEXT,
        display_name TEXT DEFAULT NULL,
        tribe TEXT DEFAULT NULL,
        avatar_id TEXT DEFAULT NULL,
        setup_complete INTEGER DEFAULT 0,
        joined_date REAL,
        gold REAL DEFAULT 1000.0,
        last_update REAL,
        state TEXT DEFAULT NULL,
        stance TEXT DEFAULT 'standard',  -- <--- NEW COLUMN HERE
        banned INTEGER DEFAULT 0,        -- admin lockout flag
        protection_waived INTEGER DEFAULT 0  -- player ended newbie shield early
    )''')

    # 2. Buildings
    c.execute('''CREATE TABLE IF NOT EXISTS buildings (
        user_id INTEGER,
        b_type TEXT,
        level INTEGER,
        PRIMARY KEY (user_id, b_type)
    )''')

    # 3. Units
    c.execute('''CREATE TABLE IF NOT EXISTS units (
        user_id INTEGER,
        u_type TEXT,
        count INTEGER,
        PRIMARY KEY (user_id, u_type)
    )''')

    # 4. Reports
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        timestamp REAL
    )''')

    # 5. Cooldowns
    c.execute('''CREATE TABLE IF NOT EXISTS cooldowns (
        user_id INTEGER,
        target_id INTEGER,
        timestamp REAL,
        PRIMARY KEY (user_id, target_id)
    )''')

    # 6. Chat
    c.execute('''CREATE TABLE IF NOT EXISTS chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        game_id TEXT,
        message TEXT,
        timestamp REAL
    )''')

    # 7. Alliances
    c.execute('''CREATE TABLE IF NOT EXISTS alliances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        tag TEXT UNIQUE,
        leader_id INTEGER,
        created_at REAL
    )''')

    # 8. Meta (key/value store for season tracking)
    c.execute('''CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    # 9. Hall of Fame (season winners archive)
    c.execute('''CREATE TABLE IF NOT EXISTS hall_of_fame (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        season INTEGER,
        game_id TEXT,
        display_name TEXT,
        score INTEGER,
        recorded_at REAL
    )''')

    # 10. Blessings (Faith sink) — one active row per (user, effect). Temporary buffs
    #     bought with Faith; expire at `expires_at` (epoch seconds). See config.BLESSING_DEFS.
    c.execute('''CREATE TABLE IF NOT EXISTS blessings (
        user_id INTEGER,
        effect TEXT,
        expires_at REAL,
        PRIMARY KEY (user_id, effect)
    )''')


    # Migration: Add display_name column if database already exists
    try:
        c.execute("ALTER TABLE users ADD COLUMN display_name TEXT DEFAULT NULL")
    except:
        pass  # Column already exists, ignore error

    # Migration: Add stance column if database already exists
    try:
        c.execute("ALTER TABLE users ADD COLUMN stance TEXT DEFAULT 'standard'")
    except:
        pass  # Column already exists, ignore error

    # Migration: Alliance membership
    try:
        c.execute("ALTER TABLE users ADD COLUMN alliance_id INTEGER DEFAULT NULL")
    except:
        pass

    # Migration: Battle record + seasonal score
    try:
        c.execute("ALTER TABLE users ADD COLUMN wins INTEGER DEFAULT 0")
    except:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN losses INTEGER DEFAULT 0")
    except:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN season_score INTEGER DEFAULT 0")
    except:
        pass

    # Migration: Renown (MG2 prestige track) — lifetime, never-decreasing score
    # earned from real combat, scaled by defender strength. Drives a tiny,
    # capped income perk (see config.RENOWN_*).
    try:
        c.execute("ALTER TABLE users ADD COLUMN renown INTEGER DEFAULT 0")
    except:
        pass

    # Migration: Admin ban lockout flag
    try:
        c.execute("ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0")
    except:
        pass

    # Migration: Player-initiated early end of newbie protection
    try:
        c.execute("ALTER TABLE users ADD COLUMN protection_waived INTEGER DEFAULT 0")
    except:
        pass

    # Migration: Multi-currency economy (Iron / Grain / Faith). New resources beyond
    # gold. Defaults seed existing rows with the new-lord starting stockpile so old
    # test accounts are not stranded at 0. See config.STARTING_* and config.CURRENCIES.
    try:
        c.execute(f"ALTER TABLE users ADD COLUMN iron REAL DEFAULT {config.STARTING_IRON}")
    except:
        pass
    try:
        c.execute(f"ALTER TABLE users ADD COLUMN grain REAL DEFAULT {config.STARTING_GRAIN}")
    except:
        pass
    try:
        c.execute(f"ALTER TABLE users ADD COLUMN faith REAL DEFAULT {config.STARTING_FAITH}")
    except:
        pass

    # Seed season metadata if missing
    c.execute("INSERT OR IGNORE INTO meta (key, value) VALUES ('season', '1')")
    c.execute("INSERT OR IGNORE INTO meta (key, value) VALUES ('season_start', ?)", (str(time.time()),))

    # Seed the bot's avatar image list (admin-swappable, persisted in meta as JSON,
    # seeded once from config.AVATAR_IDS). See get_avatars/set_avatar.
    c.execute("INSERT OR IGNORE INTO meta (key, value) VALUES ('avatars', ?)",
              (json.dumps(config.AVATAR_IDS),))

    conn.commit()
    conn.close()

# --- UNIQUE ID GENERATOR ---
def generate_unique_id():
    """Generates a unique ID like 'AKL-0H2'."""
    conn = get_db()
    c = conn.cursor()

    chars = string.ascii_uppercase + string.digits

    while True:
        part1 = ''.join(random.choices(chars, k=3))
        part2 = ''.join(random.choices(chars, k=3))
        new_id = f"{part1}-{part2}"

        c.execute("SELECT 1 FROM users WHERE game_id = ?", (new_id,))
        if not c.fetchone():
            conn.close()
            return new_id

# --- USER MANAGEMENT ---
def get_user(user_id, username="Unknown"):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()

    now = time.time()

    if not user:
        game_id = generate_unique_id()
        # INITIAL ENDOWMENT (MG4): new lords start with gold REAL DEFAULT 1000.0
        # (schema). This one-time grant is the economy's declared starting balance.
        c.execute('''INSERT INTO users
            (user_id, game_id, username, joined_date, last_update)
            VALUES (?, ?, ?, ?, ?)''',
            (user_id, game_id, username, now, now))

        for b in config.BUILDINGS:
            lvl = 1 if b in ["castle", "gold_mine"] else 0
            c.execute("INSERT INTO buildings VALUES (?, ?, ?)", (user_id, b, lvl))
        for u in config.UNITS:
            c.execute("INSERT INTO units VALUES (?, ?, 0)", (user_id, u))

        conn.commit()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()

    # Calculate Income (multi-currency: gold, iron, grain, faith)
    last_update = user['last_update']
    elapsed_seconds = now - last_update
    if elapsed_seconds > 86400: elapsed_seconds = 86400

    if elapsed_seconds > 10:
        minutes = elapsed_seconds / 60

        # Building levels that drive production (DECLARED SOURCES, MG4).
        c.execute("SELECT b_type, level FROM buildings WHERE user_id = ?", (user_id,))
        blvl = {r['b_type']: r['level'] for r in c.fetchall()}
        mine_lvl   = blvl.get('gold_mine', 0)
        iron_lvl   = blvl.get('iron_mine', 0)
        farm_lvl   = blvl.get('farm', 0)
        chapel_lvl = blvl.get('chapel', 0)

        # --- GOLD (SOURCE: gold mine) ---
        gold_income = minutes * (mine_lvl * 5)
        if user['tribe'] == 'merchant':
            gold_income *= config.TRIBES['merchant']['value']
        # MG2 Renown perk: a stupidly small, hard-capped income bonus (max +2.5%).
        # Gold only — never touches the other resources or combat.
        renown = user['renown'] if 'renown' in user.keys() else 0
        renown_tiers = renown // config.RENOWN_PER_TIER
        renown_perk = min(renown_tiers * config.RENOWN_PERK_PER_TIER, config.RENOWN_PERK_CAP)
        gold_income *= (1 + renown_perk)

        # --- IRON (SOURCE: iron mine) — stockpile resource, no upkeep ---
        iron_income = minutes * (iron_lvl * config.IRON_PER_MINE_LVL)

        # --- GRAIN (SOURCE: farm) — boosted by an active Harvest blessing if any ---
        grain_mult = _active_blessing_value(c, user_id, now, 'grain', 1.0)
        grain_income = minutes * (farm_lvl * config.GRAIN_PER_FARM_LVL) * grain_mult

        # --- FAITH (SOURCE: chapel) — slow prestige resource ---
        faith_income = minutes * (chapel_lvl * config.FAITH_PER_CHAPEL_LVL)

        # --- UPKEEP (SINKS): gold upkeep + grain (food) upkeep ---
        c.execute("SELECT u_type, count FROM units WHERE user_id = ?", (user_id,))
        unit_rows = c.fetchall()
        gold_upkeep = 0.0
        grain_upkeep = 0.0
        for row in unit_rows:
            gold_upkeep  += row['count'] * config.UPKEEP_PER_UNIT.get(row['u_type'], 0) * minutes
            grain_upkeep += row['count'] * config.GRAIN_UPKEEP_PER_UNIT.get(row['u_type'], 0) * minutes
        # Ironborn tribe: efficient forges => cheaper army gold upkeep (steady-state edge).
        if user['tribe'] == 'ironborn':
            gold_upkeep *= config.TRIBES['ironborn']['value']

        def _cur(field, fallback):
            return user[field] if field in user.keys() and user[field] is not None else fallback
        cur_iron  = _cur('iron',  config.STARTING_IRON)
        cur_grain = _cur('grain', config.STARTING_GRAIN)
        cur_faith = _cur('faith', config.STARTING_FAITH)

        new_gold  = user['gold'] + gold_income - gold_upkeep
        new_iron  = cur_iron + iron_income
        new_grain = cur_grain + grain_income - grain_upkeep
        new_faith = cur_faith + faith_income

        # --- DESERTION (SINK): unfed/unpaid troops desert. A SINGLE bounded desertion
        # (<= DESERTION_CAP per tick) driven by the WORSE of the gold/grain shortfalls,
        # so the two upkeep rails never double-punish. Floored-negative balances are
        # destroyed (declared sink); iron/faith have no upkeep but are floored defensively.
        gold_ratio  = min(1.0, max(0.0, -new_gold)  / max(gold_upkeep, 1))
        grain_ratio = min(1.0, max(0.0, -new_grain) / max(grain_upkeep, 1))
        desert_fraction = config.DESERTION_CAP * max(gold_ratio, grain_ratio)
        if desert_fraction > 0:
            for row in unit_rows:
                if row['count'] <= 0:
                    continue
                deserters = int(row['count'] * desert_fraction)
                if deserters > 0:
                    c.execute("UPDATE units SET count = count - ? WHERE user_id = ? AND u_type = ?",
                              (deserters, user_id, row['u_type']))

        new_gold  = max(0.0, new_gold)
        new_grain = max(0.0, new_grain)
        new_iron  = max(0.0, new_iron)
        new_faith = max(0.0, new_faith)

        c.execute("UPDATE users SET gold = ?, iron = ?, grain = ?, faith = ?, last_update = ? WHERE user_id = ?",
                  (new_gold, new_iron, new_grain, new_faith, now, user_id))

        conn.commit()

        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()

    conn.close()
    return dict(user)

def get_user_by_game_id(game_id):
    """Finds a user by their Unique Game ID (XXX-XXX)."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE game_id = ? AND setup_complete = 1", (game_id,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

# --- HELPER FUNCTIONS ---
def get_buildings(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT b_type, level FROM buildings WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return {row['b_type']: row['level'] for row in rows}

def get_units(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT u_type, count FROM units WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return {row['u_type']: row['count'] for row in rows}

# --- MULTI-CURRENCY HELPERS (Iron / Grain / Faith) ---
def _active_blessing_value(c, user_id, now, effect, default):
    """Internal: given an OPEN cursor, return the multiplier value of an active
    blessing of `effect` (combat/grain/defense), else `default`. Expired rows are
    treated as inactive. See config.BLESSING_DEFS."""
    try:
        c.execute("SELECT expires_at FROM blessings WHERE user_id = ? AND effect = ?",
                  (user_id, effect))
        row = c.fetchone()
    except sqlite3.OperationalError:
        return default  # blessings table missing on a very old DB
    if row and row['expires_at'] and row['expires_at'] > now:
        for b in config.BLESSING_DEFS.values():
            if b['effect'] == effect:
                return b['value']
    return default

def get_active_blessings(user_id):
    """Returns {effect: expires_at} for the user's currently-active blessings."""
    now = time.time()
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT effect, expires_at FROM blessings WHERE user_id = ? AND expires_at > ?",
                  (user_id, now))
        rows = c.fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return {r['effect']: r['expires_at'] for r in rows}

def get_blessing_combat_mult(user_id):
    """Outgoing-damage multiplier from an active Zeal blessing (1.0 if none).
    Read by the bot before a battle and passed into simulate_battle."""
    now = time.time()
    conn = get_db()
    c = conn.cursor()
    val = _active_blessing_value(c, user_id, now, 'combat', 1.0)
    conn.close()
    return val

def get_blessing_defense_mult(user_id):
    """Incoming-damage 'keep' multiplier from an active Ward blessing (1.0 if none;
    e.g. 0.90 => takes 10% less damage when defending)."""
    now = time.time()
    conn = get_db()
    c = conn.cursor()
    val = _active_blessing_value(c, user_id, now, 'defense', 1.0)
    conn.close()
    return val

def buy_blessing(user_id, blessing_key):
    """Spend Faith to activate a temporary blessing. DECLARED SINK (MG4): Faith is
    destroyed. Only one blessing per effect; buying again refreshes the timer.
    Returns (success, message)."""
    bdef = config.BLESSING_DEFS.get(blessing_key)
    if not bdef:
        return False, "Unknown blessing."
    now = time.time()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT faith FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    cur_faith = (row['faith'] if row and row['faith'] is not None else 0.0)
    if cur_faith < bdef['faith']:
        conn.close()
        return False, f"Need {bdef['faith']} ✝️ Faith (you have {int(cur_faith)})."
    c.execute("UPDATE users SET faith = faith - ? WHERE user_id = ?", (bdef['faith'], user_id))
    c.execute("INSERT INTO blessings (user_id, effect, expires_at) VALUES (?, ?, ?) "
              "ON CONFLICT(user_id, effect) DO UPDATE SET expires_at = excluded.expires_at",
              (user_id, bdef['effect'], now + bdef['duration']))
    conn.commit()
    conn.close()
    return True, f"{bdef['name']} active!"

def spend_resources(user_id, gold=0, iron=0, grain=0, faith=0):
    """Atomically debit a multi-currency cost (used by recruitment / siege). Verifies
    the user can afford ALL currencies first. DECLARED SINK (MG4). Returns (ok, msg)."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT gold, iron, grain, faith FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, "User not found."
    have = {k: (row[k] if row[k] is not None else 0.0) for k in ("gold", "iron", "grain", "faith")}
    need = {"gold": gold, "iron": iron, "grain": grain, "faith": faith}
    for k, v in need.items():
        if have[k] < v:
            conn.close()
            emoji = config.CURRENCIES[k]['emoji']
            return False, f"Not enough {emoji} {config.CURRENCIES[k]['name']} (need {int(v)}, have {int(have[k])})."
    c.execute("UPDATE users SET gold = gold - ?, iron = iron - ?, grain = grain - ?, faith = faith - ? "
              "WHERE user_id = ?", (gold, iron, grain, faith, user_id))
    conn.commit()
    conn.close()
    return True, "ok"

def add_chat_message(user_id, username, game_id, message):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO chat (user_id, username, game_id, message, timestamp) VALUES (?, ?, ?, ?, ?)",
              (user_id, username, game_id, message[:config.MAX_CHAT_LENGTH], time.time()))
    conn.commit()
    conn.close()

def get_chat_messages(limit=5):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, username, game_id, message FROM chat ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows[::-1]

def get_tavern_user_ids(exclude_user_id=None):
    conn = get_db()
    c = conn.cursor()
    if exclude_user_id is None:
        c.execute("SELECT user_id FROM users WHERE state = 'chatting' AND setup_complete = 1 AND banned = 0")
    else:
        c.execute("SELECT user_id FROM users WHERE state = 'chatting' AND setup_complete = 1 AND banned = 0 AND user_id != ?",
                  (exclude_user_id,))
    rows = c.fetchall()
    conn.close()
    return [row['user_id'] for row in rows]

# --- META / SEASON HELPERS ---
def get_meta(key, default=None):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM meta WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row['value'] if row else default

def set_meta(key, value):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO meta (key, value) VALUES (?, ?) "
              "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(value)))
    conn.commit()
    conn.close()

def get_current_season():
    try:
        return int(get_meta('season', '1'))
    except (TypeError, ValueError):
        return 1

# --- BATTLE RECORD ---
def record_battle_result(winner_id, loser_id, points=10, renown_gain=0):
    """Increments wins/losses and seasonal score for both combatants.
    Also awards lifetime Renown (MG2) to the winner."""
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET wins = COALESCE(wins, 0) + 1, "
              "season_score = COALESCE(season_score, 0) + ?, "
              "renown = COALESCE(renown, 0) + ? WHERE user_id = ?",
              (points, max(0, int(renown_gain)), winner_id))
    c.execute("UPDATE users SET losses = COALESCE(losses, 0) + 1 WHERE user_id = ?", (loser_id,))
    conn.commit()
    conn.close()

def award_renown(user_id, amount):
    """Adds lifetime Renown (MG2) — never decreases. Used by non-battle wins
    such as successful heists."""
    if amount <= 0:
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET renown = COALESCE(renown, 0) + ? WHERE user_id = ?",
              (int(amount), user_id))
    conn.commit()
    conn.close()

# --- LEADERBOARD ---
def get_leaderboard(limit=10):
    """Returns top players for the current season ordered by season_score."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT user_id, game_id, username, display_name, tribe,
                        COALESCE(season_score, 0) AS season_score,
                        COALESCE(wins, 0) AS wins, COALESCE(losses, 0) AS losses
                 FROM users WHERE setup_complete = 1
                 ORDER BY season_score DESC, wins DESC LIMIT ?''', (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_renown_leaderboard(limit=10):
    """Returns top players by lifetime Renown (MG2 prestige track)."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT user_id, game_id, username, display_name, tribe,
                        COALESCE(renown, 0) AS renown
                 FROM users WHERE setup_complete = 1
                 ORDER BY renown DESC LIMIT ?''', (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def start_new_season():
    """Archives current top players into hall_of_fame, then resets the scoreboard.
    Kingdoms (gold, buildings, army) are left untouched."""
    season = get_current_season()
    leaders = get_leaderboard(limit=3)

    conn = get_db()
    c = conn.cursor()
    now = time.time()
    for ldr in leaders:
        if ldr['season_score'] <= 0:
            continue
        name = ldr['display_name'] or ldr['username']
        c.execute('''INSERT INTO hall_of_fame (season, game_id, display_name, score, recorded_at)
                     VALUES (?, ?, ?, ?, ?)''',
                  (season, ldr['game_id'], name, ldr['season_score'], now))
    # Reset the scoreboard
    c.execute("UPDATE users SET season_score = 0, wins = 0, losses = 0")
    new_season = season + 1
    c.execute("INSERT INTO meta (key, value) VALUES ('season', ?) "
              "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (str(new_season),))
    c.execute("INSERT INTO meta (key, value) VALUES ('season_start', ?) "
              "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (str(now),))
    conn.commit()
    conn.close()
    return new_season, leaders

def get_hall_of_fame(limit=10):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT season, display_name, game_id, score FROM hall_of_fame ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- ALLIANCE HELPERS ---
def get_alliance(alliance_id):
    if not alliance_id:
        return None
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM alliances WHERE id = ?", (alliance_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_alliance_by_tag(tag):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM alliances WHERE tag = ?", (tag.upper(),))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_alliance_members(alliance_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT user_id, game_id, username, display_name
                 FROM users WHERE alliance_id = ? AND setup_complete = 1''', (alliance_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def count_alliance_members(alliance_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM users WHERE alliance_id = ?", (alliance_id,))
    n = c.fetchone()['n']
    conn.close()
    return n

def create_alliance(leader_id, name, tag):
    """Creates an alliance and charges the founder. Returns (success, message/alliance_id)."""
    name = name.strip()
    tag = tag.strip().upper()
    conn = get_db()
    c = conn.cursor()

    # Verify funds & not already in an alliance
    c.execute("SELECT gold, alliance_id FROM users WHERE user_id = ?", (leader_id,))
    row = c.fetchone()
    if row is None:
        conn.close()
        return False, "User not found."
    if row['alliance_id']:
        conn.close()
        return False, "You are already in an alliance."
    if row['gold'] < config.ALLIANCE_CREATE_COST:
        conn.close()
        return False, f"You need {config.ALLIANCE_CREATE_COST} Gold to found an alliance."

    # Uniqueness checks
    c.execute("SELECT 1 FROM alliances WHERE name = ? OR tag = ?", (name, tag))
    if c.fetchone():
        conn.close()
        return False, "That name or tag is already taken."

    now = time.time()
    c.execute("INSERT INTO alliances (name, tag, leader_id, created_at) VALUES (?, ?, ?, ?)",
              (name, tag, leader_id, now))
    alliance_id = c.lastrowid
    # DECLARED SINK (MG4): the alliance founding fee is destroyed, not transferred.
    c.execute("UPDATE users SET gold = gold - ?, alliance_id = ? WHERE user_id = ?",
              (config.ALLIANCE_CREATE_COST, alliance_id, leader_id))
    conn.commit()
    conn.close()
    return True, alliance_id

def join_alliance(user_id, alliance_id):
    """Adds a user to an alliance. Returns (success, message)."""
    if count_alliance_members(alliance_id) >= config.MAX_ALLIANCE_MEMBERS:
        return False, "That alliance is full."
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT alliance_id FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row and row['alliance_id']:
        conn.close()
        return False, "You are already in an alliance. Leave it first."
    c.execute("UPDATE users SET alliance_id = ? WHERE user_id = ?", (alliance_id, user_id))
    conn.commit()
    conn.close()
    return True, "Joined."

def leave_alliance(user_id):
    """Removes a user from their alliance. If the leader leaves, the alliance is disbanded.
    Returns (success, message)."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT alliance_id FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row or not row['alliance_id']:
        conn.close()
        return False, "You are not in an alliance."
    alliance_id = row['alliance_id']

    c.execute("SELECT leader_id FROM alliances WHERE id = ?", (alliance_id,))
    arow = c.fetchone()
    if arow and arow['leader_id'] == user_id:
        # Leader disbands: detach all members and delete the alliance
        c.execute("UPDATE users SET alliance_id = NULL WHERE alliance_id = ?", (alliance_id,))
        c.execute("DELETE FROM alliances WHERE id = ?", (alliance_id,))
        conn.commit()
        conn.close()
        return True, "disbanded"

    c.execute("UPDATE users SET alliance_id = NULL WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True, "left"

def are_allies(user_id_a, user_id_b):
    """True if both users share the same (non-null) alliance."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT alliance_id FROM users WHERE user_id IN (?, ?)", (user_id_a, user_id_b))
    rows = c.fetchall()
    conn.close()
    if len(rows) < 2:
        return False
    a = rows[0]['alliance_id']
    b = rows[1]['alliance_id']
    return a is not None and a == b

# --- ADMIN: BAN / UNBAN ---
def is_banned(user_id):
    """True if the user is currently banned (admin lockout)."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
    except sqlite3.OperationalError:
        row = None  # column missing on a very old DB; treat as not banned
    conn.close()
    return bool(row['banned']) if row and row['banned'] is not None else False

def set_banned(user_id, banned):
    """Sets/clears the ban flag for a user. Returns True if a row was updated."""
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET banned = ? WHERE user_id = ?", (1 if banned else 0, user_id))
    conn.commit()
    changed = c.rowcount
    conn.close()
    return changed > 0

# --- PLAYER: NEWBIE PROTECTION WAIVER ---
def waive_protection(user_id):
    """Permanently ends a player's newbie shield early (player-initiated)."""
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET protection_waived = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# --- ADMIN: BROADCAST TARGETS ---
def get_all_user_ids(only_setup=True):
    """Returns the user_id of every active lord for broadcasts. Excludes banned
    lords (full lockout), and is setup-complete-only by default."""
    conn = get_db()
    c = conn.cursor()
    if only_setup:
        c.execute("SELECT user_id FROM users WHERE setup_complete = 1 AND banned = 0")
    else:
        c.execute("SELECT user_id FROM users WHERE banned = 0")
    rows = c.fetchall()
    conn.close()
    return [r['user_id'] for r in rows]

# --- ADMIN: BOT IMAGE ASSETS (avatars) ---
def get_avatars():
    """Returns the effective list of bot avatar file_ids. Stored in meta as JSON
    (admin-swappable); falls back to config.AVATAR_IDS if unset/corrupt."""
    raw = get_meta('avatars', None)
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, list) and data:
                return data
        except (ValueError, TypeError):
            pass
    return list(config.AVATAR_IDS)

def set_avatar(index, file_id):
    """Replaces the avatar at the given slot index with a new file_id.
    Returns True on success, False if the index is out of range."""
    avatars = get_avatars()
    if not isinstance(index, int) or index < 0 or index >= len(avatars):
        return False
    avatars[index] = file_id
    set_meta('avatars', json.dumps(avatars))
    return True

def replace_all_avatars(file_ids):
    """Replace the ENTIRE avatar gallery with a new list of photo file_ids (admin bulk
    re-upload — e.g. after switching bot tokens so the bundled file_ids no longer send).
    Persists to meta.avatars. Returns the number of avatars stored (0 if none valid)."""
    clean = [f for f in (file_ids or []) if isinstance(f, str) and f.strip()]
    if not clean:
        return 0
    set_meta('avatars', json.dumps(clean))
    return len(clean)