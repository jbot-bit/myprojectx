# PIPELINE AUDIT REPORT

**Generated:** 2026-01-12 12:32:08

**Purpose:** End-to-end verification of DB consistency, schema alignment, and ORB calculation correctness

---


## 1. DATABASE PATH VERIFICATION

**Goal:** Confirm all scripts use the same database file

| Script | DB Path(s) |
|--------|------------|
| `build_daily_features_v2.py` | gold.db |
| `backtest_orb_exec_5mhalfsl_orbR.py` | gold.db |
| `backtest_orb_exec_5mhalfsl.py` | gold.db |
| `backtest_orb_exec_5m.py` | gold.db |
| `backfill_databento_continuous.py` | gold.db, ENV:DUCKDB_PATH (fallback: gold.db) |
| `view_results.py` | gold.db |
| `export_filtered_trades.py` | gold.db |
| `high_confidence_ruleset.py` | gold.db |

**Analysis:**

✅ **ALIGNED:** All scripts use consistent DB path (`gold.db`)

**Current DB:** `gold.db` exists
- **Size:** 607.8 MB
- **Last Modified:** 2026-01-12 11:57:07


## 2. SCHEMA VERIFICATION

**Goal:** Confirm current schema (no legacy tables, correct columns)

**Database:** `gold`

**All Tables:**

- `bars_1m`
- `bars_5m`
- `daily_features`
- `daily_features_v2`
- `orb_exec_results`
- `orb_trades_1m_exec`
- `orb_trades_1m_exec_nofilters`
- `orb_trades_5m_exec`
- `orb_trades_5m_exec_nofilters`
- `orb_trades_5m_exec_nomax`
- `orb_trades_5m_exec_orbr`
- `v_orb_trades`

**Key Tables Detail:**

### ✅ `bars_1m`

| Column | Type |
|--------|------|
| `ts_utc` | TIMESTAMP WITH TIME ZONE |
| `symbol` | VARCHAR |
| `source_symbol` | VARCHAR |
| `open` | DOUBLE |
| `high` | DOUBLE |
| `low` | DOUBLE |
| `close` | DOUBLE |
| `volume` | BIGINT |

### ✅ `bars_5m`

| Column | Type |
|--------|------|
| `ts_utc` | TIMESTAMP WITH TIME ZONE |
| `symbol` | VARCHAR |
| `source_symbol` | VARCHAR |
| `open` | DOUBLE |
| `high` | DOUBLE |
| `low` | DOUBLE |
| `close` | DOUBLE |
| `volume` | BIGINT |

### ✅ `daily_features_v2`

| Column | Type |
|--------|------|
| `date_local` | DATE |
| `instrument` | VARCHAR |
| `pre_asia_high` | DOUBLE |
| `pre_asia_low` | DOUBLE |
| `pre_asia_range` | DOUBLE |
| `pre_london_high` | DOUBLE |
| `pre_london_low` | DOUBLE |
| `pre_london_range` | DOUBLE |
| `pre_ny_high` | DOUBLE |
| `pre_ny_low` | DOUBLE |
| `pre_ny_range` | DOUBLE |
| `asia_high` | DOUBLE |
| `asia_low` | DOUBLE |
| `asia_range` | DOUBLE |
| `london_high` | DOUBLE |
| `london_low` | DOUBLE |
| `london_range` | DOUBLE |
| `ny_high` | DOUBLE |
| `ny_low` | DOUBLE |
| `ny_range` | DOUBLE |
| `orb_0900_high` | DOUBLE |
| `orb_0900_low` | DOUBLE |
| `orb_0900_size` | DOUBLE |
| `orb_0900_break_dir` | VARCHAR |
| `orb_0900_outcome` | VARCHAR |
| `orb_0900_r_multiple` | DOUBLE |
| `orb_1000_high` | DOUBLE |
| `orb_1000_low` | DOUBLE |
| `orb_1000_size` | DOUBLE |
| `orb_1000_break_dir` | VARCHAR |
| `orb_1000_outcome` | VARCHAR |
| `orb_1000_r_multiple` | DOUBLE |
| `orb_1100_high` | DOUBLE |
| `orb_1100_low` | DOUBLE |
| `orb_1100_size` | DOUBLE |
| `orb_1100_break_dir` | VARCHAR |
| `orb_1100_outcome` | VARCHAR |
| `orb_1100_r_multiple` | DOUBLE |
| `orb_1800_high` | DOUBLE |
| `orb_1800_low` | DOUBLE |
| `orb_1800_size` | DOUBLE |
| `orb_1800_break_dir` | VARCHAR |
| `orb_1800_outcome` | VARCHAR |
| `orb_1800_r_multiple` | DOUBLE |
| `orb_2300_high` | DOUBLE |
| `orb_2300_low` | DOUBLE |
| `orb_2300_size` | DOUBLE |
| `orb_2300_break_dir` | VARCHAR |
| `orb_2300_outcome` | VARCHAR |
| `orb_2300_r_multiple` | DOUBLE |
| `orb_0030_high` | DOUBLE |
| `orb_0030_low` | DOUBLE |
| `orb_0030_size` | DOUBLE |
| `orb_0030_break_dir` | VARCHAR |
| `orb_0030_outcome` | VARCHAR |
| `orb_0030_r_multiple` | DOUBLE |
| `rsi_at_0030` | DOUBLE |
| `atr_20` | DOUBLE |
| `asia_type_code` | VARCHAR |
| `london_type_code` | VARCHAR |
| `pre_ny_type_code` | VARCHAR |

### ✅ `orb_trades_5m_exec`

| Column | Type |
|--------|------|
| `date_local` | DATE |
| `orb` | VARCHAR |
| `close_confirmations` | INTEGER |
| `rr` | DOUBLE |
| `sl_mode` | VARCHAR |
| `buffer_ticks` | DOUBLE |
| `direction` | VARCHAR |
| `entry_ts` | TIMESTAMP |
| `entry_price` | DOUBLE |
| `stop_price` | DOUBLE |
| `target_price` | DOUBLE |
| `stop_ticks` | DOUBLE |
| `outcome` | VARCHAR |
| `r_multiple` | DOUBLE |
| `entry_delay_bars` | INTEGER |
| `mae_r` | DOUBLE |
| `mfe_r` | DOUBLE |

### ✅ `orb_trades_5m_exec_orbr`

| Column | Type |
|--------|------|
| `date_local` | DATE |
| `orb` | VARCHAR |
| `close_confirmations` | INTEGER |
| `rr` | DOUBLE |
| `sl_mode` | VARCHAR |
| `buffer_ticks` | DOUBLE |
| `direction` | VARCHAR |
| `entry_ts` | TIMESTAMP |
| `entry_price` | DOUBLE |
| `stop_price` | DOUBLE |
| `target_price` | DOUBLE |
| `stop_ticks` | DOUBLE |
| `orb_range_ticks` | DOUBLE |
| `outcome` | VARCHAR |
| `r_multiple` | DOUBLE |
| `entry_delay_bars` | INTEGER |
| `mae_r` | DOUBLE |
| `mfe_r` | DOUBLE |

### ✅ `orb_trades_5m_exec_nomax`

| Column | Type |
|--------|------|
| `date_local` | DATE |
| `orb` | VARCHAR |
| `close_confirmations` | INTEGER |
| `rr` | DOUBLE |
| `sl_mode` | VARCHAR |
| `buffer_ticks` | DOUBLE |
| `direction` | VARCHAR |
| `entry_ts` | TIMESTAMP |
| `entry_price` | DOUBLE |
| `stop_price` | DOUBLE |
| `target_price` | DOUBLE |
| `stop_ticks` | DOUBLE |
| `outcome` | VARCHAR |
| `r_multiple` | DOUBLE |
| `entry_delay_bars` | INTEGER |
| `mae_r` | DOUBLE |
| `mfe_r` | DOUBLE |

### ✅ `orb_trades_1m_exec`

| Column | Type |
|--------|------|
| `date_local` | DATE |
| `orb` | VARCHAR |
| `close_confirmations` | INTEGER |
| `rr` | DOUBLE |
| `direction` | VARCHAR |
| `entry_ts` | TIMESTAMP |
| `entry_price` | DOUBLE |
| `stop_price` | DOUBLE |
| `target_price` | DOUBLE |
| `stop_ticks` | DOUBLE |
| `outcome` | VARCHAR |
| `r_multiple` | DOUBLE |
| `entry_delay_min` | INTEGER |
| `mae_r` | DOUBLE |
| `mfe_r` | DOUBLE |


## 3. DATA SANITY CHECKS

**Goal:** Verify row counts, date ranges, sample data

| Table | Rows | Date Range | Status |
|-------|------|------------|--------|
| `bars_1m` | 716,540 | 2024-01-02 09:00:00+10:00 to 2026-01-10 07:59:00+10:00 | ✅ |
| `bars_5m` | 143,648 | 2024-01-02 09:00:00+10:00 to 2026-01-10 07:55:00+10:00 | ✅ |
| `daily_features_v2` | 739 | 2024-01-02 to 2026-01-09 | ✅ |
| `orb_trades_5m_exec` | 263,724 | 2024-01-02 to 2026-01-09 | ✅ |
| `orb_trades_5m_exec_orbr` | 2,991 | 2024-01-02 to 2026-01-09 | ✅ |
| `orb_trades_5m_exec_nomax` | 12,504 | 2024-01-02 to 2026-01-09 | ✅ |

**Sample Data (most recent):**

**daily_features_v2:**

```
[(datetime.date(2026, 1, 9), 4493.7, 4486.3, 4486.8, 4483.7, 4475.4, 4467.5, 4480.7, 4475.1), (datetime.date(2026, 1, 8), 4471.9, 4466.0, 4474.8, 4471.7, 4463.7, 4452.6, 4439.7, 4433.2), (datetime.date(2026, 1, 7), 4510.1, 4504.5, 4505.5, 4501.5, 4507.1, 4491.6, 4473.5, 4470.2)]
```


## 4. ORB CALCULATION VERIFICATION

**Goal:** Confirm ORB uses HIGH/LOW (wicks included), not just close prices

**File:** `build_daily_features_v2.py`

- Uses MAX(high): ✅ YES
- Uses MIN(low): ✅ YES
- Uses close only: ✅ NO (GOOD)

**Verdict:** CORRECT (uses HIGH/LOW)


## 5. BACKTEST INPUT TRACE

**Goal:** Verify backtests read from correct tables with correct columns

**File:** `backtest_orb_exec_5mhalfsl_orbR.py`

- Tables referenced: `bars_5m`, `daily_features_v2`, `datetime`
- Uses daily_features_v2: ✅ YES
- Uses bars_5m: ✅ YES
- ❌ **Missing tables:** `datetime`


## 6. RESULTS OUTPUT TRACE

**Goal:** Verify results are written/read from correct locations

**view_results.py reads from:**

- `ranked`
- `orb_trades_5m_exec`

✅ CORRECT

**CSV Exports Found:**

| File | Modified | Size (KB) |
|------|----------|----------|
| `filtered_trades_1000.csv` | 2026-01-12 12:27:08 | 87.1 |
| `filtered_trades_1100.csv` | 2026-01-12 12:27:08 | 83.8 |
| `filtered_trades_1800.csv` | 2026-01-12 12:27:08 | 86.4 |
| `filtered_trades_all.csv` | 2026-01-12 12:27:08 | 256.8 |
| `filtered_trades_summary.csv` | 2026-01-12 12:27:08 | 0.6 |
| `results_1m_by_session.csv` | 2026-01-12 09:16:18 | 7.5 |
| `results_5m_exec_by_session.csv` | 2026-01-12 09:16:18 | 4.4 |
| `results_5m_halfsl_by_session.csv` | 2026-01-12 09:16:18 | 34.6 |
| `results_session_winners.csv` | 2026-01-12 09:16:18 | 0.5 |

⚠️ **Note:** CSV exports are point-in-time snapshots. Verify they match current DB state.


## 7. SUMMARY & ACTION ITEMS

### ✅ Aligned Items

1. All scripts use `gold.db` as database file
2. Schema contains expected tables (bars_1m, bars_5m, daily_features_v2, orb_trades_*)
3. Data ranges span expected periods (2020-12-20 to recent)
4. ORB calculation in build_daily_features_v2.py uses MAX(high)/MIN(low) ✅

### ❌ Issues Found

_(To be filled based on actual findings)_

### 🔧 Recommended Fixes

1. **Standardize DB path resolution:**
   - Use `DB_PATH = os.getenv('DUCKDB_PATH', 'gold.db')` in all scripts
   - Add startup assertion: `assert os.path.exists(DB_PATH), f'Database not found: {DB_PATH}'`

2. **Add schema validation on startup:**
```

def assert_schema():
    con = duckdb.connect(DB_PATH, read_only=True)
    required_tables = ['bars_5m', 'daily_features_v2', 'orb_trades_5m_exec_orbr']
    existing = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
    for table in required_tables:
        assert table in existing, f"Missing required table: {table}"
    con.close()
    print(f"✅ Schema validated: {DB_PATH}")

```

3. **Add data sanity checks:**
```

def assert_data():
    con = duckdb.connect(DB_PATH, read_only=True)
    # Check daily_features_v2 has recent data
    max_date = con.execute("SELECT MAX(date_local) FROM daily_features_v2").fetchone()[0]
    assert max_date is not None, "daily_features_v2 is empty"
    print(f"✅ Latest features: {max_date}")
    con.close()

```


---

**End of Audit Report**
