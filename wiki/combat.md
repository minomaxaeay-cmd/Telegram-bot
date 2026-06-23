# Combat

Battles are resolved by `game_logic.simulate_battle(...)` when one lord
[attacks](arch_commands.md) another. Combat is a frontline brawl over up to
**25 rounds**, decided by who is wiped out — or, on timeout, by surviving
**gold value** (with a tie on value going to the **Attacker**).

## 1. Deployment & reserves
Each side's army (a dict of `{unit: count}`) becomes a **pool** of individual
unit objects, then `random.shuffle`d into **reserves**. [Spies](ref_units/spy.md)
(`combat_valid = False`) are excluded. The [Highlander](ref_tribes/highlander.md)
tribe multiplies its units' `soft_atk` and `hard_atk` by **1.11** here.

## 2. The frontline
Each round the frontline is refilled from reserves up to `COMBAT_WIDTH` (**40**)
total **width**, with a +2 tolerance for the last unit. Unit widths:
[peasant](ref_units/peasant.md) 1, [man-at-arms](ref_units/man_at_arms.md) 2,
[pikeman](ref_units/pikeman.md) 2, [knight](ref_units/knight.md) 4. So cheap
narrow units put more bodies on the line; knights take 4 slots each.

## 3. Damage formula
Every frontline unit attacks one **random** enemy frontline unit. The base hit is:

```
raw = attacker.hard_atk * target.hard + attacker.soft_atk * (1 - target.hard)
```

The armor check halves the hit when `target.armor > attacker.piercing`. In the
code this `* 0.5` is applied to the **final** damage (after the multipliers
below), but since every factor is multiplicative the result is identical to
halving `raw`.

The raw hit is then scaled by **side-specific** multipliers (they are NOT all
applied to every swing — they depend on which side is hitting):

```
# Attacker -> Defender hit:
actual = raw * (atk_stance.atk * tac_atk) * (def_stance.def) * uniform(0.8,1.2)
             * fort_keep      # watchtower fortification (defender only)
             * atk_forge      # attacker's blacksmith Forge

# Defender -> Attacker hit:
actual = raw * (def_stance.atk * tac_def) * (atk_stance.def) * uniform(0.8,1.2)
             * def_forge      # defender's blacksmith Forge
```

`tac_atk` and `tac_def` are **separate, per-side** tactical multipliers — the code
calls `get_tactical_bonus(atk_stance, def_stance)` for the attacker and
`get_tactical_bonus(def_stance, atk_stance)` for the defender. Because the tactical
triangle is a strict 3-cycle, at most one of them is `1.15` (the other is `1.0`).

- `fort_keep` (the [Watchtower](ref_buildings/watchtower.md) reduction) applies
  **only to hits landing on the defender**.
- `forge` is **each attacking side's own** [Blacksmith](ref_buildings/blacksmith.md)
  multiplier.
- The stance `.atk` (damage dealt) and the opponent's `.def` (damage taken) combine,
  plus the tactical bonus (see step 4).

About `target.hard` (hardness, 0–1): how much of the damage uses the attacker's
`hard_atk` vs `soft_atk`. Knights are "hard" (0.8); peasants are "soft" (0.0). This
is the heart of the [rock-paper-scissors](units.md): high-`hard_atk` units (pikemen)
shred hard targets (knights); high-`soft_atk` units shred soft targets. **Armor vs
piercing** is binary: if the target's `armor` exceeds the attacker's `piercing`, the
hit is halved.

## 4. Stances & tactics
Both sides pick a [stance](ref_stances/standard.md). `STANCE_STATS` gives an `atk`
(damage dealt) and `def` (damage-taken) multiplier. There is also a **tactical
rock-paper-scissors** (`get_tactical_bonus`): **Aggressive > Mobile > Defensive >
Aggressive** grants the winner **+15%** damage. The attacker picks their stance
each attack; the defender's stance is fixed from their profile.

## 5. Building effects (MG6)
- **[Watchtower](ref_buildings/watchtower.md) fortification:** the *defender*
  takes less damage — `min(2% * watchtower_level, 30%)` reduction (`fort_keep`).
- **[Blacksmith](ref_buildings/blacksmith.md) Forge:** each side's outgoing damage
  is multiplied by `1 + min(2% * blacksmith_level, 25%)` — symmetric, so it never
  encourages turtling.

## 5b. Blessings (temporary)
[Blessings](blessings.md) bought with [Faith](currencies.md) feed extra multipliers into
the same formula (default `1.0` when none active): **Zeal** ×1.10 on the buyer's outgoing
damage (`atk_combat_mult` / `def_combat_mult`); **Ward** ×0.90 on damage landing on a
defending blessing-holder (`def_ward_keep`).

## 5c. Siege (Raid vs Siege)
An attacker may instead mount a **[Siege](siege.md)** — a multi-phase assault that first
bombards the defender's **walls** with engines (funded by Iron+Grain). A **breach**
nullifies the Watchtower fortification for the field battle and unlocks a bigger
**sack** loot. See **[Siege Warfare](siege.md)** for the full mechanic.

## 6. Resolution
- If the attacker's army is wiped (even on mutual annihilation) → **Defender wins**.
- If the defender's army is wiped → **Attacker wins**.
- If both survive to round 25 → the side with greater **surviving gold value** wins;
  on an exact value **tie the Attacker wins** (`val_a >= val_b`).

Casualties are returned as per-unit loss dicts and applied to the database, then
the winner [loots](economy.md) gold (attacker only) and the **victor of either
side** records the result: +1 win, **+10 [season](seasons.md) score**, and
[Renown](renown.md) — so a successful **defender** is rewarded exactly like a winning
attacker (only the gold loot is attacker-exclusive).

The **defender** also receives a live alert message about the attack, with inline
**📜 View Profile** / **⚔️ Retaliate** buttons for a quick profile lookup or
counter-attack. (A [heist](espionage.md) victim gets a similar alert, there labelled
**👤 Who?** / **⚔️ Retaliate**.)

## See also
[Units](units.md) · [Siege](siege.md) · [Buildings](buildings.md) · [Economy](economy.md) · [Blessings](blessings.md) · [Stances](ref_stances/standard.md) · [Renown](renown.md) · [Espionage](espionage.md)

---
Source: `game_logic.py` (`simulate_battle`, `get_tactical_bonus`, `resolve_siege`), `config.py` (COMBAT_WIDTH, MAX_ROUNDS, STANCE_STATS, WATCHTOWER_DEF_*, BLACKSMITH_DMG_*, BLESSING_DEFS, SIEGE_ENGINES, WALL_*).
