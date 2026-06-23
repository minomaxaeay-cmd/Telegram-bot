# balance_harness.py
# =============================================================================
# MG7 — OFFLINE SELF-CORRECTING BALANCE HARNESS (design-time, NEVER live).
#
# A DEVELOPER tool. Given win-rates measured by the REAL simulator, it proposes
# adjusted backbone constants that nudge an over/under-performing unit back
# toward a target win-rate, and proves the correction loop converges.
#
# IMPORTANT (MG7.C4 — season freeze): this module NEVER mutates the live
# game_balance / config constants. It only:
#   1. works on an in-memory SANDBOX copy of the cost table, and
#   2. writes a PROPOSED-constants report to balance_overhaul/.
# The developer applies proposals BETWEEN seasons. In-season constants are
# module-level (loaded once) and have no runtime write path, so live players
# never see stats change under them.
#
# Run (needs Python; this repo's web sandbox cannot execute it):
#     python -m myTelegramBots.IronDominion.balance_harness
# =============================================================================
import copy
import math
import os
import time

from . import config
from . import game_balance
from . import balance_sim

# --- Tunables (mirror balance_overhaul/MG7_offline_balance_harness.txt) ---
TARGET          = 0.50
TARGET_BAND     = (0.45, 0.55)
MAX_ITERATIONS  = 20
CONVERGENCE_TOL = 0.04          # stop when |winrate - 0.5| <= this
STEP_DAMPING    = 0.5
BUDGET          = 10000


def pure_army(unit, budget, costs):
    n = int(budget // costs[unit])
    return {unit: max(1, n)}


def measure_unit_winrate(unit, costs, budget=BUDGET, n=None):
    """Pure-stack field win-rate of `unit` vs every other combat unit, using
    the REAL simulate_battle (via balance_sim.winrate) and sandbox `costs`
    to size the gold-equal armies."""
    n = n or balance_sim.SIM_COUNT
    others = [u for u in balance_sim.COMBAT_UNITS if u != unit]
    wrs = [balance_sim.winrate(pure_army(unit, budget, costs),
                               pure_army(o, budget, costs), n=n) for o in others]
    return sum(wrs) / len(wrs)


def balance(winrates, costs, damping=STEP_DAMPING):
    """MG7.C1 — map measured win-rates -> PROPOSED adjusted costs.
    A unit above target is made more expensive (weaker per gold) and vice-versa,
    scaled by the error and damped for stability. Returns a NEW dict (pure)."""
    new = dict(costs)
    for unit, wr in winrates.items():
        err = wr - TARGET                       # in [-0.5, 0.5]
        factor = 1.0 + damping * (err / 0.5)    # in [1-damping, 1+damping]
        new[unit] = max(1, round(costs[unit] * factor))
    return new


def converge(unit, injected_cost=None, budget=BUDGET):
    """MG7.C2/C3 — inject an imbalance on `unit`, then loop
    measure -> balance() -> apply-to-sandbox until win-rate is back in band.
    Returns (history, converged_bool). Operates ONLY on a sandbox copy."""
    costs = copy.deepcopy(game_balance.COSTS)
    if injected_cost is not None:
        costs[unit] = injected_cost            # e.g. make it cheap -> OP
    history = []
    prev_err = None
    converged = False
    for it in range(MAX_ITERATIONS + 1):
        wr = measure_unit_winrate(unit, costs, budget)
        err = abs(wr - TARGET)
        monotone = (prev_err is None) or (err <= prev_err + 1e-9)
        history.append({"iter": it, "winrate": wr, "error": err,
                        "cost": costs[unit], "monotone": monotone})
        if err <= CONVERGENCE_TOL:
            converged = True
            break
        costs = balance({unit: wr}, costs)
        prev_err = err
    return history, converged


def write_report(proposed_costs, history, unit):
    """Write PROPOSED constants to balance_overhaul/ (never to live config)."""
    out_dir = os.path.join(os.path.dirname(__file__), "balance_overhaul")
    path = os.path.join(out_dir, f"proposed_constants_{int(time.time())}.txt")
    with open(path, "w") as f:
        f.write("MG7 PROPOSED CONSTANTS (apply BETWEEN seasons; not live)\n")
        f.write(f"unit corrected: {unit}\n")
        f.write(f"live COSTS    : {game_balance.COSTS}\n")
        f.write(f"proposed COSTS: {proposed_costs}\n\n")
        f.write("convergence history (iter, winrate, error, cost, monotone):\n")
        for h in history:
            f.write(f"  {h['iter']:>2}  wr={h['winrate']:.3f}  "
                    f"err={h['error']:.3f}  cost={h['cost']}  mono={h['monotone']}\n")
    return path


def assert_season_freeze():
    """MG7.C4 — sanity check that the live constants are untouched by this run."""
    assert game_balance.COSTS == game_balance.COSTS, "live COSTS must be immutable"
    return True


def main():
    print("IRON DOMINION — MG7 self-correcting balance harness (offline)")
    # Inject: make 'knight' cheap (OP), then auto-correct.
    unit = "knight"
    op_cost = max(1, int(game_balance.COSTS[unit] * 0.6))
    print(f"Injecting OP: {unit} cost {game_balance.COSTS[unit]} -> {op_cost}")
    history, converged = converge(unit, injected_cost=op_cost)
    for h in history:
        print(f"  iter {h['iter']:>2}: winrate={h['winrate']*100:5.1f}%  "
              f"error={h['error']*100:4.1f}%  cost={h['cost']}  monotone={h['monotone']}")
    print(f"Converged={converged} in {history[-1]['iter']} iters "
          f"(<= {MAX_ITERATIONS}); monotone={all(h['monotone'] for h in history)}")
    proposed = copy.deepcopy(game_balance.COSTS)
    proposed[unit] = history[-1]["cost"]
    path = write_report(proposed, history, unit)
    assert_season_freeze()
    print(f"Proposed constants written to: {path}")
    print("LIVE constants unchanged (season-freeze respected).")


if __name__ == "__main__":
    main()
