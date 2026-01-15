# Database Schema - Source of Truth

**Last Updated:** 2026-01-15

## VERIFIED TABLES (Source of Truth)

These tables contain VERIFIED backtest results that match config.py:

### 1. `daily_features_v2_half` (MGC HALF SL mode)
- **Purpose:** Daily ORB features with HALF stop loss mode
- **Used by:** `v_orb_trades_half` view
- **Verified:** YES - matches config.py performance numbers
- **Slippage:** NO (perfect fills)
- **Columns:** date_local, orb_XXXX_high/low/size/break_dir/outcome/r_multiple/mae/mfe/stop_price/risk_ticks
- **ORB Times:** 0900, 1000, 1100, 1800, 2300, 0030

### 2. `v_orb_trades_half` (VIEW)
- **Purpose:** Clean view of all ORB trades from daily_features_v2_half
- **Source:** Reads from daily_features_v2_half
- **Usage:** Query this for MGC backtest results
- **Example:**
  ```sql
  SELECT orb_time, COUNT(*) as trades,
         AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
         AVG(r_multiple) as avg_r
  FROM v_orb_trades_half
  WHERE instrument='MGC' AND outcome IN ('WIN','LOSS')
  GROUP BY orb_time;
  ```

### 3. `daily_features_v2_nq` (NQ instrument)
- **Purpose:** Daily ORB features for NQ (Micro Nasdaq)
- **Verified:** YES
- **Same structure as daily_features_v2_half**

### 4. `daily_features_v2_mpl` (MPL instrument)
- **Purpose:** Daily ORB features for MPL (Micro Platinum)
- **Verified:** YES (2026-01-15)
- **Same structure as daily_features_v2_half**

## ARCHIVED TABLES (Do Not Use)

These tables were from experimental parameter testing and have been archived:

- `_archive_orb_trades_1m_exec` - 1-minute execution tests (outdated)
- `_archive_orb_trades_1m_exec_nofilters` - 1-minute without filters
- `_archive_orb_trades_5m_exec` - 5-minute execution tests (WRONG NUMBERS)
- `_archive_orb_trades_5m_exec_nofilters` - 5-minute without filters
- `_archive_orb_trades_5m_exec_nomax` - 5-minute without max filters
- `_archive_orb_trades_5m_exec_orbr` - 5-minute ORB range tests

**DO NOT QUERY THESE TABLES** - they contain outdated methodology and incorrect parameters.

## RAW DATA TABLES (Do Not Modify)

### Bars (1-minute and 5-minute)
- `bars_1m` - MGC 1-minute bars
- `bars_1m_nq` - NQ 1-minute bars
- `bars_1m_mpl` - MPL 1-minute bars
- `bars_5m` - MGC 5-minute bars (aggregated from bars_1m)
- `bars_5m_nq` - NQ 5-minute bars
- `bars_5m_mpl` - MPL 5-minute bars

## Config.py Performance Numbers

The numbers in `config.py` come from `daily_features_v2_half`:

```python
MGC_ORB_CONFIGS = {
    "0900": {"rr": 1.0, "sl_mode": "FULL", "tier": "DAY"},  # +0.431R
    "1000": {"rr": 3.0, "sl_mode": "FULL", "tier": "DAY"},  # +0.342R
    "1100": {"rr": 1.0, "sl_mode": "FULL", "tier": "DAY"},  # +0.449R
    "1800": {"rr": 1.0, "sl_mode": "HALF", "tier": "DAY"},  # +0.425R
    "2300": {"rr": 1.0, "sl_mode": "HALF", "tier": "NIGHT"}, # +0.387R ✓ VERIFIED
    "0030": {"rr": 1.0, "sl_mode": "HALF", "tier": "NIGHT"}, # +0.231R
}
```

**VERIFIED EXAMPLE (MGC 2300 ORB):**
- Source: `v_orb_trades_half`
- Win Rate: 69.3%
- Avg R: +0.387R (NO slippage)
- With 1 tick slippage: +0.261R
- With 2 tick slippage: +0.134R

## Important Notes

1. **No Slippage in Backtest:** The daily_features tables assume PERFECT fills (no slippage)
2. **Real Trading:** Expect 1-2 tick slippage on entry and stop
3. **Always Query v_orb_trades_half:** Don't query daily_features tables directly
4. **RR Values:** Some configs use RR > 1.0 (e.g., 1000 ORB uses RR=3.0)
5. **SL Modes:** HALF = stop at ORB midpoint, FULL = stop at opposite ORB edge

## How to Add Real-World Slippage

```sql
-- Example: MGC 2300 with 1 tick slippage
SELECT
    AVG(CASE
        WHEN outcome='WIN' THEN 1.0 - (0.2 / 0.1) / risk_ticks
        WHEN outcome='LOSS' THEN -1.0 - (0.2 / 0.1) / risk_ticks
    END) as avg_r_with_slippage
FROM v_orb_trades_half
WHERE orb_time='2300'
  AND instrument='MGC'
  AND outcome IN ('WIN','LOSS')
  AND risk_ticks > 0;
```

Where:
- 0.2 = 0.1 entry slip + 0.1 stop slip (1 tick each)
- 0.1 = MGC tick size
- risk_ticks = stop distance in ticks

---

**CRITICAL:** Only use `v_orb_trades_half` and related daily_features_v2 tables. All orb_trades_*_exec tables are ARCHIVED and outdated.
