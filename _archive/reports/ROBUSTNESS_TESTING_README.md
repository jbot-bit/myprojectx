# Robustness Testing System

Complete end-to-end pipeline for testing backtest edge robustness by comparing filtered vs no-filter performance.

## Overview

This system identifies profitable trading configs from your filtered backtest results, re-runs them WITHOUT filters (MAX_STOP=999999, ASIA_TP_CAP=999999), and compares performance to determine which edges are truly robust.

**Key Question:** Do your profitable edges depend on filters, or do they work regardless?

---

## Quick Start

### Option 1: Run Complete Pipeline (Recommended)

```bash
python run_complete_robustness_test.py
```

This executes all 5 steps automatically. Takes 5-15 minutes depending on system.

### Option 2: Run Steps Individually

```bash
# Step 1: Audit database
python audit_robustness_setup.py

# Step 2: Extract candidates
python extract_candidate_configs.py

# Step 4: Run robustness tests
python run_robustness_batch.py

# Step 5: Generate report
python generate_robustness_report.py
```

---

## System Components

### 1. audit_robustness_setup.py

**Purpose:** Validates database and identifies filtered results table

**What it does:**
- Confirms `gold.db` exists
- Finds all `orb_trades_5m*` tables
- Counts configs per table
- Identifies the filtered table (should have 570 configs)
- Describes schema
- Verifies MAX_STOP=100 and ASIA_TP_CAP=150 filters are applied

**Output:**
- `filtered_table_name.txt` - Name of filtered table for next steps

**Fail Conditions:**
- Database not found
- No orb_trades_5m tables exist
- Required columns missing

---

### 2. extract_candidate_configs.py

**Purpose:** Queries filtered table for profitable configs

**Criteria:**
- `trades >= 100` (adequate sample size)
- `total_r >= 20` (meaningful profit)

**What it does:**
- Builds SQL query for profitable configs
- Groups by: orb, close_confirmations, rr, sl_mode, buffer_ticks
- Displays session breakdown
- Shows top 10 configs

**Output:**
- `candidate_configs.csv` - Full details (trades, wins, WR, R, etc.)
- `candidate_configs.json` - Config keys only (for batch runner)

**Example Output:**
```
Found 69 candidate configs meeting criteria

By Session:
  10:00:  62 configs | +2311.0R |  29519 trades
  18:00:   7 configs |  +304.0R |   3517 trades
```

---

### 3. run_robustness_batch.py

**Purpose:** Re-runs all candidate configs WITHOUT filters

**Test Parameters:**
- `MAX_STOP_TICKS = 999999` (no limit)
- `ASIA_TP_CAP_TICKS = 999999` (no limit)

**What it does:**
- Loads all candidate configs from `candidate_configs.json`
- Creates `orb_robustness_results` table
- For each config:
  - Fetches daily features for that ORB
  - Runs full backtest (same logic as original, no filters)
  - Writes results to database
- Progress displayed per config

**Output:**
- Database table: `orb_robustness_results`
- Contains all trade-by-trade results for no-max tests

**Performance:**
- ~1-5 seconds per config
- 69 configs × 3 seconds = ~3.5 minutes total

---

### 4. generate_robustness_report.py

**Purpose:** Compare filtered vs no-max results and identify robust edges

**Classification System:**

1. **ROBUST** - Profitable in BOTH scenarios
   - Criteria: Both filtered_r >= 20 AND nomax_r >= 20
   - These are your highest-confidence edges

2. **FILTER-DEPENDENT** - Only profitable WITH filters
   - Criteria: filtered_r >= 20 but nomax_r < 20
   - Lose money without filters

3. **NO-FILTER-BETTER** - Only profitable WITHOUT filters
   - Criteria: nomax_r >= 20 but filtered_r < 20
   - Filters are hurting this edge

4. **MARGINAL** - Weak in both scenarios
   - Neither meets profitability threshold

**What it does:**
- Joins `orb_trades_5m_exec` and `orb_robustness_results`
- Calculates deltas (extra trades, R difference)
- Classifies each config
- Displays robust edges
- Calculates overall filter impact

**Output:**
- `robustness_comparison.csv` - Full comparison table
- `robust_edges.csv` - Robust edges only
- `ROBUSTNESS_REPORT.md` - Human-readable summary

**Example Output:**
```
Found 4 ROBUST edges

18:00 ORB | RR=2.0 | Confirm=1 | SL=half | Buffer=0.0
  WITH Filters:    +60.0R (504 trades, 37.0% WR)
  WITHOUT Filters: +60.0R (513 trades, 36.6% WR)
  Worst Case:      +60.0R
  Extra Trades:    9 (+1.8%)
  R Delta:         +0.0R (neutral)
```

---

## Understanding Results

### Robust Edges

**What they are:**
- Configs profitable with AND without filters
- High confidence - not dependent on specific filter values
- Lowest overfitting risk

**Trading Recommendation:**
- TRADE LIVE if worst_case_r > 50R
- PAPER TRADE if worst_case_r > 30R
- MONITOR if worst_case_r > 20R

### Filter-Dependent Edges

**What they are:**
- Only profitable when MAX_STOP=100 and ASIA_TP_CAP=150 are applied
- Lose money without filters

**Why this happens:**
- Filters prevent large-stop, low-probability trades
- Without filters, big losers drag down performance

**Trading Recommendation:**
- KEEP FILTERS if trading these configs
- Be cautious - higher overfitting risk

### R Delta Interpretation

**R Delta = nomax_r - filtered_r**

- **Positive (e.g., +50R):** Filters hurt performance
  - Filtered out profitable trades
  - Consider removing filters

- **Negative (e.g., -50R):** Filters help performance
  - Prevented losing trades
  - Keep filters

- **Near zero (±10R):** Filters neutral
  - Minimal impact either way

---

## Expected Results

Based on Phase 3 validation (24 configs tested):

- **Filters saved +440.5R** on tested configs
- **Most configs are FILTER-DEPENDENT**
- **~4-6 ROBUST edges** expected (17% of profitable configs)
- **10:00 and 18:00 ORBs** dominate profitable configs

---

## Files Created

### Input Files
- `filtered_table_name.txt` - Identified filtered table name

### Candidate Files
- `candidate_configs.csv` - Full profitable config details
- `candidate_configs.json` - Config keys for batch runner

### Output Files
- `robustness_comparison.csv` - Full comparison table
- `robust_edges.csv` - Robust edges only
- `ROBUSTNESS_REPORT.md` - Summary report

### Database Tables
- `orb_robustness_results` - No-max backtest results

---

## Database Schema

### orb_robustness_results

Same schema as `orb_trades_5m_exec`:

```sql
CREATE TABLE orb_robustness_results (
    date_local DATE NOT NULL,
    orb VARCHAR NOT NULL,
    close_confirmations INTEGER NOT NULL,
    rr DOUBLE NOT NULL,
    sl_mode VARCHAR NOT NULL,
    buffer_ticks DOUBLE NOT NULL,
    direction VARCHAR,
    entry_ts TIMESTAMP,
    entry_price DOUBLE,
    stop_price DOUBLE,
    target_price DOUBLE,
    stop_ticks DOUBLE,
    outcome VARCHAR,
    r_multiple DOUBLE,
    entry_delay_bars INTEGER,
    mae_r DOUBLE,
    mfe_r DOUBLE,
    PRIMARY KEY (date_local, orb, close_confirmations, rr, sl_mode, buffer_ticks)
)
```

**Key difference:** NO FILTERS applied (MAX_STOP=999999, ASIA_TP_CAP=999999)

---

## Troubleshooting

### Error: Database not found

```bash
[FAIL] Database not found: gold.db
```

**Solution:** Run from project root directory where `gold.db` exists

### Error: filtered_table_name.txt not found

```bash
[FAIL] filtered_table_name.txt not found. Run audit_robustness_setup.py first.
```

**Solution:** Run Step 1 first to identify filtered table

### Error: candidate_configs.json not found

```bash
[FAIL] candidate_configs.json not found. Run extract_candidate_configs.py first.
```

**Solution:** Run Step 2 to extract candidate configs

### Error: orb_robustness_results table not found

```bash
[FAIL] orb_robustness_results table not found. Run run_robustness_batch.py first.
```

**Solution:** Run Step 4 to create and populate robustness results

### No candidates found

```bash
[WARN] No candidates found. Try lowering thresholds (trades >= 50, total_r >= 10)
```

**Solution:** Adjust criteria in `extract_candidate_configs.py`:
- Change `>= 100` to `>= 50` for trades
- Change `>= 20` to `>= 10` for total_r

---

## Advanced Usage

### Re-run Specific Configs

Edit `candidate_configs.json` to include only specific configs, then run:

```bash
python run_robustness_batch.py
```

### Test Different Filter Values

Modify `run_robustness_batch.py`:

```python
# Example: Test with MAX_STOP=150 instead of no limit
MAX_STOP_TICKS = 150
ASIA_TP_CAP_TICKS = 200
```

### Export to Different Table

Modify `ensure_robustness_table()` function to use different table name.

---

## Performance Optimization

### Current Performance

- ~69 configs
- ~3-5 seconds per config
- **Total: ~3-5 minutes**

### If Running Full Grid (570 configs)

- Estimated: 30-45 minutes
- Consider running overnight

### Optimization Tips

1. **Reduce candidates:** Raise thresholds (trades >= 200, total_r >= 50)
2. **Parallel processing:** Modify batch runner to use multiprocessing
3. **Cache daily features:** Store in memory instead of re-querying

---

## Next Steps After Running

1. **Read ROBUSTNESS_REPORT.md**
   - Review robust edges
   - Check filter recommendations

2. **Analyze robust_edges.csv**
   - Sort by worst_case_r
   - Identify highest-confidence trades

3. **Paper Trade Top Edges**
   - Start with ROBUST edges (worst_case_r > 50R)
   - Track 20-30 trades before going live

4. **Update TRADING_RULESET.md**
   - Replace with only ROBUST edges
   - Remove filter-dependent configs if going no-max

---

## Technical Notes

### Why Rebuild Instead of Using Existing Scripts?

The original backtest scripts (`backtest_orb_exec_5mhalfsl.py`) are designed for CLI use with argparse. Rather than using subprocess to call them 69 times, we:

1. Extract the core backtest logic
2. Run it programmatically in a loop
3. Write results directly to database

**Benefits:**
- Faster (no subprocess overhead)
- Better error handling
- Progress tracking
- Single database connection

### Backtest Logic Validation

The robustness batch runner uses **identical logic** to the original scripts:

- Same entry detection (N consecutive closes outside ORB)
- Same stop calculation (full/half SL + buffer)
- Same target calculation (RR × risk)
- Same outcome detection ("both hit = LOSS" logic)
- Same R-multiple calculation

**Only difference:** Filter values (999999 vs 100/150)

---

## FAQ

**Q: Why only 69 candidates instead of 570?**

A: Only 69 configs meet the profitability criteria (trades >= 100, total_r >= 20). The other 501 are either:
- Too few trades (< 100)
- Not profitable enough (< 20R)
- Losing money

**Q: Why are only 10:00 and 18:00 ORBs profitable?**

A: Other sessions (09:00, 11:00, 23:00, 00:30) don't have any configs meeting both criteria. They may have:
- Configs with R > 20 but trades < 100
- Configs with trades > 100 but R < 20
- All configs losing money

**Q: How do I test ALL 570 configs?**

A: Lower the thresholds in `extract_candidate_configs.py`:

```python
HAVING COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) >= 50  # was 100
   AND SUM(r_multiple) FILTER (WHERE outcome IN ('WIN','LOSS')) >= 0  # was 20
```

This will test all configs with any profit, but will take much longer.

**Q: Can I run this on a different database?**

A: Yes, change `DB_PATH = "gold.db"` in all scripts to point to your database.

**Q: Will this overwrite my existing backtest results?**

A: No, results are written to a NEW table: `orb_robustness_results`. Your `orb_trades_5m_exec` table is not modified.

---

**Created:** 2026-01-12
**Author:** Robustness Testing System
**Version:** 1.0
