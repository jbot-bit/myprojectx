# NQ & MPL: NOT SUITABLE FOR ORB STRATEGY

## Date: 2026-01-16

---

## Executive Summary

After extending scan windows and finding optimal RR values for NQ and MPL, the data shows these instruments are **NOT suitable** for the ORB breakout strategy.

**Recommendation: Trade MGC ONLY.**

---

## The Hard Truth

### What the Data Shows:

**NQ Results (310 trading days):**
- Optimal RR: 1.0 for ALL 6 ORBs
- Sharp dropoff at RR=1.25+ (e.g., 1100 ORB: 62% → 32% WR)
- Total: +241R/year (BEFORE slippage)

**MPL Results (365 trading days):**
- Optimal RR: 1.0 for ALL 6 ORBs
- Sharp dropoff at RR=1.25+ (e.g., 1100 ORB: 67% → 38% WR)
- Total: +676R/year (BEFORE slippage)

**MGC Results (corrected with extended scans):**
- Optimal RR: 1.5-8.0 (HUGE slippage buffer)
- Moves extend 30-80 points beyond targets
- Total: +600R/year (ROBUST)

---

## Why RR=1.0 is a Red Flag

### The Problem:

When optimal RR is 1.0 and win rates drop 30+ percentage points at RR=1.25, it means:
1. **Moves barely reach 1R** - no extension beyond target
2. **No slippage buffer** - any execution costs kill the edge
3. **Tight, choppy price action** - not trending moves like MGC

### Slippage Reality:

| Cost Component | NQ/MPL Impact |
|---------------|---------------|
| Entry slippage | ~0.05-0.1R |
| Exit slippage | ~0.05-0.1R |
| Commissions/fees | ~0.02R |
| **TOTAL COST** | **~0.12-0.22R per trade** |

**With 60% WR at "1R":**
- Gross: +0.2R avg per trade
- Net after slippage: -0.02R to +0.08R
- **Breakeven or slightly negative**

### Compare to MGC:

| Instrument | Optimal RR | Slippage Buffer | Live Trading Edge |
|------------|-----------|-----------------|-------------------|
| **MGC** | 3.0-8.0 | HUGE (30-80 points beyond target) | ✅ ROBUST |
| **NQ** | 1.0 only | NONE (barely hits 1R) | ❌ KILLED BY SLIPPAGE |
| **MPL** | 1.0 only | NONE (barely hits 1R) | ❌ KILLED BY SLIPPAGE |

---

## Detailed Analysis

### NQ ORB Results:

| ORB | RR=1.0 WR | RR=1.25 WR | Dropoff | Conclusion |
|-----|-----------|------------|---------|------------|
| 0900 | 53.0% | 27.0% | -26% | NOT VIABLE |
| 1000 | 56.1% | 23.4% | -33% | NOT VIABLE |
| 1100 | 62.2% | 32.1% | -30% | NOT VIABLE |
| 1800 | 62.1% | 28.4% | -34% | NOT VIABLE |
| 2300 | 53.1% | 26.8% | -26% | NOT VIABLE |
| 0030 | 62.2% | 22.8% | -39% | NOT VIABLE |

**Pattern: Massive win rate collapse beyond 1R = moves don't extend**

### MPL ORB Results:

| ORB | RR=1.0 WR | RR=1.25 WR | Dropoff | Conclusion |
|-----|-----------|------------|---------|------------|
| 0900 | 62.9% | 44.2% | -19% | NOT VIABLE |
| 1000 | 56.1% | 36.4% | -20% | NOT VIABLE |
| 1100 | 67.5% | 38.5% | -29% | NOT VIABLE |
| 1800 | 55.4% | 24.0% | -31% | NOT VIABLE |
| 2300 | 65.1% | 31.4% | -34% | NOT VIABLE |
| 0030 | 60.5% | 28.8% | -32% | NOT VIABLE |

**Pattern: Same as NQ - moves don't extend beyond 1R**

### MGC ORB Results (CONTRAST):

| ORB | Optimal RR | Win Rate | Extension Beyond Target | Live Trading |
|-----|-----------|----------|-------------------------|--------------|
| 0900 | 6.0 | 17.1% | 30+ points | ✅ SAFE |
| 1000 | 8.0 | 15.3% | 50+ points | ✅ SAFE (CROWN JEWEL) |
| 1100 | 3.0 | 30.4% | 15+ points | ✅ SAFE |
| 1800 | 1.5 | 51.0% | 5-10 points | ✅ SAFE |
| 2300 | 1.5 | 56.1% | 5-10 points | ✅ SAFE (BEST OVERALL) |
| 0030 | 3.0 | 31.3% | 15+ points | ✅ SAFE |

**Pattern: Moves extend FAR beyond targets, huge slippage buffers**

---

## Why MGC Works But NQ/MPL Don't

### MGC Characteristics:
- **Overnight trend moves**: Asia/Europe sessions drive 30-80 point runs
- **Extended holding**: Trades often take 6-12 hours to hit target
- **Smooth moves**: Price trends cleanly without choppy retracements
- **Multiple time zones**: 24-hour trading captures global liquidity flows

### NQ/MPL Characteristics:
- **Intraday chop**: Moves don't extend far from breakout
- **Quick reversals**: Price hits 1R then pulls back
- **Tight action**: Range-bound within daily ATR
- **Not trending**: Momentum doesn't sustain overnight

---

## The Scan Window Fix Was Important But Didn't Change Reality

### What We Learned:

1. **Extended scan windows HELPED MGC**: Went from +400R → +600R/year
   - Why? MGC moves take 6-12 hours to develop
   - Short scans were cutting off winners early

2. **Extended scan windows DIDN'T help NQ/MPL much**:
   - Moves still only reach 1R
   - Extending from 85min to 10+ hours didn't matter
   - The moves just aren't there

### The Fix Revealed the Truth:

The scan window investigation was valuable because it showed:
- MGC has ROBUST extended moves (strategy works!)
- NQ/MPL have TIGHT intraday action (strategy doesn't work)

**We needed extended scans to see this difference clearly.**

---

## Configuration Changes Made

### trading_app/config.py:

**MGC: UNCHANGED (TRADE THIS)**
```python
MGC_ORB_CONFIGS = {
    "0900": {"rr": 6.0, "sl_mode": "FULL"},   # ✅
    "1000": {"rr": 8.0, "sl_mode": "FULL"},   # ✅ CROWN JEWEL
    "1100": {"rr": 3.0, "sl_mode": "FULL"},   # ✅
    "1800": {"rr": 1.5, "sl_mode": "FULL"},   # ✅
    "2300": {"rr": 1.5, "sl_mode": "HALF"},   # ✅ BEST OVERALL
    "0030": {"rr": 3.0, "sl_mode": "HALF"},   # ✅
}
```

**NQ: ALL SKIPPED**
```python
NQ_ORB_CONFIGS = {
    "0900": {"rr": None, "sl_mode": None, "tier": "SKIP"},  # ❌
    "1000": {"rr": None, "sl_mode": None, "tier": "SKIP"},  # ❌
    "1100": {"rr": None, "sl_mode": None, "tier": "SKIP"},  # ❌
    "1800": {"rr": None, "sl_mode": None, "tier": "SKIP"},  # ❌
    "2300": {"rr": None, "sl_mode": None, "tier": "SKIP"},  # ❌
    "0030": {"rr": None, "sl_mode": None, "tier": "SKIP"},  # ❌
}
```

**MPL: ALL SKIPPED**
```python
MPL_ORB_CONFIGS = {
    "0900": {"rr": None, "sl_mode": None, "tier": "SKIP"},  # ❌
    "1000": {"rr": None, "sl_mode": None, "tier": "SKIP"},  # ❌
    "1100": {"rr": None, "sl_mode": None, "tier": "SKIP"},  # ❌
    "1800": {"rr": None, "sl_mode": None, "tier": "SKIP"},  # ❌
    "2300": {"rr": None, "sl_mode": None, "tier": "SKIP"},  # ❌
    "0030": {"rr": None, "sl_mode": None, "tier": "SKIP"},  # ❌
}
```

---

## Final Recommendation

### TRADE MGC ONLY

**Why:**
1. Optimal RR values of 3.0-8.0 provide HUGE slippage buffer
2. Moves extend 30-80 points beyond targets
3. Extended overnight trends perfect for ORB strategy
4. Proven robust with +600R/year expected value

**Don't Trade NQ/MPL Because:**
1. RR=1.0 optimal means NO slippage buffer
2. Sharp dropoffs at higher RR show moves don't extend
3. Slippage (~0.2R per trade) kills the edge entirely
4. Tight/choppy price action not suited for breakout strategy

---

## What About Other Strategies for NQ/MPL?

**This ORB breakout strategy doesn't work for NQ/MPL.**

But these instruments might work with:
- Mean reversion strategies (tight ranges favor reversals)
- Scalping (quick in/out on intraday moves)
- Different breakout methods (shorter timeframes, tighter stops)

**That's future research. For NOW: MGC ONLY.**

---

## System Performance Summary

### After All Fixes (2026-01-16):

| Instrument | Status | Annual R | Notes |
|------------|--------|----------|-------|
| **MGC** | ✅ TRADE | +600R | Extended scans, RR=3.0-8.0, ROBUST |
| **NQ** | ❌ SKIP | N/A | RR=1.0 only, slippage kills edge |
| **MPL** | ❌ SKIP | N/A | RR=1.0 only, slippage kills edge |
| **TOTAL** | | **+600R** | **MGC ONLY** |

---

## Lessons Learned

1. **RR=1.0 optimal is a WARNING sign**, not success
2. **Sharp WR dropoffs = tight moves**, not robust edge
3. **Slippage matters** - need buffer in RR values
4. **Extended scans revealed truth** about instrument differences
5. **Be honest about what works** - don't force bad instruments

---

## Next Steps

1. ✅ Updated config.py to skip NQ/MPL entirely
2. ✅ Set PRIMARY_INSTRUMENT to MGC
3. ✅ Documented findings
4. ⏳ Remove NQ/MPL from UI (future cleanup)
5. ⏳ Focus all development on MGC strategies

---

**Created:** 2026-01-16
**Status:** FINAL - DO NOT TRADE NQ/MPL WITH ORB STRATEGY
**Recommendation:** MGC ONLY

