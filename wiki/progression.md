# Progression

Iron Dominion is designed as a **long game** with an honest, very long horizon —
the result of a structured balance overhaul (documented under `balance_overhaul/`).

## The core curve
- [Gold mine](ref_buildings/gold_mine.md) income is **linear** (`level × 5/min`).
- [Building](buildings.md) cost is **exponential** (`base × 1.6^level`).
- Combined with the **level cap of 33**, the *fastest possible* path to a maxed
  gold mine (all income reinvested, daily login) is estimated at **~11.45 years**
  (a design figure from a `config.py` comment, not a runtime-enforced value) — so the
  parts that matter (gold, and therefore [army](units.md)) cannot be maxed in
  under 10 years, by design.

## Fast hook, bounded summit
- **Hook:** a new lord can field a viable army within ~a day (early mine levels
  are cheap), so the game grabs you quickly.
- **Summit:** the top tier is gated behind years, but always *reachable* and never
  forces idle waiting — there's always an affordable action.

## What rewards continued play
Because the mine plateaus, the long-term rewards come from:
1. The **24h offline [income](economy.md) cap** — daily players massively outpace
   infrequent ones.
2. **[Combat](combat.md) & [raiding](espionage.md)** — loot and army growth.
3. **[Renown](renown.md)** — a lifetime prestige score that always climbs.

## Buildings ↔ army are inseparable
You can't field a real army without economy ([mine](ref_buildings/gold_mine.md)
funds upkeep) and military buildings ([barracks](ref_buildings/barracks.md)/
[blacksmith](ref_buildings/blacksmith.md) unlock units). Pure "all economy" or
"all military" strategies both lose to a balanced build. See [units](units.md).

## See also
[Economy](economy.md) · [Buildings](buildings.md) · [Units](units.md) · [Renown](renown.md) · [Combat](combat.md)

---
Source: `config.py` (MAX_BUILDING_LEVEL, cost/income constants), `balance_overhaul/` specs (MG0/MG2/MG3/MG6).
