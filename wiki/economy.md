# Economy

The economy is a **closed, conservative system**: each currency is only created by its
production [building](buildings.md) and only destroyed through declared sinks.
Player-vs-player transfers ([loot](#looting) and [heists](espionage.md)) move gold but
never create it.

> Iron Dominion uses **four currencies** — Gold, [Iron, Grain, Faith](currencies.md).
> This page covers Gold and the shared upkeep/desertion rules; see
> **[Currencies](currencies.md)** for the full Iron/Grain/Faith breakdown.

## Starting stockpile
Every new lord begins with **1000 gold** (`users.gold REAL DEFAULT 1000.0`), plus
**100 Iron**, **200 Grain**, **0 Faith** (`config.STARTING_*`). The gold grant is the
only "out-of-loop" gold source besides the admin gift tool.

## Income (the gold mine)
Income accrues passively from your [Gold Mine](ref_buildings/gold_mine.md):

```
income_per_minute = gold_mine_level * 5
```

- Income is computed when you act, based on elapsed time since `last_update`
  (only if more than ~10 seconds have passed), and is **capped at 24 hours** of
  accrual (`elapsed_seconds` capped at 86400). So a daily login captures a full
  day; logging in less often **forfeits** the excess. The same capped window drives
  the **upkeep** charge below, so upkeep is likewise only ever billed for up to 24h
  per tick.
- The [Merchant](ref_tribes/merchant.md) tribe multiplies income by **1.08** (+8%).
- [Renown](renown.md) grants a tiny capped income bonus (max **+2.5%**).

Income is **linear** in mine level, while upgrade cost is **exponential** — this
shapes the whole [progression](progression.md) curve.

## Upkeep & desertion
Each [unit](units.md) costs **gold per minute** (see [constants](ref_constants.md)):
peasant 0.1, man-at-arms 0.5, pikeman 1.0, knight 2.0, spy 0.5 — **and** [Grain](currencies.md)
per minute (food): peasant 0.2, man-at-arms 0.4, pikeman 0.5, knight 1.0, spy 0.3.

```
new_gold  = gold  + gold_income  - gold_upkeep
new_grain = grain + grain_income - grain_upkeep
```

If a tick leaves your **gold OR grain** negative, that balance is floored at 0 and unfed/
unpaid troops **desert**. Desertion is a **single bounded event** per tick: up to
`DESERTION_CAP` (**10%**) of each unit type, scaled by the **worse** of the two shortfalls
(so the gold and grain rails never double-punish). This is why a large army **requires**
both a strong [Gold Mine](ref_buildings/gold_mine.md) *and* enough [Farms](ref_buildings/farm.md)
— see [progression](progression.md), [units](units.md) and [currencies](currencies.md).

## Looting
When you win an attack (see [combat](combat.md)), you steal gold from the loser:

```
exposed = max(0, defender_gold - safe_gold)        # safe_gold = castle_level * 1000
loot    = floor(exposed * 0.30)                    # LOOT_PERCENTAGE
```

The [Castle](ref_buildings/castle.md) "vault" protects `SAFE_GOLD_PER_LEVEL`
(**1000**) gold per castle level from looting and [heists](espionage.md).

## Sources & sinks (ledger)
Per-currency closed ledger (see [Currencies](currencies.md) and [MG4](../balance_overhaul/MG4_closed_economy.txt)):

| Currency | Sources | Sinks | Transfers (zero-sum) |
|---|---|---|---|
| Gold 💰 | gold-mine income (out-of-loop: starting 1000, admin gift) | [building](buildings.md) costs, [recruitment](units.md), gold upkeep, treasury-floored gold, [alliance](alliances.md) fee (2000) | [loot](#looting), [heist](espionage.md) |
| Iron ⛓️ | [Iron Mine](ref_buildings/iron_mine.md) | military recruitment | — |
| Grain 🌾 | [Farm](ref_buildings/farm.md) | food upkeep, grain floored on starvation | — |
| Faith ✝️ | [Chapel](ref_buildings/chapel.md) | [Blessings](blessings.md) | — |

(**Desertion** destroys *units*, not currency — a unit sink. Iron/Grain/Faith have no
PvP transfer, so they are trivially zero-sum.)

## See also
[Currencies](currencies.md) · [Buildings](buildings.md) · [Units](units.md) · [Combat](combat.md) · [Blessings](blessings.md) · [Renown](renown.md) · [Progression](progression.md) · [Constants](ref_constants.md)

---
Source: `database.py` (income tick, desertion, spend_resources, buy_blessing), `bot.py` (loot, recruit), `config.py` (UPKEEP_PER_UNIT, GRAIN_UPKEEP_PER_UNIT, CURRENCIES, STARTING_*, production rates, LOOT_PERCENTAGE, SAFE_GOLD_PER_LEVEL, DESERTION_CAP, TRIBES, RENOWN_*).
