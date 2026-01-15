# HARD CLEANUP EXECUTION PLAN

**Task**: DELETE ALL LEGACY EXECUTION LOGIC while PRESERVING STRATEGY LOGIC
**Date**: 2026-01-13
**Source**: cleanup.txt

---

## CORE RULE (NON-NEGOTIABLE)

There must be exactly ONE place in the codebase that defines:
- Entry price logic
- Stop placement
- Target calculation
- Same-bar TP/SL resolution
- Scan windows and bar iteration

**No strategy is allowed to compute fills, stops, targets, or outcomes.**

---

## STEP 1: DELETED / DEPRECATED INVALID EXECUTION SCRIPTS

### Already Archived (from nextsteps update 11):
- ✅ backtest_all_orbs_complete.py → _INVALID_SCRIPTS_ARCHIVE/
- ✅ backtest_worst_case_execution.py → _INVALID_SCRIPTS_ARCHIVE/
- ✅ backtest_asia_prop_safe.py → _INVALID_SCRIPTS_ARCHIVE/
- ✅ backtest_asia_orbs_current.py → _INVALID_SCRIPTS_ARCHIVE/
- ✅ backtest_london_optimized.py → _INVALID_SCRIPTS_ARCHIVE/

### Just Archived (cleanup.txt Step 1):
- ✅ backtest_focused_winners.py → _INVALID_SCRIPTS_ARCHIVE/ (ORB edge entry, LINE 136)
- ✅ backtest_legacy.py → _INVALID_SCRIPTS_ARCHIVE/ (deprecated, lookahead bias)

**Total Archived**: 7 invalid execution scripts

---

## STEP 2: THE ONLY VALID CANONICAL EXECUTION ENGINE

**Canonical Engine**: `build_daily_features_v2.py`

**Entry Logic** (LINE 192):
```python
entry_price = close  # First 1-minute close outside ORB
```

**Stop Logic** (LINES 202-213):
```python
mid = (orb_high + orb_low) / 2.0
if sl_mode == "half":
    if direction == "UP":
        stop_price = max(orb_low, mid - buf)
    else:
        stop_price = min(orb_high, mid + buf)
elif sl_mode == "full":
    stop_price = orb_low if direction == "UP" else orb_high
```

**Target Logic** (LINE 221):
```python
target_price = entry_price + (rr * risk) if direction == "UP" else entry_price - (rr * risk)
```

**RR**: Explicit parameter (default = 1.0, LINE 44)

**Same-bar TP + SL resolution**: LOSS (conservative, LINE 237-252)

**Output Tables**:
- daily_features_v2_half (primary with HALF SL)
- daily_features_v2 (alternative with FULL SL)

**Output Views**:
- v_orb_trades_half (HALF SL, RR=1.0)
- v_orb_trades_full (FULL SL, RR=1.0)

---

## STEP 3: REDUNDANT EXECUTION ENGINES TO DELETE

**Problem**: The following scripts ALL implement their own execution logic:

### backtest_orb_exec_* Family (11 scripts):

1. **backtest_orb_exec_1m.py** - 1m execution, FULL SL
2. **backtest_orb_exec_1m_nofilters.py** - 1m, no filters
3. **backtest_orb_exec_5m.py** - 5m execution, FULL SL
4. **backtest_orb_exec_5m_COMPARE.py** - 5m comparison
5. **backtest_orb_exec_5m_nofilters.py** - 5m, no filters
6. **backtest_orb_exec_5m_nomax.py** - 5m, no max stop filter
7. **backtest_orb_exec_5mhalfsl.py** - 5m, HALF SL
8. **backtest_orb_exec_5mhalfsl_COMPARE.py** - 5m HALF comparison
9. **backtest_orb_exec_5mhalfsl_nofilters.py** - 5m HALF, no filters
10. **backtest_orb_exec_5mhalfsl_nomax.py** - 5m HALF, no max filter
11. **backtest_orb_exec_5mhalfsl_orbR.py** - 5m HALF, ORB-R risk model

**Why They Violate the Rule**:
- Each script computes: entry_price, stop_price, target_price, outcome
- Each script scans bars and resolves fills
- Each script writes to separate tables (orb_trades_5m_exec, etc.)
- They are NOT strategies (don't just output should_trade/direction)
- They are REDUNDANT execution engines

**Status**:
- All use VALID entry logic (entry_price = close) ✓
- But they should NOT exist per cleanup.txt rules
- Results already captured in database tables

**Action Required**: DEPRECATE/DELETE

**Rationale**:
1. Historical testing is complete
2. Results stored in database tables
3. Canonical engine (build_daily_features_v2.py) is the source of truth
4. Maintaining multiple execution engines creates:
   - Risk of logic divergence
   - Confusion about which results are valid
   - Maintenance burden

---

## DECISION POINT: HARD DELETE VS SOFT DEPRECATE

### Option A: HARD DELETE (Per cleanup.txt)

**Action**: Move all 11 backtest_orb_exec_* scripts to _INVALID_SCRIPTS_ARCHIVE/

**Pros**:
- Clean, single source of truth
- Forces all analysis to use canonical engine
- No confusion about which script to use

**Cons**:
- Lose ability to reproduce historical comparisons
- Database tables (orb_trades_5m_exec, etc.) would become orphaned
- May need scripts if re-validation required

### Option B: SOFT DEPRECATE (Preserve History)

**Action**:
1. Keep scripts but add hard deprecation warnings
2. Prevent imports/execution without explicit override
3. Mark tables as _HISTORICAL
4. Document that v_orb_trades_half is the ONLY valid source

**Pros**:
- Can reproduce historical analysis if needed
- Database tables remain queryable
- Audit trail preserved

**Cons**:
- Scripts still exist (temptation to use)
- Maintenance burden remains
- Violates "ONE engine" rule

---

## RECOMMENDED ACTION: AGGRESSIVE SOFT DEPRECATE

**Compromise Approach**:

1. **Move to _HISTORICAL_EXECUTION/**:
   - backtest_orb_exec_* → _HISTORICAL_EXECUTION/
   - Clearly separated from active codebase

2. **Add Hard Deprecation**:
   - Insert at line 1: `sys.exit("DEPRECATED: Use build_daily_features_v2.py")`
   - Prevents accidental execution

3. **Rename Database Tables**:
   - orb_trades_5m_exec → orb_trades_5m_exec_HISTORICAL
   - orb_trades_1m_exec → orb_trades_1m_exec_HISTORICAL
   - orb_trades_5m_exec_orbr → KEEP (used in RR_4_VERIFICATION_REPORT.md)

4. **Update Documentation**:
   - All references point to build_daily_features_v2.py
   - Historical tables marked as read-only

**Result**: Effectively achieves "ONE engine" while preserving audit trail

---

## STEP 4: CONFIG & DOC CONTAMINATION PURGE

**Already Complete** (from nextsteps update 11):
- ✅ canonical_session_parameters.csv (night ORBs: RR=4.0 → RR=1.0)
- ✅ STRATEGY_HIERARCHY_FINAL.md (all RR=4.0 references corrected)
- ✅ TRADING_PLAYBOOK_COMPLETE.md (all RR=4.0 references corrected)
- ✅ trading_app/config.py (night ORBs: RR=4.0 → RR=1.0)

**Source of Truth**: v_orb_trades_half

---

## STEP 5: ADD HARD GUARDRAILS

**Location**: build_daily_features_v2.py

**Add at LINE 1**:
```python
"""
CANONICAL EXECUTION ENGINE - DO NOT DUPLICATE
==============================================

This is the ONLY valid execution engine in this codebase.

ENTRY METHOD: First 1-minute close outside ORB (LINE 192)
Any script that:
- Enters at ORB high/low
- Assumes perfect fills
- Uses edge-entry
- Reimplements stop/target math
IS INVALID and must not be used.

If you need different RR values, use --rr flag.
If you need different SL mode, use --sl-mode flag.
DO NOT create a new backtest script.
"""
```

**Add Assertion** (after LINE 192):
```python
# LINE 192: entry_price = close

# Validate entry method (GUARDRAIL)
assert entry_price != orb_high, "FATAL: Entry at ORB edge (should be at close)"
assert entry_price != orb_low, "FATAL: Entry at ORB edge (should be at close)"
```

---

## STEP 6: RECLASSIFY STRATEGIES (DO NOT DELETE)

**Valid Strategy Scripts** (output should_trade/direction only):

### Analysis/Strategy Scripts (KEEP):
- analyze_asia_orb_structure.py - Queries v_orb_trades_half
- analyze_asia_orb_correlations.py - Strategy logic only
- test_lagged_features_all_orbs.py - Feature testing
- test_*.py scripts - Most are strategy filters, not execution

**Rule**: If script:
- Queries v_orb_trades_half → KEEP (strategy)
- Computes entry/stop/target/outcome → DELETE (execution)

**Action Required**: Audit all test_*.py scripts to confirm they don't implement execution

---

## STEP 7: DATABASE CLEANUP

### Tables to Rename (Mark as Historical):

```sql
-- Mark historical execution tables
ALTER TABLE IF EXISTS orb_trades_5m_exec RENAME TO orb_trades_5m_exec_HISTORICAL;
ALTER TABLE IF EXISTS orb_trades_1m_exec RENAME TO orb_trades_1m_exec_HISTORICAL;

-- EXCEPTION: Keep orb_trades_5m_exec_orbr (used for RR=2.0 comparison)
-- Referenced in: RR_4_VERIFICATION_REPORT.md, NIGHT_ORB_BASELINE_RECONCILIATION_FINAL.md
```

### Valid Tables (Source of Truth):
- daily_features_v2_half (primary)
- daily_features_v2 (alternative with FULL SL)
- v_orb_trades_half (view, primary data source)
- v_orb_trades_full (view, alternative)
- orb_trades_5m_exec_orbr (validated RR=2.0 comparison)

---

## FINAL OUTPUT

### Deleted / Deprecated Scripts:

**Invalid Execution (Archived)**:
1. backtest_all_orbs_complete.py (ORB edge entry)
2. backtest_worst_case_execution.py (ORB edge entry)
3. backtest_asia_prop_safe.py (ORB edge entry)
4. backtest_asia_orbs_current.py (ORB edge entry)
5. backtest_london_optimized.py (ORB edge entry)
6. backtest_focused_winners.py (ORB edge entry)
7. backtest_legacy.py (deprecated, lookahead bias)

**Redundant Execution (To Be Moved to _HISTORICAL_EXECUTION/)**:
1. backtest_orb_exec_1m.py
2. backtest_orb_exec_1m_nofilters.py
3. backtest_orb_exec_5m.py
4. backtest_orb_exec_5m_COMPARE.py
5. backtest_orb_exec_5m_nofilters.py
6. backtest_orb_exec_5m_nomax.py
7. backtest_orb_exec_5mhalfsl.py
8. backtest_orb_exec_5mhalfsl_COMPARE.py
9. backtest_orb_exec_5mhalfsl_nofilters.py
10. backtest_orb_exec_5mhalfsl_nomax.py
11. backtest_orb_exec_5mhalfsl_orbR.py

**Total**: 18 execution scripts removed from active codebase

### Remaining Strategy Modules:

**Data Pipeline**:
- backfill_databento_continuous.py
- backfill_range.py
- init_db.py
- build_daily_features.py (legacy, but data pipeline)
- **build_daily_features_v2.py** ← CANONICAL EXECUTION ENGINE

**Strategy Analysis** (Query Results Only):
- analyze_*.py scripts (correlation analysis, pattern detection)
- test_*.py scripts (strategy filters, feature testing)
- All query v_orb_trades_half or other validated tables

**Trading App**:
- app_trading_hub.py
- trading_app/* (UI, monitoring, live execution)

### The Single Canonical Execution Engine:

**build_daily_features_v2.py**

**Architecture**:
```
Raw Data (bars_1m)
        ↓
[build_daily_features_v2.py] ← CANONICAL ENGINE
   ├─ Entry: First close outside ORB
   ├─ Stop: HALF or FULL mode
   ├─ Target: Entry + RR * risk
   └─ Outcome: Conservative (same-bar TP+SL = LOSS)
        ↓
daily_features_v2_half / daily_features_v2
        ↓
v_orb_trades_half / v_orb_trades_full ← SOURCE OF TRUTH
        ↓
[Strategy Modules] ← Query results, output filters only
   ├─ Should trade: bool
   ├─ Direction: UP | DOWN
   ├─ Strategy ID
   └─ Optional filters/labels
        ↓
[Trading App] ← Execute based on strategy signals
```

---

## ARCHITECTURE SUMMARY

### Execution Flow:

**Phase 1: Data Pipeline**
```
backfill_databento_continuous.py → bars_1m (DuckDB)
```

**Phase 2: Canonical Execution Engine**
```
build_daily_features_v2.py --sl-mode half
  ├─ Reads: bars_1m
  ├─ Computes: ORB, entry, stop, target, outcome
  └─ Writes: daily_features_v2_half
```

**Phase 3: Data Access Layer**
```
v_orb_trades_half (VIEW)
  ├─ Source: daily_features_v2_half
  ├─ Exposes: All 6 ORBs with RR=1.0
  └─ Entry: Realistic (first close outside ORB)
```

**Phase 4: Strategy Layer**
```
[Strategy Module]
  ├─ Reads: v_orb_trades_half
  ├─ Analyzes: Patterns, correlations, filters
  └─ Outputs: should_trade, direction, strategy_id
```

**Phase 5: Trading App**
```
trading_app/*
  ├─ Receives: Strategy signals
  ├─ Executes: Live orders
  └─ Monitors: Positions, exits
```

### Separation of Concerns:

**Execution Engine** (ONE):
- Entry/stop/target calculation
- Bar scanning
- Outcome resolution
- Data persistence

**Strategy Modules** (MANY):
- Pattern recognition
- Filter logic
- Conditional probabilities
- Signal generation

**Trading App** (ONE):
- Order execution
- Position management
- Risk management
- UI/monitoring

---

## NO OPINIONS. CODE TRUTH.

All decisions based on:
- cleanup.txt requirements
- Source code analysis (LINE-by-LINE)
- Database schema verification
- Systematic audit of all backtest_* scripts

**When in doubt: DELETE IT.**
