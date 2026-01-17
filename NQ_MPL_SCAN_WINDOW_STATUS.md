# NQ & MPL Scan Window Status - CRITICAL FINDINGS

## Date: 2026-01-16

## ⚠️ CRITICAL ISSUE DISCOVERED

---

## Summary

**MGC:** ✅ Extended scan windows (until 09:00 next day) - COMPLETE
**NQ:** ⚠️ **UNKNOWN** - needs verification
**MPL:** ⚠️ **UNKNOWN** - needs verification

---

## The Problem

### What We Know About MGC:
1. ✅ `execution_engine.py` has extended scan windows (all ORBs until 09:00 next day)
2. ✅ `build_daily_features_v2.py` uses execution_engine logic
3. ✅ `validated_strategies.py` has corrected RR values based on extended scans
4. ✅ `trading_app/config.py` synchronized with validated data
5. ✅ Apps work correctly with extended scan windows

### What We DON'T Know About NQ/MPL:
1. ❓ Were NQ/MPL configs validated with extended or short scan windows?
2. ❓ Do NQ/MPL backtests use same scan window logic as MGC?
3. ❓ Are current NQ/MPL RR values optimal?

---

## Current Codebase Analysis

### 1. execution_engine.py
**Status:** MGC-SPECIFIC ONLY

```python
SYMBOL = "MGC"  # Line 55 - Hardcoded to MGC!
TICK_SIZE = 0.1

def _orb_scan_end_local(orb: str, d: date) -> str:
    """All ORBs scan until 09:00 next day"""
    return f"{d + timedelta(days=1)} 09:00:00"  # Extended windows
```

**Issue:** This extended scan logic ONLY applies to MGC backtests!

### 2. build_daily_features_v2.py
**Status:** MGC-SPECIFIC ONLY

```python
SYMBOL = "MGC"  # Line 51 - Hardcoded!
DB_PATH = "gold.db"

# Uses execution_engine.py for trade simulation
# Writes to daily_features_v2 table (MGC data only)
```

**Issue:** NQ and MPL features were NOT built with this script!

### 3. NQ & MPL Data Tables

**NQ Data:**
- Table: `bars_1m_nq` (separate from MGC)
- Features: `daily_features_v2_nq` (if exists)
- Build script: **UNKNOWN** ❌

**MPL Data:**
- Table: `bars_1m_mpl` (separate from MGC)
- Features: `daily_features_v2_mpl` (exists, validated 2026-01-15)
- Build script: **UNKNOWN** ❌

### 4. Trading App Configs

**NQ Configuration (config.py lines 108-125):**
```python
NQ_ORB_CONFIGS = {
    "0900": {"rr": 1.0, "sl_mode": "FULL"},     # +0.145R avg
    "1000": {"rr": 1.5, "sl_mode": "FULL"},     # +0.174R avg
    "1100": {"rr": 1.5, "sl_mode": "FULL"},     # +0.260R avg
    "1800": {"rr": 1.5, "sl_mode": "HALF"},     # +0.257R avg
    "2300": {"rr": None, "sl_mode": None},      # SKIP (negative)
    "0030": {"rr": 1.0, "sl_mode": "HALF"},     # +0.292R avg
}
```

**Question:** Were these RR values validated with extended scan windows?
**Answer:** ❓ **UNKNOWN** - no documentation of scan windows used

**MPL Configuration (config.py lines 127-147):**
```python
# VALIDATED CONFIGURATION (2026-01-15)
# Backtest: 365 days (2025-01-13 to 2026-01-12)
# Total: +288R, ALL 6 ORBs profitable
MPL_ORB_CONFIGS = {
    "0900": {"rr": 1.0, "sl_mode": "FULL"},     # 57.6% WR, +55R
    "1000": {"rr": 1.0, "sl_mode": "FULL"},     # 56.1% WR, +31R
    "1100": {"rr": 1.0, "sl_mode": "FULL"},     # 67.1% WR, +88R (BEST!)
    "1800": {"rr": 1.0, "sl_mode": "FULL"},     # 55.1% WR, +27R
    "2300": {"rr": 1.0, "sl_mode": "FULL"},     # 62.9% WR, +77R (EXCELLENT!)
    "0030": {"rr": 1.0, "sl_mode": "FULL"},     # 58.0% WR, +52R
}
```

**Validated:** 2026-01-15 (yesterday)
**Scan windows used:** ❓ **UNKNOWN** - not documented

---

## Critical Questions

### For NQ:

1. **When were these configs validated?**
   - No date in comments
   - No scan window documentation
   - No reference to validation script

2. **What scan windows were used?**
   - If short windows (85 min): RR values may be underestimated
   - If extended windows (09:00 next day): RR values may be correct
   - **Currently unknown**

3. **Is NQ 2300 really negative?**
   - Currently marked as "SKIP"
   - But MGC 2300 is **BEST OVERALL** with extended scans
   - Was NQ 2300 tested with short scan windows and thus appeared negative?

4. **Could NQ have higher optimal RR values?**
   - Current configs: RR=1.0-1.5
   - If tested with short scans, may be underestimated
   - Potential for higher RR with extended scans?

### For MPL:

1. **What scan windows were used on 2026-01-15?**
   - Validated yesterday
   - No scan window info in config comments
   - Need to find the validation script

2. **Are all RR=1.0 configs optimal?**
   - All 6 ORBs use RR=1.0
   - MGC showed massive improvements with higher RR when extending scans
   - Could MPL benefit from higher RR values?

3. **Could MPL have MUCH better performance?**
   - Current: +288R/year (all ORBs combined)
   - With extended scans + optimized RR: potentially +400-500R/year?

---

## Likely Scenarios

### Scenario A: NQ/MPL Used SHORT Scan Windows ⚠️

**Evidence:**
- MGC configs were originally validated with short scans (before Jan 16 fix)
- NQ/MPL configs show conservative RR values (1.0-1.5)
- NQ 2300 marked as "SKIP" (but MGC 2300 is best overall with extended scans!)
- No mention of extended scan windows in NQ/MPL documentation

**Impact:**
- Current NQ/MPL configs are **UNDERESTIMATED**
- Missing big moves (like MGC was missing)
- Optimal RR values likely **MUCH HIGHER**
- Performance could be **50-100% BETTER** with extended scans

**Action Needed:**
- Re-run NQ/MPL backtests with extended scan windows
- Find optimal RR values for each ORB
- Update configs with corrected values

### Scenario B: NQ/MPL Used EXTENDED Scan Windows ✅

**Evidence:**
- MPL validated very recently (2026-01-15), same day as MGC scan fix awareness
- High win rates (55-67%) suggest captures most targets
- Conservative RR values may be intentional (different instruments)

**Impact:**
- Current configs are **CORRECT**
- NQ/MPL naturally have lower RR potential than MGC
- Performance is already optimized

**Action Needed:**
- Verify scan windows were extended
- Document scan window methodology
- Confirm RR values are optimal

---

## Live Trading App Implications

### Current App Behavior:

**For MGC:** ✅ CORRECT
- Uses extended scan window logic via strategy_engine
- Detects ORBs in real-time (zero lookahead)
- Applies corrected RR values

**For NQ:** ⚠️ **POTENTIALLY WRONG**
- Uses NQ_ORB_CONFIGS from config.py
- If those configs were validated with short scans: **RR values are wrong**
- May be exiting winning trades too early
- Missing big moves

**For MPL:** ⚠️ **POTENTIALLY WRONG**
- Uses MPL_ORB_CONFIGS from config.py
- If validated with short scans: **RR values are wrong**
- All using RR=1.0 seems suspiciously conservative
- May have much higher optimal RR

### Strategy Engine Handling:

**Code (strategy_engine.py lines 64-77):**
```python
def _load_instrument_configs(self):
    if self.instrument in ["NQ", "MNQ"]:
        self.orb_configs = NQ_ORB_CONFIGS
        self.orb_size_filters = NQ_ORB_SIZE_FILTERS
    elif self.instrument == "MPL":
        # NOT HANDLED! Defaults to MGC configs ❌
        self.orb_configs = MGC_ORB_CONFIGS
    else:
        self.orb_configs = MGC_ORB_CONFIGS
```

**CRITICAL BUG FOUND:**
- ✅ NQ configs load correctly
- ❌ **MPL configs DON'T LOAD!**
- MPL defaults to MGC configs (WRONG!)

**Impact:**
- Trading MPL in live app uses **WRONG CONFIG VALUES**
- Uses MGC RR values (6.0, 8.0, 3.0, 1.5, 1.5, 3.0)
- Instead of MPL RR values (1.0 for all)
- **DANGEROUS FOR LIVE TRADING!**

---

## Action Items (URGENT)

### 1. Fix MPL Strategy Engine ⚠️ **CRITICAL**

**File:** `trading_app/strategy_engine.py` line 64-77

**Current Code:**
```python
def _load_instrument_configs(self):
    if self.instrument in ["NQ", "MNQ"]:
        self.orb_configs = NQ_ORB_CONFIGS
        self.orb_size_filters = NQ_ORB_SIZE_FILTERS
    else:
        # Defaults to MGC
        self.orb_configs = MGC_ORB_CONFIGS
```

**Fixed Code:**
```python
def _load_instrument_configs(self):
    if self.instrument in ["NQ", "MNQ"]:
        self.orb_configs = NQ_ORB_CONFIGS
        self.orb_size_filters = NQ_ORB_SIZE_FILTERS
    elif self.instrument in ["MPL", "PL"]:
        self.orb_configs = MPL_ORB_CONFIGS
        self.orb_size_filters = MPL_ORB_SIZE_FILTERS
    else:
        # Default to MGC
        self.orb_configs = MGC_ORB_CONFIGS
        self.orb_size_filters = MGC_ORB_SIZE_FILTERS
```

### 2. Investigate NQ/MPL Scan Windows

**Find:**
- What scripts were used to validate NQ/MPL configs?
- What scan windows were used?
- When were they validated?

**Check:**
- `_archive/experiments/` for NQ/MPL backtest scripts
- Any notes or docs mentioning NQ/MPL validation
- Database queries to see if daily_features_v2_nq/mpl exist

### 3. Re-validate NQ/MPL with Extended Scans

**If short scans were used:**
- Create NQ/MPL versions of execution_engine.py
- Or modify existing to accept instrument parameter
- Re-run backtests with extended scan windows (09:00 next day)
- Find optimal RR values for each ORB
- Update configs

**Potential improvements:**
- NQ 2300 may be profitable with extended scans (currently SKIP)
- MPL ORBs may have much higher optimal RR (currently all 1.0)
- Overall system performance could improve 50-100%

### 4. Document Scan Windows

**Add to config.py:**
- Document what scan windows were used for each instrument
- Add validation dates
- Add reference to validation scripts
- Add notes about scan window methodology

---

## Risk Assessment

### For Live Trading:

**MGC:** ✅ **SAFE**
- Extended scan windows confirmed
- Configs validated correctly
- Ready for live trading

**NQ:** ⚠️ **MEDIUM RISK**
- Configs may be based on short scan windows
- May exit winners too early (underestimated RR)
- May mark profitable setups as SKIP (2300 ORB)
- **Recommend re-validation before live trading**

**MPL:** 🚨 **HIGH RISK**
- **CRITICAL BUG:** Strategy engine doesn't load MPL configs!
- Uses MGC configs instead (WRONG values!)
- **DO NOT TRADE MPL LIVE until fixed**
- After fix, still needs scan window verification

---

## Recommendations

### Immediate (Today):

1. ✅ **Fix MPL strategy engine bug** (5 minutes)
2. ✅ **Verify fix with test** (5 minutes)
3. ✅ **Update both apps** (app_trading_hub.py and app_simplified.py)

### Short Term (This Week):

1. ⏳ **Find NQ/MPL validation scripts**
2. ⏳ **Verify scan windows used**
3. ⏳ **Document findings**

### Medium Term (Next 1-2 Weeks):

1. ⏳ **If short scans were used: Re-validate NQ/MPL with extended scans**
2. ⏳ **Find optimal RR values**
3. ⏳ **Update configs**
4. ⏳ **Re-test apps**

---

## Conclusion

**MGC:** ✅ Fully validated, extended scan windows, ready to go

**NQ:** ⚠️ Scan windows unknown, may need re-validation

**MPL:** 🚨 Critical bug + scan windows unknown, **DO NOT TRADE LIVE**

**Next Steps:**
1. Fix MPL bug immediately
2. Investigate NQ/MPL validation history
3. Re-validate if needed
4. Update this document with findings

---

**Created:** 2026-01-16
**Priority:** HIGH
**Status:** Investigation ongoing
