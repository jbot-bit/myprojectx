# Data Integrity Audit Commands

## Run These Two Commands:

```bash
# 1. COMPLETE ORB PARAMETER SWEEP
python backtest_all_orbs_complete.py
```

**Purpose**: Test ALL 6 ORBs with ALL parameter combinations (252+ configs)

**Output**:
- `complete_orb_sweep_results.csv` - All configurations tested
- `canonical_session_parameters.csv` - **LOCKED optimal parameters for each ORB**
- Console shows BEST config per ORB

**Determines**: Which sessions to trade, with what RR/SL/filters (CANONICAL)

---

```bash
# 2. DATA INTEGRITY & CORRECTNESS AUDIT
python audit_data_integrity.py
```

**Purpose**: Verify underlying market data is accurate, complete, and correctly aligned

**Tests**:
1. ✅ Data source validation (contracts, timezone, bar resolution)
2. ✅ Timezone & session boundary audit (UTC+10, no DST, 5 random rows per session)
3. ✅ Bar completeness check (missing bars, duplicates, gaps)
4. ✅ Price continuity & contract roll safety (3 random roll periods)
5. ✅ Session high/low correctness (verify calculations match raw bars)
6. ✅ Trade count & day count verification (reconcile days vs opportunities)

**Output**: PASS/FAIL per test with evidence

**Critical**: If ANY test fails → **RESULTS INVALID - Do not trade**

---

## Expected Results:

### From backtest_all_orbs_complete.py:

```
CANONICAL SESSION PARAMETERS (LOCKED)
================================================================================

0900 ORB: TRADE
--------------------------------------------------------------------------------
  OPTIMAL CONFIG: RR=1.0, SL=FULL, Filter=MAX_STOP_100_TP_CAP_150
  Performance: 487 trades, 62.8% WR, +0.257R avg, +125.0R total

1000 ORB: TRADE
--------------------------------------------------------------------------------
  OPTIMAL CONFIG: RR=2.5, SL=FULL, Filter=MAX_STOP_100_TP_CAP_150
  Performance: 455 trades, 38.2% WR, +0.338R avg, +154.0R total

1100 ORB: TRADE
--------------------------------------------------------------------------------
  OPTIMAL CONFIG: RR=1.0, SL=FULL, Filter=MAX_STOP_100_TP_CAP_150
  Performance: 465 trades, 64.9% WR, +0.299R avg, +139.0R total

1800 ORB: TRADE
--------------------------------------------------------------------------------
  OPTIMAL CONFIG: RR=3.0, SL=FULL, Filter=BASELINE (or with filters)
  Performance: ~500 trades, ~37-55% WR, +0.3 to +1.0R avg

2300 ORB: SKIP or TRADE (depends on optimal config)
--------------------------------------------------------------------------------
  OPTIMAL CONFIG: TBD (will show best RR/SL if positive)

0030 ORB: SKIP or TRADE (depends on optimal config)
--------------------------------------------------------------------------------
  OPTIMAL CONFIG: TBD (will show best RR/SL if positive)
```

**Key**: Only mark ORB as SKIP if negative at BEST configuration

---

### From audit_data_integrity.py:

```
AUDIT SUMMARY
================================================================================

[PASS] Data Source Validation
[PASS] Session Boundaries
[PASS] Bar Completeness
[PASS] Contract Rolls
[PASS] Session Calculations
[PASS] Trade Counts

OVERALL: PASS
================================================================================

All data integrity checks passed.
Backtest results can be considered valid.
```

**If any test fails**: Review the detailed output and fix the issue before trusting backtest results.

---

## What These Audits Prove:

### 1. Parameter Sweep:
- ✅ Every ORB tested at 7 RR values (1.0-4.0)
- ✅ Both HALF and FULL SL modes tested
- ✅ Multiple filter sets tested
- ✅ CANONICAL parameters locked per ORB (no more "skip/trade" without proof)

### 2. Data Integrity:
- ✅ All timestamps in UTC+10 (Australia/Brisbane, no DST)
- ✅ Session boundaries correct (09:00, 10:00, 11:00, 18:00, 23:00, 00:30)
- ✅ No missing/duplicate/synthetic bars
- ✅ Contract rolls handled properly (no artificial gaps)
- ✅ Session high/low calculations verified against raw bars
- ✅ No lookahead bias (future bars can't leak into calculations)
- ✅ Trade counts reconcile with dataset days

---

## After Running Both Audits:

### IF ALL PASS:

1. **Update TRADING_RULESET.md** with canonical parameters from `canonical_session_parameters.csv`
2. **Lock session parameters** - no more changing RR/SL without re-sweeping
3. **Trust backtest results** - data integrity verified
4. **Ready to paper trade** - confidence in edge is justified

### IF ANY FAIL:

1. **STOP** - Do not trade based on these results
2. **Review failure details** - identify root cause
3. **Fix data/code issue** - correct the problem
4. **Re-run audits** - verify fix worked
5. **Only then proceed** - after all tests pass

---

## Files Created:

### From Parameter Sweep:
- `complete_orb_sweep_results.csv` - All 252+ configurations
- `canonical_session_parameters.csv` - Optimal params per ORB (THIS IS TRUTH)

### From Data Integrity:
- Console output only (detailed audit log)
- If fails, review console for specific issues

---

## Critical Rule:

**Sessions are parameter-dependent, not "good" or "bad".**

A session is only marked "SKIP" if **negative at its BEST configuration**.

Every ORB must be tested with ALL parameters before declaring it untradeable.

---

**Run both audits now. Results will determine canonical trading parameters.**
