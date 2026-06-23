# Siege Warfare

Siege is the centerpiece offensive mechanic. When you attack a lord you choose
**Raid** or **Siege**:

- ⚔️ **Raid** — the instant field [battle](combat.md) (unchanged). The defender's
  [Watchtower](ref_buildings/watchtower.md) fortifies them.
- 🏰 **Siege** — a multi-phase assault that can smash the **walls**, nullify the
  fortification, and **sack** the city for extra loot. The only way to truly crack a
  fortified lord.

Resolved by `game_logic.resolve_siege(...)`, which wraps `simulate_battle`.

## Walls
Every fief has walls whose hit points scale with the defender's fortification buildings
(MG6 coherence):
```
wall_hp = WALL_BASE + WALL_PER_WATCHTOWER * watchtower_lvl + WALL_PER_CASTLE * castle_lvl
        = 100 + 60*watchtower + 25*castle
```
A fresh lord (watchtower 0, castle 1) has **125** wall HP; a fortified one (watchtower 5,
castle 3) has **475**.

## Siege engines (consumable)
You fund engines **per assault** from Gold + [Iron](currencies.md) + [Grain](currencies.md)
in the **Siege Workshop**. They are spent in the assault (a declared [MG4](economy.md)
sink) — not banked — and have **zero field-combat value**.

| Engine | Gold | Iron | Grain | Wall damage / volley |
|---|---|---|---|---|
| Battering Ram 🪵 | 120 | 20 | 10 | 25 |
| Trebuchet 🎯 | 300 | 40 | 20 | 60 |

(`config.SIEGE_ENGINES`.)

## The three phases
1. **Bombardment** — over `BOMBARD_VOLLEYS` (**3**) volleys your engines batter the
   wall, while the defender's Watchtower returns fire, destroying
   `floor(WT_ENGINE_KILLS_PER_LVL · watchtower_lvl)` = `floor(0.20·lvl)` engines per
   volley. Total damage ≥ wall HP ⇒ **breach**. So a fortified target needs **more**
   engines (siege cost scales with the defender's fortification).
2. **Field battle** — the normal `simulate_battle`. If the walls were **breached**, the
   defender's Watchtower fortification is **nullified** (you're inside). Because engines
   don't fight, you still need a real army to win here.
3. **Sack / repulse** — win **+ breach** ⇒ loot `SIEGE_SACK_LOOT_PCT` (**50%**) of
   exposed gold with the vault **halved** (`SIEGE_SACK_VAULT_MULT` 0.5), plus
   `SIEGE_BREACH_RENOWN_MULT` (**×1.5**) [renown](renown.md). Win but walls **held** ⇒
   normal loot. Lose ⇒ your troops and engines are gone.

## Why a siege needs everything
Engines (Iron+Grain economy) break the walls; a field [army](units.md) wins the battle;
the defender's [buildings](buildings.md) set the wall HP and counter-fire. An all-engine
attacker brings no army and **cannot** win the field — so siege never becomes a dominant
single-axis strategy (the unit [rock-paper-scissors](units.md) is untouched).

## See also
[Combat](combat.md) · [Currencies](currencies.md) · [Watchtower](ref_buildings/watchtower.md) · [Economy](economy.md) · [Renown](renown.md) · [Constants](ref_constants.md)

---
Source: `config.py` (SIEGE_ENGINES, WALL_*, BOMBARD_VOLLEYS, WT_ENGINE_KILLS_PER_LVL, SIEGE_SACK_*), `game_logic.py` (`resolve_siege`, `wall_hp`, `siege_cost`), `bot.py` (mode choice, Siege Workshop, atk_final siege branch).
