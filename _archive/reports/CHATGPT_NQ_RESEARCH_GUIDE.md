# ChatGPT Guide: NQ Trading Research Framework

**Purpose**: Guide for continuing NQ (Nasdaq E-mini) trading research
**Date**: 2026-01-13
**Database**: `gold.db` (DuckDB)

---

## Project Overview

Trading research framework for NQ futures using Opening Range Breakout (ORB) strategies with zero-lookahead enforcement.

**Data Coverage**:
- **NQ**: 268 trading days (Jan 13 - Nov 21, 2025)
- **Bars**: 306,243 1-minute bars
- **Tables**: `bars_1m_nq`, `bars_5m_nq`, `daily_features_v2_nq`

---

## What Has Been Completed

### ✅ Phase 1: Data Pipeline
- DBN ingestion with continuous contract logic
- Data integrity audit (PASSED)
- Feature engineering with 6 ORBs (0900, 1000, 1100, 1800, 2300, 0030)
- MAE/MFE tracking for all ORBs

### ✅ Phase 2: Baseline Backtesting
- Universal backtest framework (MGC + NQ)
- **Best ORB**: 0030 (NYSE open) - 63.9% WR, +0.279R
- **Key Finding**: NQ favors US market hours (opposite of MGC/Gold)

### ✅ Phase 3: RR Optimization
- **Result**: All ORBs optimal at **RR = 1.0**
- **Why**: NQ is mean-reverting at ORB timescale
- Win rates collapse from 64% at 1R to 3% at 2R

### ✅ Phase 4: Filter Discovery
- **5 of 6 ORBs** improve 10-118% with ORB size filters
- Best improvements: 0900 (+118%), 1800 (+22%), 1100 (+22%)
- **Top 3 setups** average 65% WR, +0.299R/trade

### ✅ Phase 5: Dashboard Integration
- Symbol selector added (MGC/NQ dropdown)
- Dynamic data loading based on instrument

### ✅ Phase 6: Massive Moves Research
- Tested 2 patterns for 3R+ intraday runners
- **Result**: ❌ BOTH FAILED (negative expectancy, low WR)
- **Conclusion**: 3R+ intraday targets NOT repeatable on NQ
- **Recommendation**: Stick with proven 1R framework

---

## Database Schema

### Tables

**bars_1m_nq**:
- Columns: `ts_utc`, `ts_local`, `date_local`, `open`, `high`, `low`, `close`, `volume`
- 306,243 rows

**daily_features_v2_nq**:
- 268 rows (one per trading day)
- Session stats: `asia_high/low/range`, `london_high/low/range`, `ny_high/low/range`
- Pre-session: `pre_asia_*`, `pre_london_*`, `pre_ny_*`
- ORBs: `orb_0900_*`, `orb_1000_*`, `orb_1100_*`, `orb_1800_*`, `orb_2300_*`, `orb_0030_*`
- ORB fields: `high`, `low`, `size`, `break_dir`, `outcome`, `r_multiple`, `mae`, `mfe`, `stop_price`, `risk_ticks`

### Session Windows (Brisbane UTC+10)

| Session | Start | End | Description |
|---------|-------|-----|-------------|
| Pre-Asia | 07:00 | 09:00 | Before Asia open |
| Asia | 09:00 | 17:00 | Asian trading hours |
| Pre-London | 17:00 | 18:00 | Before London open |
| London | 18:00 | 23:00 | London overlap |
| Pre-NY | 23:00 | 00:30 (next day) | Before NYSE open |
| NY Cash | 00:30 | 02:00 (next day) | NYSE cash market |

---

## Key Findings Summary

### NQ Market Behavior

**Characteristics**:
1. **Mean-reverting at 1R scale** - Quick moves to 1R, then consolidation/reversal
2. **Best session**: NYSE open (0030) - equity index driven by US market
3. **High volatility** - Wider ranges than MGC
4. **False breakouts** - Many intraday fake-outs from algo sweeps

**Optimal Strategy**:
- Target: 1R only (don't chase higher)
- Entry: First close outside ORB
- Stop: Opposite ORB edge (FULL SL)
- Filters: ORB size-based per session

### Proven Edges

**Top 3 Setups** (with filters):
1. **0030 ORB** - 66% WR, +0.320R | Filter: ORB >= 37 points
2. **1800 ORB** - 64.6% WR, +0.292R | Filter: ORB 10-30 points
3. **1100 ORB** - 64.2% WR, +0.284R | Filter: ORB 6-19 points

**Expected Return**: ~0.33R/day (after slippage)

### What Doesn't Work

❌ **3R+ intraday runners** - 23-25% WR, negative expectancy
❌ **High RR targets** (2R+) - Win rate collapses to 3-6%
❌ **Trend following** - Early impulse ≠ sustained trend
❌ **Breakout retests** - 75% failure rate at 3R

---

## Scripts Available

### Data & Features
- `scripts/ingest_databento_dbn_nq.py` - Data ingestion
- `scripts/build_daily_features_nq.py` - Feature engineering
- `scripts/audit_nq_data_integrity.py` - Data validation

### Backtesting & Optimization
- `scripts/backtest_baseline.py` - Universal baseline (MGC/NQ)
- `scripts/optimize_rr.py` - RR optimization
- `scripts/test_filters.py` - Filter discovery

### Research
- `scripts/research_nq_massive_moves.py` - 3R+ runner research (failed)

---

## How to Run Common Operations

### Load NQ Data
```python
import duckdb
con = duckdb.connect('gold.db')

# Load 1-minute bars
bars = con.execute("""
    SELECT ts_utc, open, high, low, close, volume
    FROM bars_1m_nq
    WHERE DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') = '2025-01-13'
    ORDER BY ts_utc
""").df()

# Load daily features
features = con.execute("""
    SELECT *
    FROM daily_features_v2_nq
    ORDER BY date_local
""").df()

con.close()
```

### Run Baseline Backtest
```bash
python scripts/backtest_baseline.py NQ
```

### Run RR Optimization
```bash
python scripts/optimize_rr.py NQ
```

### Run Filter Tests
```bash
python scripts/test_filters.py NQ
```

---

## Research Guidelines

### Zero-Lookahead Rules (CRITICAL)

**Allowed Features** (known at decision time):
- Pre-session ranges (e.g., `pre_asia_range` known before 09:00 ORB)
- Prior session H/L (e.g., `asia_high` known before 18:00 ORB)
- Rolling indicators (ATR, RSI calculated only up to current time)
- Prior day levels

**FORBIDDEN Features** (lookahead):
- Session type codes (`asia_type_code`) - computed after session ends
- Current session range for same-session ORB
- Future price data

### Conservative Execution

**Required Assumptions**:
1. **Entry**: Next bar after signal (never same bar)
2. **Same-bar conflict**: If both TP and SL hit same bar = LOSS
3. **Slippage**: Test with 0, 1, 2 ticks
4. **No cherry-picking**: Use all signals, not just "clean" ones

### Robustness Tests (MUST PASS 3 of 4)

1. ✓ **Overall positive expectancy** (>0.5R avg or >50% WR at 1R)
2. ✓ **IS/OOS both positive** (70/30 split by date)
3. ✓ **No outlier dependency** (positive without top 1% days)
4. ✓ **Minimum sample size** (>=20 trades)

---

## Next Research Ideas

### 1. Intra-Session Dependencies ⬅️ NEXT
**Question**: Does one session's behavior predict the next?

**Examples**:
- If Asia has strong UP trend, does London continue UP?
- If London is ranging (low volatility), does NY expand?
- Does Asia ORB outcome predict 1800 ORB outcome?

**Approach**: Correlation analysis + conditional probabilities

---

### 2. Session Regime Classification
**Question**: Can we classify "good" vs "bad" trading days?

**Features**: Volatility, range, directional consistency
**Goal**: Filter for high-probability days only

---

### 3. Entry Timing Variants
**Question**: Does waiting for 2nd or 3rd close improve results?

**Test**: Compare 1-close vs 2-close vs 3-close entry confirmations

---

### 4. Multi-ORB Portfolio
**Question**: What's the optimal combination of ORBs to trade daily?

**Test**: Portfolio optimization (Sharpe ratio, max drawdown)

---

### 5. Time-of-Day Momentum
**Question**: Are certain hours better for specific directions?

**Test**: UP/DOWN bias by hour of day

---

## File Locations

### Key Reports
- `outputs/NQ_OPTIMIZATION_COMPLETE.md` - Complete optimization summary
- `outputs/NQ_RR_OPTIMIZATION_REPORT.md` - RR analysis
- `outputs/NQ_MASSIVE_REPORT.md` - 3R+ runner research (failed)
- `outputs/NQ_VS_MGC_COMPARISON.md` - Instrument comparison
- `outputs/COMPLETE_NQ_INTEGRATION_SUMMARY.md` - Full integration summary

### Data Files
- `outputs/NQ_baseline_backtest.csv` - Baseline results
- `outputs/NQ_rr_optimization.csv` - RR test data
- `outputs/NQ_filter_tests.csv` - Filter test data
- `outputs/NQ_MASSIVE_TRADES.csv` - All massive move tests

### Configs
- `configs/market_nq.yaml` - NQ market parameters
- `configs/market_mgc.yaml` - MGC market parameters

---

## Important Context

### Why NQ vs MGC?
- **NQ**: Equity index, US-driven, higher volatility
- **MGC**: Commodity, global 24/5, lower volatility
- **Different optimal times**: NQ (NYSE open), MGC (London open)

### Why 1R Targets?
- NQ mean-reverts after 1R moves
- Win rate collapses at higher targets (64% → 3%)
- Quick profit-taking is optimal

### Why ORB Size Filters?
- Large ORBs signal momentum (0030, 1000)
- Medium ORBs avoid extremes (1800, 1100)
- Small ORBs reduce noise (0900)
- Improvements: 10-118% over baseline

---

## Common Pitfalls to Avoid

❌ **Don't**: Assume 3R+ targets are achievable (they're not)
❌ **Don't**: Use lookahead features (type codes, same-session stats)
❌ **Don't**: Ignore IS/OOS testing (overfitting risk)
❌ **Don't**: Cherry-pick trades (use all signals)

✅ **Do**: Target 1R for NQ
✅ **Do**: Use ORB size filters
✅ **Do**: Test conservative execution
✅ **Do**: Validate with robustness tests

---

## Quick Reference: NQ Constants

```python
SYMBOL = "NQ"
TICK_SIZE = 0.25
TABLE_1M = "bars_1m_nq"
TABLE_5M = "bars_5m_nq"
TABLE_FEATURES = "daily_features_v2_nq"
TZ_LOCAL = "Australia/Brisbane"  # UTC+10
DB_PATH = "gold.db"

# Session start times (local)
ASIA_START = (9, 0)
LONDON_START = (18, 0)
NY_FUTURES_START = (23, 0)
NY_CASH_START = (0, 30)  # next day

# ORB times
ORBS = ['0900', '1000', '1100', '1800', '2300', '0030']

# Proven optimal parameters
OPTIMAL_RR = 1.0
OPTIMAL_SL_MODE = 'FULL'

# Filter thresholds (in points)
FILTER_0030_MIN_SIZE = 37.0  # 149 ticks
FILTER_1800_MIN_SIZE = 10.0
FILTER_1800_MAX_SIZE = 30.0
FILTER_1100_MIN_SIZE = 6.25
FILTER_1100_MAX_SIZE = 18.75
FILTER_1000_MIN_SIZE = 17.5
FILTER_0900_MAX_SIZE = 16.5
```

---

## Status Summary

**Completed**:
✅ Data pipeline
✅ Baseline backtests
✅ RR optimization (result: 1.0 optimal)
✅ Filter discovery (result: size filters work)
✅ Dashboard integration
✅ Massive moves research (result: failed, not viable)

**Next**: Intra-session dependencies research

**Overall**: NQ framework fully validated. 1R ORB strategy with size filters is the proven edge (~0.33R/day expected).

---

**Last Updated**: 2026-01-13
**Status**: Ready for next research phase
