# balance_sim.py
# =============================================================================
# MG5 / MG7 AUTHORITATIVE BALANCE HARNESS
# Runs the REAL game_logic.simulate_battle (with its true per-round RNG,
# frontline width, target shuffling and stances) — this is the source of truth
# for MG5's win-rate ceiling / counter checks, NOT the SQL approximation.
#
# Run from the project root (folder containing 'myTelegramBots'):
#     python -m myTelegramBots.IronDominion.balance_sim
#
# Tunables below mirror balance_overhaul/MG5_sampled_non_domination.txt.
# Defaults are sized to run in a reasonable time; raise SIM_COUNT / SAMPLE_SIZE
# for tighter confidence intervals (see the CI note in the printout).
# =============================================================================
import random
import math

from . import config
from . import game_logic

# --- Tunables (see MG5 spec) ---
SIM_COUNT             = 1000     # battles per matchup orientation
WINRATE_CEILING       = 0.55
WINRATE_FLOOR_COUNTER = 0.60
TEST_BUDGETS          = [2000, 10000, 50000]
SAMPLE_SIZE           = 40       # mixed comps for the sampled ceiling (raise as desired)
NEUTRAL_TRIBE         = "merchant"  # gold tribe: no combat modifier

COMBAT_UNITS = [k for k, v in config.UNITS.items() if v["combat_valid"]]


def pure_army(unit, budget):
    n = budget // config.UNITS[unit]["cost"]
    return {unit: int(n)} if n > 0 else {unit: 1}


def random_mixed_army(budget):
    """A gold-equal army with a random split across the combat units."""
    weights = {u: random.random() for u in COMBAT_UNITS}
    total = sum(weights.values()) or 1.0
    army = {}
    for u in COMBAT_UNITS:
        gold = budget * weights[u] / total
        cnt = int(gold // config.UNITS[u]["cost"])
        if cnt > 0:
            army[u] = cnt
    return army or pure_army(random.choice(COMBAT_UNITS), budget)


def ci95(p, n):
    return 1.96 * math.sqrt(max(p * (1 - p), 1e-9) / max(n, 1))


def winrate(a, b, n=SIM_COUNT):
    """Win-rate of army `a` vs army `b`, averaged over BOTH orientations so the
    defender tie-advantage cancels out."""
    wins = games = 0
    for _ in range(n):
        w, _, _, _ = game_logic.simulate_battle(a, b, NEUTRAL_TRIBE, NEUTRAL_TRIBE)
        wins += 1 if w == "Attacker" else 0
        games += 1
    for _ in range(n):
        w, _, _, _ = game_logic.simulate_battle(b, a, NEUTRAL_TRIBE, NEUTRAL_TRIBE)
        wins += 1 if w == "Defender" else 0
        games += 1
    return wins / games


def counter_survivors_ok(winner_army, loser_army, n=200):
    """C3: in a counter matchup the winner should take >0 casualties
    (no costless 100% wipe). Returns True if the winner ever loses a unit."""
    for _ in range(n):
        w, _, atk_losses, def_losses = game_logic.simulate_battle(
            winner_army, loser_army, NEUTRAL_TRIBE, NEUTRAL_TRIBE)
        if w == "Attacker" and sum(atk_losses.values()) > 0:
            return True
    return False


def run_counter_matrix(budget):
    print(f"\n=== Pure-stack counter matrix @ gold {budget} "
          f"(row attacker win% vs column) ===")
    header = "             " + " ".join(f"{u[:8]:>8}" for u in COMBAT_UNITS)
    print(header)
    wr_field = {}
    for atk in COMBAT_UNITS:
        cells, opp_wrs = [], []
        for dfn in COMBAT_UNITS:
            if atk == dfn:
                cells.append(f"{'--':>8}")
                continue
            wr = winrate(pure_army(atk, budget), pure_army(dfn, budget))
            opp_wrs.append(wr)
            cells.append(f"{wr*100:7.1f}%")
        wr_field[atk] = sum(opp_wrs) / len(opp_wrs)
        print(f"{atk:12} " + " ".join(cells))
    return wr_field


def run_sampled_ceiling(budget):
    """C1: build SAMPLE_SIZE mixed comps, round-robin, report the max field
    win-rate vs the ceiling."""
    comps = [random_mixed_army(budget) for _ in range(SAMPLE_SIZE)]
    field_wr = []
    for i, a in enumerate(comps):
        wins = games = 0
        for j, b in enumerate(comps):
            if i == j:
                continue
            wr = winrate(a, b, n=max(50, SIM_COUNT // 5))  # lighter per-pair for speed
            wins += wr
            games += 1
        field_wr.append(wins / max(games, 1))
    mx = max(field_wr)
    print(f"@ {budget}: max sampled-field win-rate = {mx*100:.1f}% "
          f"(ceiling {WINRATE_CEILING*100:.0f}%) "
          f"-> {'PASS' if mx <= WINRATE_CEILING else 'FAIL/REVIEW'}")
    return mx


def main():
    print("IRON DOMINION — MG5 authoritative balance harness")
    print(f"SIM_COUNT={SIM_COUNT}  SAMPLE_SIZE={SAMPLE_SIZE}  units={COMBAT_UNITS}")
    for B in TEST_BUDGETS:
        wr_field = run_counter_matrix(B)
        print("  pure-stack field win-rates:",
              {u: f"{w*100:.0f}%" for u, w in wr_field.items()})

        # C2: every unit has an equal-cost counter winning >= floor
        print("  C2 counters:")
        for dfn in COMBAT_UNITS:
            best = max(
                ((atk, winrate(pure_army(atk, B), pure_army(dfn, B)))
                 for atk in COMBAT_UNITS if atk != dfn),
                key=lambda t: t[1])
            ok = "PASS" if best[1] >= WINRATE_FLOOR_COUNTER else "REVIEW"
            print(f"    {dfn:12} best counter = {best[0]:12} "
                  f"{best[1]*100:.1f}%  [{ok}]")

        run_sampled_ceiling(B)
    print("\nNote: raise SIM_COUNT/SAMPLE_SIZE for tighter CIs. "
          "MG7 reuses winrate()/random_mixed_army() for its correction loop.")


if __name__ == "__main__":
    main()
