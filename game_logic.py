# game_logic.py
import random
import html
from . import config

def calculate_power_score(buildings):
    """Calculates a vague 'Power Score' for profiles."""
    score = 0
    for b_type, level in buildings.items():
        score += level
    # Castle is worth double points
    score += buildings.get('castle', 1)
    return score

def can_build(user_gold, current_buildings, b_key, tribe):
    b_data = config.BUILDINGS[b_key]

    # 1. Check Slots
    castle_lvl = current_buildings.get("castle", 1)
    max_slots = castle_lvl * 5
    used_slots = sum([config.BUILDINGS[k]["slots"] * lvl for k, lvl in current_buildings.items()])

    if (used_slots + b_data["slots"]) > max_slots:
        return False, f"Not enough space! ({used_slots}/{max_slots}). Upgrade Castle."

    # 2. Check Prerequisites
    for r in b_data["req"]:
        req_name, req_lvl = r.split(":")
        if current_buildings.get(req_name, 0) < int(req_lvl):
            return False, f"Requires {config.BUILDINGS[req_name]['name']} Lv {req_lvl}"

    # 3. Check Cost (With Builder Bonus)
    current_lvl = current_buildings.get(b_key, 0)

    # MG0 hard cap: no building may exceed MAX_BUILDING_LEVEL. This bounds the
    # otherwise-infinite 1.6^level cost curve so time-to-max is finite (>10 yr).
    if current_lvl >= config.MAX_BUILDING_LEVEL:
        return False, f"🏛️ Max level reached (Lv {config.MAX_BUILDING_LEVEL})."

    # DECLARED SINK (MG4): gold spent here is destroyed, not transferred.
    base_cost = int(b_data["cost"] * (1.6 ** current_lvl))

    if tribe == "builder":
        base_cost = int(base_cost * config.TRIBES['builder']['value'])

    if user_gold < base_cost:
        return False, f"Need {base_cost} Gold."

    return True, base_cost

def get_tactical_bonus(atk_stance, def_stance):
    # Rock-Paper-Scissors Logic: Aggressive > Mobile > Defensive > Aggressive
    if atk_stance == "aggressive" and def_stance == "mobile": return 1.15
    if atk_stance == "mobile" and def_stance == "defensive": return 1.15
    if atk_stance == "defensive" and def_stance == "aggressive": return 1.15
    return 1.0

def recruit_cost(unit_key, amount=1):
    """Multi-currency recruitment cost (MG4 declared sink). Gold is the universal
    cost (unchanged); military units ALSO cost Iron (see config.IRON_COST_PER_UNIT).
    Returns {'gold': g, 'iron': i}."""
    g = config.UNITS[unit_key]["cost"] * amount
    i = config.IRON_COST_PER_UNIT.get(unit_key, 0) * amount
    return {"gold": g, "iron": i}

def simulate_battle(atk_army, def_army, atk_tribe, def_tribe, atk_stance="standard", def_stance="standard", def_buildings=None, atk_buildings=None, atk_combat_mult=1.0, def_combat_mult=1.0, def_ward_keep=1.0):
    # 1. DEPLOYMENT & RESERVES
    def create_unit_pool(army_dict, tribe_bonus):
        pool = []
        for k, count in army_dict.items():
            if count <= 0: continue
            if not config.UNITS[k]["combat_valid"]: continue
            for _ in range(count):
                u = config.UNITS[k].copy()
                u["key"] = k
                u["current_hp"] = u["hp"]
                # Apply Highlander Bonus
                if tribe_bonus == "highlander":
                    u["soft_atk"] *= config.TRIBES['highlander']['value']
                    u["hard_atk"] *= config.TRIBES['highlander']['value']
                pool.append(u)
        random.shuffle(pool)
        return pool

    reserves_a = create_unit_pool(atk_army, atk_tribe)
    reserves_b = create_unit_pool(def_army, def_tribe)
    
    # Store initial counts for loss calculation
    atk_start_counts = {k: 0 for k in atk_army}
    for u in reserves_a: atk_start_counts[u['key']] += 1
    
    def_start_counts = {k: 0 for k in def_army}
    for u in reserves_b: def_start_counts[u['key']] += 1

    def fill_frontline(frontline, reserves):
        current_width = sum(u['width'] for u in frontline)
        while reserves and current_width < config.COMBAT_WIDTH:
            u = reserves.pop(0)
            if current_width + u['width'] <= config.COMBAT_WIDTH + 2:
                frontline.append(u)
                current_width += u['width']
            else:
                reserves.insert(0, u) # Too fat, put back
                break
        return frontline

    line_a = []
    line_b = []

    # 2. CALCULATE MULTIPLIERS
    atk_mult_dmg = config.STANCE_STATS[atk_stance]["atk"] * get_tactical_bonus(atk_stance, def_stance)
    atk_mult_mit = config.STANCE_STATS[atk_stance]["def"]
    
    def_mult_dmg = config.STANCE_STATS[def_stance]["atk"] * get_tactical_bonus(def_stance, atk_stance)
    def_mult_mit = config.STANCE_STATS[def_stance]["def"]

    # MG6 — Watchtower fortification: the DEFENDER's watchtower reduces incoming
    # damage (a real, bounded home-defense bonus). Hard-capped to prevent turtling.
    wt_level = (def_buildings or {}).get("watchtower", 0)
    def_fort = min(config.WATCHTOWER_DEF_BONUS_PER_LVL * wt_level, config.WATCHTOWER_DEF_CAP)
    fort_keep = 1.0 - def_fort

    # MG6 — Blacksmith "Forge": symmetric, bounded army-wide damage multiplier.
    # Each side's outgoing damage is scaled by its own blacksmith level (tech axis).
    atk_forge = 1.0 + min(config.BLACKSMITH_DMG_PER_LVL * (atk_buildings or {}).get("blacksmith", 0), config.BLACKSMITH_DMG_CAP)
    def_forge = 1.0 + min(config.BLACKSMITH_DMG_PER_LVL * (def_buildings or {}).get("blacksmith", 0), config.BLACKSMITH_DMG_CAP)

    log = []
    log.append(f"⚔️ <b>Tactics:</b> {atk_stance.title()} vs {def_stance.title()}")
    if get_tactical_bonus(atk_stance, def_stance) > 1.0: log.append(f"🔥 <b>Attacker Bonus!</b> {atk_stance} counters {def_stance}!")
    if get_tactical_bonus(def_stance, atk_stance) > 1.0: log.append(f"🛡️ <b>Defender Bonus!</b> {def_stance} counters {atk_stance}!")
    if def_fort > 0: log.append(f"🏯 <b>Fortified!</b> Watchtower Lv{wt_level} reduces incoming damage by {int(def_fort*100)}%.")

    # 3. BATTLE LOOP
    for r in range(config.MAX_ROUNDS):
        line_a = fill_frontline(line_a, reserves_a)
        line_b = fill_frontline(line_b, reserves_b)
        
        if not line_a or not line_b: break

        # Initialize pending damage
        for u in line_a: u['pending_dmg'] = 0
        for u in line_b: u['pending_dmg'] = 0

        # A attacks B
        for u in line_a:
            target = random.choice(line_b)
            raw_dmg = (u["hard_atk"] * target["hard"]) + (u["soft_atk"] * (1 - target["hard"]))
            actual_dmg = raw_dmg * atk_mult_dmg * def_mult_mit * random.uniform(0.8, 1.2) * fort_keep * atk_forge * atk_combat_mult * def_ward_keep
            if target["armor"] > u["piercing"]: actual_dmg *= 0.5
            target['pending_dmg'] += actual_dmg

        # B attacks A
        for u in line_b:
            target = random.choice(line_a)
            raw_dmg = (u["hard_atk"] * target["hard"]) + (u["soft_atk"] * (1 - target["hard"]))
            actual_dmg = raw_dmg * def_mult_dmg * atk_mult_mit * random.uniform(0.8, 1.2) * def_forge * def_combat_mult
            if target["armor"] > u["piercing"]: actual_dmg *= 0.5
            target['pending_dmg'] += actual_dmg

        # Apply Damage & Remove Dead
        dead_a = []
        for i, u in enumerate(line_a):
            u['current_hp'] -= u['pending_dmg']
            if u['current_hp'] <= 0: dead_a.append(i)
            
        dead_b = []
        for i, u in enumerate(line_b):
            u['current_hp'] -= u['pending_dmg']
            if u['current_hp'] <= 0: dead_b.append(i)
            
        for i in sorted(dead_a, reverse=True): line_a.pop(i)
        for i in sorted(dead_b, reverse=True): line_b.pop(i)

    # 4. RESULTS
    survivors_a = reserves_a + line_a
    survivors_b = reserves_b + line_b
    
    if len(survivors_a) == 0:
        # Attacker army destroyed (even on mutual annihilation) -> assault fails, defender holds
        winner = "Defender"
    elif len(survivors_b) == 0:
        winner = "Attacker"
    else:
        # If time runs out, compare Gold Value remaining
        val_a = sum(config.UNITS[u['key']]['cost'] for u in survivors_a)
        val_b = sum(config.UNITS[u['key']]['cost'] for u in survivors_b)
        winner = "Attacker" if val_a >= val_b else "Defender"

    # Calculate Losses (Dictionary format for DB update)
    atk_survivors_count = {}
    for u in survivors_a: atk_survivors_count[u['key']] = atk_survivors_count.get(u['key'], 0) + 1
    
    def_survivors_count = {}
    for u in survivors_b: def_survivors_count[u['key']] = def_survivors_count.get(u['key'], 0) + 1

    atk_losses = {}
    for k, start_val in atk_start_counts.items():
        lost = start_val - atk_survivors_count.get(k, 0)
        if lost > 0: atk_losses[k] = lost

    def_losses = {}
    for k, start_val in def_start_counts.items():
        lost = start_val - def_survivors_count.get(k, 0)
        if lost > 0: def_losses[k] = lost

    return winner, log, atk_losses, def_losses

# =============================================================================
# SIEGE WARFARE (TASK 3) — multi-phase assault built on top of simulate_battle.
# =============================================================================
def wall_hp(def_buildings):
    """Defender wall hit points, scaling with their fortification buildings (MG6)."""
    b = def_buildings or {}
    return (config.WALL_BASE
            + config.WALL_PER_WATCHTOWER * b.get("watchtower", 0)
            + config.WALL_PER_CASTLE * b.get("castle", 0))

def siege_cost(engines):
    """Total gold/iron/grain to field a set of engines, e.g. {'trebuchet':2}.
    DECLARED SINK (MG4)."""
    cost = {"gold": 0, "iron": 0, "grain": 0}
    for ek, n in engines.items():
        if n <= 0 or ek not in config.SIEGE_ENGINES:
            continue
        e = config.SIEGE_ENGINES[ek]
        cost["gold"]  += e["gold"] * n
        cost["iron"]  += e["iron"] * n
        cost["grain"] += e["grain"] * n
    return cost

def _bombard(engines, def_buildings):
    """Phase 1. Engines batter the wall over BOMBARD_VOLLEYS while the watchtower
    destroys some of them each volley. Returns (breached, engine_losses, total_dmg,
    wall, log_lines)."""
    wall = wall_hp(def_buildings)
    wt_lvl = (def_buildings or {}).get("watchtower", 0)
    # Mutable remaining-engine counts.
    remaining = {ek: n for ek, n in engines.items()
                 if n > 0 and ek in config.SIEGE_ENGINES}
    losses = {ek: 0 for ek in remaining}
    total_dmg = 0.0
    kills_per_volley = int(wt_lvl * config.WT_ENGINE_KILLS_PER_LVL)
    log = [f"🏰 <b>Walls:</b> {wall} HP (Watchtower Lv{wt_lvl})."]
    for v in range(config.BOMBARD_VOLLEYS):
        if not any(remaining.values()):
            break
        # Watchtower counter-fire FIRST (so a freshly-arrived engine can be shot before
        # it fires on a heavily-defended wall). Spread kills across engine types.
        to_kill = kills_per_volley
        while to_kill > 0 and any(remaining.values()):
            for ek in list(remaining):
                if remaining[ek] > 0:
                    remaining[ek] -= 1
                    losses[ek] += 1
                    to_kill -= 1
                    if to_kill <= 0:
                        break
        # Surviving engines fire on the wall.
        volley_dmg = sum(remaining[ek] * config.SIEGE_ENGINES[ek]["wall_dmg"]
                         for ek in remaining) * random.uniform(0.8, 1.2)
        total_dmg += volley_dmg
    breached = total_dmg >= wall
    lost_total = sum(losses.values())
    log.append(f"💥 Bombardment dealt {int(total_dmg)} wall damage"
               + (f"; lost {lost_total} engine(s) to counter-fire." if lost_total else "."))
    log.append("🧱 <b>BREACH!</b> The walls are down." if breached
               else "🛡️ The walls <b>held</b>.")
    return breached, losses, total_dmg, wall, log

def resolve_siege(atk_army, def_army, engines, atk_tribe, def_tribe,
                  atk_stance="standard", def_stance="standard",
                  def_buildings=None, atk_buildings=None,
                  atk_combat_mult=1.0, def_combat_mult=1.0, def_ward_keep=1.0):
    """Full multi-phase siege. Returns
    (winner, breached, log, atk_losses, def_losses, engine_losses).
    Phase 1 bombardment -> Phase 2 field battle (fortification nullified if breached)
    -> winner. The bot applies sack vs normal loot from `breached`."""
    breached, engine_losses, _dmg, _wall, slog = _bombard(engines, def_buildings)

    # If breached, the attacker is inside the walls: nullify the watchtower fortify
    # bonus for the field battle (but leave other buildings intact).
    field_def_bld = dict(def_buildings or {})
    if breached:
        field_def_bld["watchtower"] = 0

    winner, blog, atk_losses, def_losses = simulate_battle(
        atk_army, def_army, atk_tribe, def_tribe, atk_stance, def_stance,
        def_buildings=field_def_bld, atk_buildings=atk_buildings,
        atk_combat_mult=atk_combat_mult, def_combat_mult=def_combat_mult,
        def_ward_keep=def_ward_keep)

    log = slog + ["", "⚔️ <b>The armies clash...</b>"] + blog
    if winner == "Attacker":
        log.append("🔥 <b>The city is SACKED!</b>" if breached
                   else "🏆 You won the field, but the vault stayed locked behind the walls.")
    else:
        log.append("💀 The assault was repulsed.")
    return winner, breached, log, atk_losses, def_losses, engine_losses

def run_espionage(attacker, target, spies_sent, mission_type, atk_units, def_units, def_buildings):
    """
    Executes an espionage mission with tiered outcomes.
    
    Returns tuple: (success, user_msg, target_alert, spies_died, stolen_gold, building_damaged)
    """
    # 1. Calculate Defense Score
    def_spies = def_units.get("spy", 0)
    watchtower_lvl = def_buildings.get("watchtower", 0)
    
    defense_score = (def_spies * 1.0) + (watchtower_lvl * config.WATCHTOWER_DETECT) + config.BASE_DETECTION
    
    # Attack score has variance (+/- 20%) to add uncertainty
    attack_score = spies_sent * random.uniform(0.8, 1.2)
    
    # Ratio determines success tier
    ratio = attack_score / max(defense_score, 1)
    
    # 2. Initialize Results
    success = False
    spies_died = 0
    user_msg = ""
    target_alert = None
    stolen_gold = 0
    building_damaged = None
    
    # 3. Determine Outcome Tier
    if ratio > 1.5:
        # TIER 1: GHOST (Critical Success - No losses, minimal alert)
        success = True
        spies_died = 0
        target_alert = "⚠️ Your guards heard whispers in the shadows, but found nothing..."
        
    elif ratio > 1.0:
        # TIER 2: DETECTED SUCCESS (Mission succeeds but some spies caught)
        success = True
        spies_died = max(1, int(spies_sent * 0.20))
        target_alert = "⚔️ <b>INTRUDERS SPOTTED!</b>\nYour guards intercepted spies from an unknown lord!"
        
    elif ratio > 0.5:
        # TIER 3: FAILED (Half your spies die, enemy knows you tried)
        success = False
        spies_died = max(1, int(spies_sent * 0.50))
        user_msg = "❌ <b>MISSION FAILED</b>\n\nTheir defenses were too strong. Half your rogues were killed."
        target_alert = f"🛡️ <b>INFILTRATION REPELLED</b>\nYour guards killed enemy spies attempting to breach your walls."
        
    else:
        # TIER 4: DISASTER (Total wipe, identity exposed)
        success = False
        spies_died = spies_sent
        user_msg = "💀 <b>COMPLETE DISASTER</b>\n\nNo survivors. Your identity has been exposed to the enemy."
        target_alert = f"⛓️ <b>SPIES CAPTURED!</b>\nYou interrogated enemy agents. They serve <b>{html.escape(str(attacker['username']))}</b>."
    
    # 4. Execute Mission Rewards (only if successful)
    if success:
        surviving_spies = spies_sent - spies_died
        
        if mission_type == "scout":
            # SCOUT: Reveal enemy intelligence
            unit_info = ", ".join([f"{config.UNITS[k]['name']}: {v}" for k, v in def_units.items() if v > 0])
            building_info = ", ".join([f"{config.BUILDINGS[k]['name']}: Lv{v}" for k, v in def_buildings.items() if v > 0])
            
            user_msg = (f"👁️ <b>INTELLIGENCE ACQUIRED</b>\n\n"
                       f"💰 Treasury: ~{int(target['gold'])} Gold\n"
                       f"⚔️ Forces: {unit_info or 'None detected'}\n"
                       f"🏗️ Buildings: {building_info or 'None detected'}\n"
                       f"🛡️ Stance: {target.get('stance', 'standard').title()}")
            if spies_died > 0:
                user_msg += f"\n\n💀 Rogues Lost: {spies_died}"
                
        elif mission_type == "heist":
            # HEIST: Steal gold based on carrying capacity and vault limits
            
            # 1. Calculate Safe Gold based on Castle Level (Vault)
            castle_lvl = def_buildings.get('castle', 1)
            safe_gold = castle_lvl * config.SAFE_GOLD_PER_LEVEL
            
            # 2. Can only steal what is NOT in the vault
            available_gold = max(0, target['gold'] - safe_gold)
            
            # 3. Calculate Spy Capacity
            capacity = surviving_spies * config.SPY_CARRY_CAP
            
            # 4. Final Steal Amount (Lower of Capacity vs Available)
            stolen_gold = int(min(capacity, available_gold))
            
            if stolen_gold > 0:
                user_msg = f"💰 <b>HEIST SUCCESSFUL!</b>\n\nYour rogues escaped with {stolen_gold} Gold!"
            else:
                user_msg = "💰 <b>HEIST COMPLETE</b>\n\nBut the treasury was locked in the Vault..."
                
            if spies_died > 0:
                user_msg += f"\n💀 Rogues Lost: {spies_died}"
            if target_alert and stolen_gold > 0:
                target_alert += f"\n📉 Treasury Alert: {stolen_gold} Gold is missing!"
                
        elif mission_type == "sabotage":
            # SABOTAGE: Chance to damage a random building
            roll = random.randint(0, 100)
            
            if roll < config.SABOTAGE_CHANCE:
                # Find buildings that can be damaged (level > 0, not castle)
                damageable = [b for b, lvl in def_buildings.items() if lvl > 0 and b != "castle"]
                
                if damageable:
                    building_damaged = random.choice(damageable)
                    b_name = config.BUILDINGS[building_damaged]['name']
                    user_msg = f"🔥 <b>SABOTAGE SUCCESSFUL!</b>\n\nYour agents destroyed their {b_name}!"
                    if target_alert:
                        target_alert += f"\n🔥 Your {b_name} was burned down by saboteurs!"
                else:
                    user_msg = "🔥 <b>INFILTRATION COMPLETE</b>\n\nBut there were no vulnerable buildings to sabotage."
            else:
                user_msg = "💨 <b>SABOTAGE FAILED</b>\n\nYour agents couldn't plant the explosives, but escaped safely."
                
            if spies_died > 0:
                user_msg += f"\n💀 Rogues Lost: {spies_died}"
    
    return success, user_msg, target_alert, spies_died, stolen_gold, building_damaged