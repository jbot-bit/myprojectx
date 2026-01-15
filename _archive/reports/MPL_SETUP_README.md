# MPL (Micro Platinum) Integration Guide

Complete setup for ingesting and backtesting Micro Platinum futures (MPL) in the myprojectx trading system.

## Overview

MPL is now fully integrated into the myprojectx framework with the same architecture as MGC and NQ:
- **Symbol**: MPL (continuous logical symbol)
- **Database tables**: `bars_1m_mpl`, `bars_5m_mpl`, `daily_features_v2_mpl`
- **Contract months**: F, J, N, V (Jan, Apr, Jul, Oct)
- **Tick size**: 0.1 ($0.50 per tick, $5 per point)
- **Exchange**: NYMEX

## Files Created

### 1. Configuration
- `configs/market_mpl.yaml` - Market parameters and baseline structure

### 2. Data Ingestion
- `scripts/ingest_databento_dbn_mpl.py` - Ingest DBN files into DuckDB
- `backfill_databento_continuous_mpl.py` - Backfill historical data via Databento API

### 3. Feature Building
- `scripts/build_daily_features_mpl.py` - Calculate daily ORB features (V2)

### 4. Utilities
- `wipe_mpl.py` - Wipe all MPL data from database

### 5. Trading App
- Updated `trading_app/config.py` with MPL ORB configs (placeholders awaiting backtest)

## Quick Start

### Step 1: Backfill Historical Data

Using Databento API (recommended):
```bash
python backfill_databento_continuous_mpl.py 2024-01-01 2026-01-10
```

This will:
1. Download 1-minute OHLCV bars from Databento (MPL.FUT parent symbol)
2. Select front month contract (highest volume, excludes spreads)
3. Stitch into continuous series stored as 'MPL'
4. Build 5-minute bars from 1-minute bars
5. Calculate daily features (ORBs, session stats, ATR)

### Step 2: Verify Data

Check database contents:
```bash
# Check bar counts
python -c "import duckdb; con = duckdb.connect('gold.db'); print('1m bars:', con.execute('SELECT COUNT(*) FROM bars_1m_mpl').fetchone()[0]); print('5m bars:', con.execute('SELECT COUNT(*) FROM bars_5m_mpl').fetchone()[0]); print('Features:', con.execute('SELECT COUNT(*) FROM daily_features_v2_mpl').fetchone()[0])"
```

### Step 3: Run Baseline Backtest

Create a baseline backtest script (similar to MGC/NQ):
```bash
# Example - you'll need to create this
python analyze_mpl_baseline.py
```

### Step 4: Update Trading App Config

After backtest, update `trading_app/config.py` with optimal parameters:
- RR ratios per ORB
- SL mode (FULL vs HALF)
- ORB size filters
- Performance metrics

## Database Schema

### bars_1m_mpl
```sql
CREATE TABLE bars_1m_mpl (
  ts_utc        TIMESTAMPTZ NOT NULL,
  symbol        TEXT NOT NULL,          -- 'MPL'
  source_symbol TEXT,                   -- 'MPLF5', 'MPLJ5', etc
  open          DOUBLE NOT NULL,
  high          DOUBLE NOT NULL,
  low           DOUBLE NOT NULL,
  close         DOUBLE NOT NULL,
  volume        BIGINT NOT NULL,
  PRIMARY KEY (symbol, ts_utc)
);
```

### bars_5m_mpl
Same structure as bars_1m_mpl, aggregated to 5-minute buckets.

### daily_features_v2_mpl
One row per trading day with:
- Session high/low (Asia, London, NY)
- Pre-move travel metrics
- ATR(20)
- All 6 ORBs: 0900, 1000, 1100, 1800, 2300, 0030
  - Each ORB has: high, low, size, break_dir, outcome, r_multiple, mae, mfe

## Trading Day Definition

**CRITICAL**: Trading day = 09:00 local → next 09:00 local (Australia/Brisbane, UTC+10)

This ensures:
- ORBs are evaluated in correct session context
- No lookahead bias
- Consistent with MGC/NQ framework

## Alternative: Ingest from Local DBN Files

If you have pre-downloaded DBN files:
```bash
python scripts/ingest_databento_dbn_mpl.py /path/to/mpl_dbn_folder
```

DBN folder should contain:
- `*.dbn` or `*.dbn.zst` files
- `symbology.json` (optional, for contract mapping)

## Wipe and Rebuild

If you need to start over:
```bash
# Wipe all MPL data
python wipe_mpl.py

# Backfill again
python backfill_databento_continuous_mpl.py 2024-01-01 2026-01-10
```

## Expected Patterns

Platinum is a **hybrid metal**:
- **Precious metal**: Jewelry, investment (like gold)
- **Industrial metal**: Automotive catalysts, electronics (like copper)

Expected behavior:
- May correlate with gold (MGC) during risk-off periods
- May correlate with industrial metals during economic growth
- Potential London/Asian session strength (global commodity)
- May differ from NQ (equity index)

## Next Steps

1. **Backfill data**: Run `backfill_databento_continuous_mpl.py` for 2+ years
2. **Baseline backtest**: Create `analyze_mpl_baseline.py` (copy from MGC/NQ)
3. **Optimize parameters**: Test different RR ratios, SL modes, filters
4. **Update config**: Add verified parameters to `trading_app/config.py`
5. **Live integration**: Add MPL to trading dashboard UI

## Notes

- **Zero lookahead enforcement**: All features computable at entry time
- **Contract rolls**: Automatically handled by front-month selection
- **Session windows**: Match MGC/NQ for direct comparison
- **Tick size**: 0.1 (same as MGC, different from NQ's 0.25)
- **Databento dataset**: GLBX.MDP3 (CME Globex)

## Troubleshooting

**No data returned:**
- Check Databento availability dates for MPL
- Verify API key is valid
- Try smaller date ranges

**Missing features:**
- Ensure bars_1m_mpl has data for the date
- Check session windows cover 24-hour trading day
- Verify trading day definition (09:00→09:00 local)

**Contract selection issues:**
- MPL contracts: MPLF (Jan), MPLJ (Apr), MPLN (Jul), MPLV (Oct)
- Script filters spreads (contain '-')
- Selects highest volume outright contract

## Reference

- MGC baseline: `configs/market_mgc.yaml`
- NQ baseline: `configs/market_nq.yaml`
- MPL config: `configs/market_mpl.yaml`
- Feature builder V2: `build_daily_features_v2.py` (base class)
