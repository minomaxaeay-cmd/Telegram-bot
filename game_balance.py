# game_balance.py
# =============================================================================
# MG1 — PARAMETRIC BACKBONE (single source of truth for unit combat stats).
#
# Every combat stat is DERIVED from a unit's gold cost and a role vector:
#       stat = round(role_fraction * cost / stat_price)
# This keeps cost <-> stats coherent: tuning one price/constant reshapes the
# whole roster predictably. A small, documented set of EXCEPTIONS overrides the
# backbone where intentional rock-paper-scissors asymmetry is required.
#
# See balance_overhaul/MG1_parametric_backbone.txt.
# NOTE: `org` was removed from all units — it was never read by simulate_battle.
# =============================================================================

# Backbone constant: gold per 1 point of each stat.
STAT_PRICE = {
    "hp":       2.2,
    "soft_atk": 3.0,
    "hard_atk": 4.0,
    "armor":    6.0,
    "piercing": 4.0,
}

# Gold cost anchors each unit's total stat budget.
COSTS = {
    "peasant":      20,
    "man_at_arms": 130,
    "pikeman":     250,
    "knight":      500,
}

# Role vector: fraction of cost allocated to each lane (each unit sums to ~1.0).
ROLE_VECTOR = {
    "peasant":     {"hp": 0.75, "soft_atk": 0.25, "hard_atk": 0.00, "armor": 0.00, "piercing": 0.00},
    "man_at_arms": {"hp": 0.46, "soft_atk": 0.35, "hard_atk": 0.06, "armor": 0.10, "piercing": 0.03},
    "pikeman":     {"hp": 0.44, "soft_atk": 0.04, "hard_atk": 0.40, "armor": 0.02, "piercing": 0.10},
    "knight":      {"hp": 0.44, "soft_atk": 0.18, "hard_atk": 0.12, "armor": 0.20, "piercing": 0.06},
}

# Category attributes: define the unit's ROLE, not its budget, so they are NOT
# cost-derived. width = frontline footprint; hard = targetness (fraction of
# incoming damage computed from the attacker's hard_atk vs soft_atk).
CATEGORY = {
    "peasant":     {"width": 1, "hard": 0.0},
    "man_at_arms": {"width": 2, "hard": 0.2},
    "pikeman":     {"width": 2, "hard": 0.0},
    "knight":      {"width": 4, "hard": 0.8},
}

# Documented exceptions (MG1.C2): stats intentionally OFF the backbone.
# Format: (unit, stat) -> (value, reason)
EXCEPTIONS = {
    # peasant.hp 15 (backbone would give 7). REQUIRED for peasant's anti-pikeman
    # counter role: the REAL stochastic sim (Snowflake Python harness) shows at
    # hp 7 peasant beats NOTHING (3% field, loses to pikeman 10/89), while at
    # hp 15 peasant cleanly counters pikeman (100%) and the mixed-comp ceiling is
    # actually LOWEST (74%). An earlier deterministic SQL model wrongly flagged a
    # "peasant screen" at hp 15 -> that was a model artifact; the real sim
    # disproved it. So hp 15 is the correct, healthiest value.
    ("peasant", "hp"):        (15, "Anti-pikeman chaff counter; real-sim verified (hp 7 makes peasant a dead unit)."),
    ("pikeman", "hard_atk"):  (40, "Anti-knight counter spike — the core of the rock-paper-scissors triangle."),
    ("pikeman", "piercing"):  (15, "High piercing bypasses heavy armor (anti-armor specialist)."),
    ("knight",  "armor"):     (12, "Heavy-unit armor kept modest so pikemen reliably counter knights."),
    ("knight",  "piercing"):  (5,  "Knight piercing capped so it does not erase the pikeman counter."),
}

STAT_KEYS = ("hp", "soft_atk", "hard_atk", "armor", "piercing")


def generate_stat(unit, stat):
    """Return the backbone-derived stat, or its documented exception override."""
    if (unit, stat) in EXCEPTIONS:
        return EXCEPTIONS[(unit, stat)][0]
    frac = ROLE_VECTOR[unit][stat]
    return round(frac * COSTS[unit] / STAT_PRICE[stat])


def build_unit(unit, display_name, combat_valid=True):
    """Assemble a full unit stat dict from the backbone + category attributes."""
    u = {"name": display_name, "cost": COSTS[unit], "width": CATEGORY[unit]["width"]}
    for s in STAT_KEYS:
        u[s] = generate_stat(unit, s)
    u["hard"] = CATEGORY[unit]["hard"]
    u["combat_valid"] = combat_valid
    return u


# =============================================================================
# MG1 EXTENSION — MULTI-CURRENCY COST BACKBONE (Iron recruitment cost).
# Iron is a second recruitment currency (see config.IRON_COST_PER_UNIT). To stay
# coherent with the gold backbone, an armoured unit's iron cost is derived as a
# fixed fraction of its gold cost, with a documented exception: the peasant levy
# uses NO iron (it is unarmoured chaff), so it is excluded from the formula.
# config.IRON_COST_PER_UNIT holds the authoritative (rounded, hand-tunable) values;
# `iron_cost()` is the formula they track within tolerance, and `iron_cost_table()`
# lets a test assert coverage (MG1-style).
# =============================================================================
IRON_COST_FRACTION = 0.12   # armoured units spend ~12% of their gold cost in iron

def iron_cost(unit):
    """Backbone-derived iron recruitment cost. Peasant (levy) is the documented
    no-iron exception; spy is priced separately (espionage tool, not armour)."""
    if unit == "peasant":
        return 0
    if unit == "spy":
        return 5
    return round(COSTS[unit] * IRON_COST_FRACTION)

def iron_cost_table():
    """All combat-unit iron costs derived from the backbone (for tests/coverage)."""
    return {u: iron_cost(u) for u in list(COSTS.keys()) + ["spy"]}

