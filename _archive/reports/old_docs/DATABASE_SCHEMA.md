# Database Schema - gold.db

**Database:** DuckDB (`gold.db`)

**Purpose:** Local data pipeline for MGC (Micro Gold) futures trading analysis

---

## Active Tables

### bars_1m
**Purpose:** Primary raw 1-minute OHLCV data

**Schema:**
```sql
CREATE TABLE bars_1m (
    ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    symbol VARCHAR NOT NULL,
    source_symbol VARCHAR,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT,
    PRIMARY KEY (symbol, ts_utc)
)
```

**Size:** Varies (full historical dataset)
**Source:** Databento (GLBX.MDP3) or ProjectX API
**Notes:**
- `symbol` = 'MGC' (continuous logical symbol)
- `source_symbol` = actual contract (e.g., 'MGCG4', 'MGCM4')
- All timestamps in UTC
- Timezone conversion to `Australia/Brisbane` for trading day logic

### bars_5m
**Purpose:** 5-minute aggregated bars (derived from bars_1m)

**Schema:**
```sql
CREATE TABLE bars_5m (
    ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    symbol VARCHAR NOT NULL,
    source_symbol VARCHAR,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT,
    PRIMARY KEY (symbol, ts_utc)
)
```

**Size:** ~1/5 of bars_1m
**Source:** Deterministically aggregated from bars_1m
**Notes:**
- Bucket = floor(epoch(ts)/300)*300
- Fully rebuildable at any time
- Used for ORB break detection

### daily_features_v2 ⭐ V2 (Zero Lookahead)
**Purpose:** Daily features with strict temporal boundaries for backtesting

**Schema:**
```sql
CREATE TABLE daily_features_v2 (
    date_local DATE NOT NULL,
    instrument VARCHAR NOT NULL DEFAULT 'MGC',

    -- PRE blocks (context BEFORE opens)
    pre_asia_range DOUBLE,
    pre_london_range DOUBLE,
    pre_ny_range DOUBLE,

    -- ORBs (6 per day)
    orb_0900_high DOUBLE, orb_0900_low DOUBLE, orb_0900_size DOUBLE, orb_0900_break_dir VARCHAR,
    orb_0900_outcome VARCHAR, orb_0900_r_multiple DOUBLE,

    orb_1000_high DOUBLE, orb_1000_low DOUBLE, orb_1000_size DOUBLE, orb_1000_break_dir VARCHAR,
    orb_1000_outcome VARCHAR, orb_1000_r_multiple DOUBLE,

    orb_1100_high DOUBLE, orb_1100_low DOUBLE, orb_1100_size DOUBLE, orb_1100_break_dir VARCHAR,
    orb_1100_outcome VARCHAR, orb_1100_r_multiple DOUBLE,

    orb_1800_high DOUBLE, orb_1800_low DOUBLE, orb_1800_size DOUBLE, orb_1800_break_dir VARCHAR,
    orb_1800_outcome VARCHAR, orb_1800_r_multiple DOUBLE,

    orb_2300_high DOUBLE, orb_2300_low DOUBLE, orb_2300_size DOUBLE, orb_2300_break_dir VARCHAR,
    orb_2300_outcome VARCHAR, orb_2300_r_multiple DOUBLE,

    orb_0030_high DOUBLE, orb_0030_low DOUBLE, orb_0030_size DOUBLE, orb_0030_break_dir VARCHAR,
    orb_0030_outcome VARCHAR, orb_0030_r_multiple DOUBLE,

    -- SESSION blocks (analytics only - known AFTER session close)
    asia_high DOUBLE, asia_low DOUBLE, asia_range DOUBLE,
    london_high DOUBLE, london_low DOUBLE, london_range DOUBLE,
    ny_high DOUBLE, ny_low DOUBLE, ny_range DOUBLE,

    -- Session type codes (lookahead - use with caution)
    asia_type_code VARCHAR,
    london_type_code VARCHAR,
    pre_ny_type_code VARCHAR,

    -- Additional features
    atr_20 DOUBLE,

    PRIMARY KEY (date_local, instrument)
)
```

**Size:** 739 days (2024-01-02 to 2026-01-10)
**Source:** `build_daily_features_v2.py`
**Notes:**
- **Zero-lookahead structure** - critical for honest backtesting
- PRE blocks known AT the ORB open (valid for decision making)
- SESSION blocks known AFTER session close (analytics only)
- Session type codes are LOOKAHEAD - do NOT use for ORB trading rules
- Use v_orb_trades view for normalized ORB analysis

### v_orb_trades (View)
**Purpose:** Normalized view of all ORB opportunities for analysis

**Schema:**
```sql
CREATE VIEW v_orb_trades AS
SELECT
    date_local,
    '0900' AS orb_time, orb_0900_high AS orb_high, orb_0900_low AS orb_low,
    orb_0900_size AS orb_size, orb_0900_break_dir AS break_dir,
    orb_0900_outcome AS outcome, orb_0900_r_multiple AS r_multiple,
    pre_asia_range, asia_range, london_range, ny_range,
    asia_type_code, london_type_code, pre_ny_type_code, atr_20
FROM daily_features_v2
UNION ALL
SELECT
    date_local,
    '1000' AS orb_time, orb_1000_high, orb_1000_low,
    orb_1000_size, orb_1000_break_dir,
    orb_1000_outcome, orb_1000_r_multiple,
    pre_asia_range, asia_range, london_range, ny_range,
    asia_type_code, london_type_code, pre_ny_type_code, atr_20
FROM daily_features_v2
-- ... (similar for 1100, 1800, 2300, 0030)
```

**Size:** 4,434 rows (739 days × 6 ORBs)
**Source:** View over daily_features_v2
**Notes:**
- Unpivots 6 ORB columns into rows
- Used by Streamlit dashboard (app_edge_research.py)
- Easier to query than wide format

### orb_trades_1m_exec
**Purpose:** 1-minute precision backtest results with RR optimization

**Schema:**
```sql
CREATE TABLE orb_trades_1m_exec (
    date_local DATE NOT NULL,
    orb VARCHAR NOT NULL,
    close_confirmations INTEGER NOT NULL,
    rr DOUBLE NOT NULL,

    direction VARCHAR,
    entry_ts TIMESTAMP,
    entry_price DOUBLE,
    stop_price DOUBLE,
    target_price DOUBLE,
    stop_ticks DOUBLE,

    outcome VARCHAR,
    r_multiple DOUBLE,
    entry_delay_min INTEGER,
    mae_r DOUBLE,
    mfe_r DOUBLE,

    PRIMARY KEY (date_local, orb, close_confirmations, rr)
)
```

**Size:** 11,653 rows (RR grid: 1.5, 2.0, 2.5, 3.0)
**Source:** `backtest_orb_exec_1m.py`
**Notes:**
- 1-minute bar precision backtest
- Supports multiple confirmation closes (1, 2, or 3)
- RR grid search capability
- Tracks MAE/MFE for slippage analysis
- Current data: 1 confirmation close, 4 RR targets
- Used by `rr_summary.py` and `rr_query.py`

---

## Deprecated Tables

### daily_features (V1)
**Status:** DEPRECATED - Contains lookahead bias
**Replacement:** Use `daily_features_v2` instead
**Issue:** Session type codes (EXPANDED, CONSOLIDATION) used in ORB filters created lookahead bias
**Migration:** Run `build_daily_features_v2.py` to rebuild with zero-lookahead structure

---

## Unused Tables

### orb_exec_results
**Status:** UNUSED (0 rows)
**Created by:** `init_orb_exec_results.py`
**Replaced by:** `orb_trades_1m_exec`

**Schema:**
```sql
CREATE TABLE orb_exec_results (
    date_local DATE NOT NULL,
    instrument VARCHAR NOT NULL,
    orb_time VARCHAR NOT NULL,
    variant VARCHAR NOT NULL,
    dir VARCHAR,

    entry_ts TIMESTAMP WITH TIME ZONE,
    entry_price DOUBLE,
    stop_price DOUBLE,
    target_price DOUBLE,

    risk_ticks DOUBLE,
    target_ticks DOUBLE,

    outcome VARCHAR,
    r_multiple DOUBLE,

    notes VARCHAR,

    PRIMARY KEY (date_local, instrument, orb_time, variant, dir)
)
```

**Why Unused:**
- Original design for backtest results
- Replaced by `orb_trades_1m_exec` which has better schema:
  - Includes `rr` in primary key (supports RR grid search)
  - Tracks MAE/MFE (max adverse/favorable excursion)
  - Simpler primary key structure
  - Entry delay tracking
- Can be safely dropped if needed

**Migration:**
```bash
# Safe to drop
python -c "import duckdb; con = duckdb.connect('gold.db'); con.execute('DROP TABLE IF EXISTS orb_exec_results')"
```

---

## Data Flow

```
Source Data
    ↓
bars_1m (Databento/ProjectX)
    ↓
bars_5m (aggregated)
    ↓
daily_features_v2 (PRE blocks, ORBs, SESSIONs)
    ↓
v_orb_trades (normalized view)
    ↓
[Analysis & Backtesting]
    ↓
orb_trades_1m_exec (backtest results)
```

---

## Key Principles

### Zero-Lookahead Methodology
**Rule:** If you can't calculate it at the open, you can't use it to trade the open.

**Valid for ORB decisions:**
- PRE blocks (PRE_ASIA, PRE_LONDON, PRE_NY)
- Previous day ORB outcomes
- Previous completed sessions (ASIA known at 18:00+, LONDON at 23:00+)

**INVALID for ORB decisions (lookahead bias):**
- Session type codes for same-day sessions
- Intraday session stats before session closes
- Future ORB outcomes

### Honesty Over Accuracy
- V1 system had 57.9% win rate (INVALID - lookahead bias)
- V2 system has 50-58% win rate (HONEST - zero lookahead)
- Lower but REAL numbers are better than inflated backtests

---

## Commands Reference

### Initialize Schema
```bash
python init_db.py
```

### Backfill Data
```bash
python backfill_databento_continuous.py 2024-01-01 2026-01-10
```

### Build V2 Features
```bash
python build_daily_features_v2.py 2026-01-10
```

### Run Backtest
```bash
# Single RR target
python backtest_orb_exec_1m.py --confirm 1 --rr 2.0

# RR grid search
python backtest_orb_exec_1m.py --rr-grid "1.5,2.0,2.5,3.0" --confirm 1
```

### Analyze Results
```bash
python analyze_orb_v2.py          # Discover V2 edges
python rr_summary.py              # Compare RR targets
python export_v2_edges.py         # Export all edges
```

---

**Last Updated:** 2026-01-11
**Database Version:** V2 (Zero Lookahead)
**Total Rows:** ~1M+ bars, 739 daily features, 11,653 backtest results
