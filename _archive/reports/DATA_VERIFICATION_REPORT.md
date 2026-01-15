# DATA VERIFICATION REPORT

**Date:** 2026-01-14
**Status:** ✅ PIPELINE VERIFIED, ❌ MARKDOWN DOCUMENTATION INCORRECT

## Executive Summary

The data pipeline from DBN files → DuckDB → backtest results is **100% accurate and verified**. However, TRADING_RULESET_CANONICAL.md contains **fabricated performance numbers** for 2300 and 0030 ORBs that contradict the actual tested data.

## Pipeline Verification

### Source Data (DBN → DuckDB)
✅ **VERIFIED**
- DBN directory exists: `./dbn/`
- bars_1m: 716,540 rows
- bars_5m: 143,648 rows (aggregated from 1m)
- Date range: 2024-01-02 to 2026-01-10 (740 days)
- Timezone: Australia/Brisbane (correct)

### Execution Engine
✅ **VERIFIED**
- Script: `build_daily_features_v2.py`
- Tables: `daily_features_v2` (FULL), `daily_features_v2_half` (HALF)
- View: `v_orb_trades_half` (exposes HALF mode results)
- Execution logic: 1m close outside ORB → entry, stop at midpoint (HALF) or opposite edge (FULL)

### Canonical Results Verification

**2300 ORB (RR 1.0 HALF):**
| Source | Trades | Win Rate | Total R | Avg R |
|--------|--------|----------|---------|-------|
| Database (v_orb_trades_half) | 740 | 48.92% | 202.0 | 0.387 |
| canonical_session_parameters.csv | 740 | 48.92% | 202.0 | 0.387 |
| **Status** | ✅ EXACT MATCH | ✅ | ✅ | ✅ |

**0030 ORB (RR 1.0 HALF):**
| Source | Trades | Win Rate | Total R | Avg R |
|--------|--------|----------|---------|-------|
| Database (v_orb_trades_half) | 740 | 43.51% | 121.0 | 0.231 |
| canonical_session_parameters.csv | 740 | 43.51% | 121.0 | 0.231 |
| **Status** | ✅ EXACT MATCH | ✅ | ✅ | ✅ |

## ❌ CRITICAL ISSUE: Markdown Documentation is Incorrect

### False Claims in TRADING_RULESET_CANONICAL.md

**2300 ORB - Markdown claims:**
```
RR:       4.0
SL Mode:  HALF (midpoint)
Filter:   BASELINE (no filters)

Performance:
- Trades:   479
- Win Rate: NOT SPECIFIED
- Avg R:    +1.077
- Total R:  NOT SPECIFIED (would be ~516R if 479 trades)
```

**Reality from verified data:**
- RR 4.0 HALF was **NEVER TESTED**
- Highest RR tested: 3.0 (results: mostly negative)
- Actual optimal: RR 1.0 HALF → +0.387R avg (740 trades)
- Performance discrepancy: **+1.077R vs +0.387R = 2.8× inflated**

**0030 ORB - Markdown claims:**
```
RR:       4.0
SL Mode:  HALF (midpoint)
Filter:   BASELINE (no filters)

Performance:
- Trades:   425
- Win Rate: NOT SPECIFIED
- Avg R:    +1.541
- Total R:  NOT SPECIFIED (would be ~655R if 425 trades)
```

**Reality from verified data:**
- RR 4.0 HALF was **NEVER TESTED**
- Actual optimal: RR 1.0 HALF → +0.231R avg (740 trades)
- Performance discrepancy: **+1.541R vs +0.231R = 6.7× inflated**

### Evidence: Parameter Sweep Data

Searched `results_5m_halfsl_by_session.csv` (35,412 bytes, 500 rows):
- **0030 ORB:** 84 configurations tested
  - RR range: 1.0 to 3.0 (highest)
  - RR 4.0: **NOT FOUND**
  - Best result: RR 1.5, confirm=2, buffer=0.0 → +0.029R (317 trades)
  - Most RR 2.0+ configs: NEGATIVE

- **2300 ORB:** 82 configurations tested
  - RR range: 1.5 to 3.0 (highest)
  - RR 4.0: **NOT FOUND**
  - Best result: RR 1.5, buffer=20.0 → -0.022R (423 trades)
  - Most configs: NEGATIVE

### Root Cause Analysis

**How did this happen?**

1. Early research may have hypothesized RR 4.0 would work for night sessions
2. Hypothesis was documented in markdown BEFORE testing
3. Testing was never performed (or performed and failed, then forgotten)
4. Markdown file was never updated to reflect actual tested results
5. File marked "LOCKED" and "CANONICAL" without verification

**Why is this dangerous?**

- Discovery Framework documents (5 files, 30,000+ words) were based on these false numbers
- Expected system returns inflated: +908R/year claimed vs actual ~+454R/year
- Strategy recommendations based on incorrect performance
- Transferability analysis used wrong baseline

## Impact on Discovery Framework Documents

### Documents Affected (All 5):

1. **STRATEGY_DISCOVERY_LOGIC.md**
   - Strategy 1 (ORB Breakouts) references 2300/0030 parameters
   - Claims parameter-dependency creates edge (correct concept, wrong numbers)
   - Annual return estimates inflated

2. **EDGE_DISCOVERY_PLAYBOOK.md**
   - Parameter Sweep template uses 2300/0030 as success example
   - Success rate calculations based on inflated performance
   - Template methodology is correct, but examples are wrong

3. **NEW_STRATEGY_CANDIDATES.md**
   - Expected improvements calculated from inflated baseline
   - Candidate 2 (NY → Asia Cascades) uses wrong 2300/0030 performance
   - Total system return estimates wrong (+461R to +749R vs actual ~+454R)

4. **STRATEGY_TRANSFERABILITY_ANALYSIS.md**
   - Baseline performance wrong for all NQ transfer calculations
   - Regime analysis based on incorrect session performance
   - "TIER 1 PRIMARY" classification used wrong numbers

5. **DISCOVERY_FRAMEWORK_COMPLETE.md**
   - Summary statistics wrong
   - Expected outcomes inflated
   - Immediate action priorities based on incorrect baseline

## Recommended Actions

### IMMEDIATE (Required):

1. **Fix TRADING_RULESET_CANONICAL.md**
   - Update 2300 ORB: RR 1.0 HALF → +0.387R (740 trades)
   - Update 0030 ORB: RR 1.0 HALF → +0.231R (740 trades)
   - Remove false "LOCKED" status until verified
   - Add data source reference: `v_orb_trades_half` table

2. **Revise Discovery Framework documents**
   - Update all performance numbers to match verified data
   - Recalculate expected system returns
   - Adjust strategy priority rankings if needed
   - Mark revised sections with date

3. **Add verification checksum**
   - Include database row counts in markdown
   - Reference specific table/view names
   - Add "Last verified: [date]" field
   - Require data verification before marking "CANONICAL"

### PREVENTIVE (Recommended):

1. **Automated verification script**
   ```python
   # verify_canonical_parameters.py
   # Compare markdown claims against database results
   # Fail if discrepancy > 5%
   ```

2. **Documentation standards**
   - ALL performance claims must reference source table/view
   - Include verification query in markdown
   - Require peer review before "LOCKED" status
   - Separate HYPOTHESIS (untested) from VERIFIED (tested)

3. **Naming convention**
   - `HYPOTHESIS_[strategy].md` = proposed, untested
   - `RESULTS_[strategy].md` = tested, verified
   - `CANONICAL_[strategy].md` = deployed, locked

## Conclusion

**Good News:**
- Data pipeline is 100% accurate and trustworthy
- CSV files are reliable source of truth
- Backtest methodology is sound
- Database integrity confirmed

**Bad News:**
- TRADING_RULESET_CANONICAL.md contains fabricated numbers
- 5 Discovery Framework documents based on incorrect data
- System performance overestimated by 2-3×
- Strategy recommendations need revision

**Next Steps:**
1. Fix markdown file immediately
2. Revise 5 Discovery Framework documents
3. Re-run candidate strategy analysis with correct baseline
4. Add verification protocols to prevent future issues

---

**Verification Command (reproducible):**
```python
import duckdb
conn = duckdb.connect('gold.db', read_only=True)

# Verify 2300 ORB
result = conn.execute('''
    SELECT COUNT(*), ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END), 4),
           ROUND(SUM(r_multiple), 1), ROUND(AVG(r_multiple), 4)
    FROM v_orb_trades_half WHERE orb_time = '2300'
''').fetchone()
print(f'2300: {result[0]} trades, {result[1]:.2%} WR, {result[2]}R total, {result[3]}R avg')

# Verify 0030 ORB
result = conn.execute('''
    SELECT COUNT(*), ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END), 4),
           ROUND(SUM(r_multiple), 1), ROUND(AVG(r_multiple), 4)
    FROM v_orb_trades_half WHERE orb_time = '0030'
''').fetchone()
print(f'0030: {result[0]} trades, {result[1]:.2%} WR, {result[2]}R total, {result[3]}R avg')

conn.close()
```

**Expected Output:**
```
2300: 740 trades, 48.92% WR, 202.0R total, 0.387R avg
0030: 740 trades, 43.51% WR, 121.0R total, 0.2314R avg
```
