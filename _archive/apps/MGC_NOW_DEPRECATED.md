# MGC_NOW.py - DEPRECATED (2026-01-16)

## Why This App Was Archived

**DANGEROUS: Hardcoded OUTDATED values that do not match database reality.**

This app was retired because it contains hardcoded win rates and parameters that are **massively inflated** compared to the actual validated_setups database values.

---

## The Problem

### Hardcoded Values in MGC_NOW.py (WRONG):

| ORB Time | App Said | Database Reality | Error |
|----------|----------|------------------|-------|
| **1100** | 86.8% WR | 30.4% WR | ❌ **3x too high!** |
| **0900** | 77.4% WR | 17.1% WR | ❌ **4.5x too high!** |
| **1000** | 77.4% WR | 15.3% WR | ❌ **5x too high!** |
| **2300** | 72.8% WR | 56.1% WR | ❌ Wrong |
| **1800** | 70.5% WR | 51.0% WR | ❌ Wrong |
| **0030** | 69.5% WR | 31.3% WR | ❌ **2x too high!** |

### Additional Issues:
- ❌ Wrong SL modes (said HALF for all, but 0900/1000/1100/1800 should be FULL)
- ❌ Wrong RR targets (calculated 1R, but should be 1.5R-8.0R depending on setup)
- ❌ Wrong filter thresholds
- ❌ Wrong expectancy values

---

## Risk of Using This App

1. **Expectation Mismatch:**
   - You'd expect 70-86% win rates
   - Reality: 15-56% win rates
   - Could cause emotional devastation after a string of losses

2. **Wrong Position Sizing:**
   - App calculated risk based on wrong parameters
   - Could lead to over-leveraging

3. **Wrong Setup Selection:**
   - App showed wrong tier rankings
   - Would prioritize wrong setups

4. **Outdated Strategy:**
   - Values were from BEFORE the scan window bug fix (Jan 2026)
   - Based on truncated scan windows that missed huge moves
   - Not representative of corrected strategy performance

---

## What To Use Instead

### ✅ Use These Apps (Correct Values):

**1. `trading_app/app_trading_hub.py` - FULL FEATURED**
```bash
streamlit run trading_app/app_trading_hub.py
```
- 5-tab interface (LIVE, LEVELS, TRADE PLAN, JOURNAL, AI CHAT)
- Loads values dynamically from database via config_generator.py
- Always up-to-date with validated_setups table
- 1,200 lines, professional grade

**2. `trading_app/app_simplified.py` - LEAN DASHBOARD**
```bash
streamlit run trading_app/app_simplified.py
```
- Single-page focused interface
- Same accurate values as trading_hub
- Simpler, faster, easier to use during live trading
- 400 lines

Both apps use the **auto-generated config system** (config_generator.py) which reads directly from the validated_setups database. They can NEVER get out of sync.

---

## Correct MGC Setup Values (as of 2026-01-16)

### From validated_setups Database:

| ORB | RR | SL Mode | Win Rate | Avg R | Tier | Annual R |
|-----|----|---------|---------:|------:|------|----------|
| **2300** | 1.5 | HALF | 56.1% | +0.403R | S+ | ~+105R/year |
| **1000** | 8.0 | FULL | 15.3% | +0.378R | S+ | ~+98R/year |
| **1800** | 1.5 | FULL | 51.0% | +0.274R | S | ~+72R/year |
| **0030** | 3.0 | HALF | 31.3% | +0.254R | S | ~+66R/year |
| **1100** | 3.0 | FULL | 30.4% | +0.215R | A | ~+56R/year |
| **0900** | 6.0 | FULL | 17.1% | +0.198R | A | ~+51R/year |

**Total System: ~+450-600R/year (after filters)**

Key points:
- ✅ Win rates are 15-56%, NOT 70-86%
- ✅ RR targets are 1.5-8.0R (asymmetric edge), NOT 1.0R
- ✅ Extended scan windows (until 09:00 next day)
- ✅ Based on 740 days of data (2024-01-02 to 2026-01-10)

---

## History: Where MGC_NOW.py Values Came From

**Best guess:** These values were from an earlier backtest iteration that had:
1. Short scan windows (stopped at 85 minutes instead of ~24 hours)
2. Different filter settings
3. Possibly forward-looking bias
4. Or manual calculation errors

The corrected values (Jan 2026) come from:
- Extended scan windows (all ORBs scan until 09:00 next day)
- Fixed execution engine (conservative same-bar TP/SL resolution)
- Zero-lookahead methodology
- Rigorous backtest validation

---

## Timeline

- **???** - MGC_NOW.py created with hardcoded values (source unknown)
- **2026-01-15** - Scan window bug discovered and fixed
- **2026-01-16** - validated_setups updated with CORRECTED values
- **2026-01-16** - Config system migrated to auto-generate from database
- **2026-01-16** - MGC_NOW.py archived (this file created)

---

## Could MGC_NOW.py Be Fixed?

Yes, but **not worth the effort** because:
1. You already have 2 better apps (trading_hub, app_simplified)
2. Would require complete rewrite to use config_generator.py
3. Time-based display logic would still need updating
4. Those apps have much more functionality anyway

**Recommendation:** Use trading_hub or app_simplified instead. They're better in every way.

---

## Lesson Learned

**Hardcoded values are dangerous.**

This is exactly why we implemented the auto-config system (config_generator.py):
- Single source of truth (validated_setups database)
- No manual sync required
- Apps always load current values
- Can't get out of date

MGC_NOW.py is a cautionary tale of what happens when values are hardcoded instead of loaded dynamically.

---

*Archived: 2026-01-16*
*Reason: Hardcoded outdated values - dangerously inflated win rates*
*Replacement: Use trading_app/app_trading_hub.py or app_simplified.py*
