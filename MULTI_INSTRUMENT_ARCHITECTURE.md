# Multi-Instrument Database Architecture

**Date**: 2026-01-18
**Status**: Production Ready
**Approach**: Separate Tables Per Instrument

---

## Architecture Overview

Instead of consolidating all instruments into unified tables, we use **separate tables per instrument**. This is the cleanest and simplest approach.

### Benefits:
- **Simple**: No complex consolidation logic
- **Clean**: Easy to query per instrument
- **Safe**: No schema confusion or type mismatches
- **Scalable**: Can add ES, RTY, etc. as new tables
- **Debuggable**: Each instrument is isolated
- **Performant**: Smaller tables = faster queries

---

## Database Schema

### Location
`gold.db` (local database)

### Tables by Instrument

#### MGC (Micro Gold)
```
bars_1m              720,227 rows
bars_5m              144,386 rows
daily_features_v2    740 rows
validated_setups     6 rows (MGC-specific strategies)
```

#### MPL (Micro Platinum)
```
bars_1m_mpl          327,127 rows
bars_5m_mpl          70,640 rows
daily_features_v2_mpl 730 rows
validated_setups     6 rows (MPL-specific strategies)
```

#### NQ (Nasdaq E-mini)
```
bars_1m_nq           350,499 rows
bars_5m_nq           105,508 rows
daily_features_v2_nq 310 rows
validated_setups     5 rows (NQ-specific strategies)
```

#### Shared
```
validated_setups     19 rows total (all instruments)
```

---

## Table Naming Convention

### Pattern:
```
{table_name}         <- MGC (default, no suffix)
{table_name}_mpl     <- MPL
{table_name}_nq      <- NQ
{table_name}_es      <- ES (future)
{table_name}_rty     <- RTY (future)
```

### Examples:
- `bars_1m` = MGC 1-minute bars
- `bars_1m_mpl` = MPL 1-minute bars
- `bars_1m_nq` = NQ 1-minute bars
- `daily_features_v2` = MGC daily features
- `daily_features_v2_mpl` = MPL daily features

---

## Schema Structure

### bars_1m (and bars_1m_mpl, bars_1m_nq)
```sql
CREATE TABLE bars_1m (
    ts_utc TIMESTAMPTZ PRIMARY KEY,
    symbol VARCHAR,              -- e.g., 'MGC', 'MGCG6', etc.
    source_symbol VARCHAR,       -- actual contract (e.g., 'MGCG6')
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT
);
```

### bars_5m (and bars_5m_mpl, bars_5m_nq)
```sql
CREATE TABLE bars_5m (
    ts_utc TIMESTAMPTZ PRIMARY KEY,
    symbol VARCHAR,
    source_symbol VARCHAR,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT
);
```

### daily_features_v2 (and daily_features_v2_mpl, daily_features_v2_nq)
```sql
CREATE TABLE daily_features_v2 (
    date_local DATE PRIMARY KEY,

    -- Session data
    asia_high DOUBLE,
    asia_low DOUBLE,
    london_high DOUBLE,
    london_low DOUBLE,
    ny_high DOUBLE,
    ny_low DOUBLE,

    -- ORBs (6 total: 0900, 1000, 1100, 1800, 2300, 0030)
    orb_0900_high DOUBLE,
    orb_0900_low DOUBLE,
    orb_0900_size DOUBLE,
    orb_0900_break_dir VARCHAR,
    -- ... (repeated for each ORB time)

    -- Indicators
    atr_20 DOUBLE,
    rsi_14 DOUBLE,

    -- Pre-move metrics
    pre_ny_travel DOUBLE,
    pre_orb_travel DOUBLE
);
```

### validated_setups (shared across all instruments)
```sql
CREATE TABLE validated_setups (
    setup_id INTEGER PRIMARY KEY,
    instrument VARCHAR,           -- 'MGC', 'MPL', 'NQ'
    strategy_name VARCHAR,
    orb_time VARCHAR,
    rr_target DOUBLE,
    sl_mode VARCHAR,
    tier VARCHAR,
    win_rate DOUBLE,
    avg_r DOUBLE,
    trade_count INTEGER,
    orb_size_filter DOUBLE        -- NULL or threshold
);
```

---

## Query Patterns

### Get MGC bars
```sql
SELECT * FROM bars_1m WHERE ts_utc >= '2026-01-01';
```

### Get MPL bars
```sql
SELECT * FROM bars_1m_mpl WHERE ts_utc >= '2026-01-01';
```

### Get NQ bars
```sql
SELECT * FROM bars_1m_nq WHERE ts_utc >= '2026-01-01';
```

### Get all validated setups for MGC
```sql
SELECT * FROM validated_setups WHERE instrument = 'MGC';
```

### Get daily features for MPL
```sql
SELECT * FROM daily_features_v2_mpl ORDER BY date_local DESC LIMIT 30;
```

---

## Application Integration

### Python Code Pattern
```python
def get_bars_table(instrument: str) -> str:
    """Get table name for instrument"""
    if instrument == 'MGC':
        return 'bars_1m'
    elif instrument == 'MPL':
        return 'bars_1m_mpl'
    elif instrument == 'NQ':
        return 'bars_1m_nq'
    else:
        raise ValueError(f"Unknown instrument: {instrument}")

# Usage
instrument = 'MPL'
table = get_bars_table(instrument)
bars = conn.execute(f"SELECT * FROM {table} WHERE ts_utc >= ?", [start_date]).fetchall()
```

### Helper Function
```python
def get_feature_table(instrument: str) -> str:
    """Get daily features table for instrument"""
    if instrument == 'MGC':
        return 'daily_features_v2'
    else:
        return f'daily_features_v2_{instrument.lower()}'
```

---

## Data Pipeline

### Backfill Process
Each instrument has its own backfill workflow:

**MGC:**
```bash
python backfill_databento_continuous.py 2024-01-01 2026-01-10
python build_daily_features.py 2026-01-10
```

**MPL:**
```bash
python backfill_databento_continuous.py 2024-01-01 2026-01-10 --instrument MPL
python build_daily_features.py 2026-01-10 --instrument MPL
```

**NQ:**
```bash
python backfill_databento_continuous.py 2024-01-01 2026-01-10 --instrument NQ
python build_daily_features.py 2026-01-10 --instrument NQ
```

---

## Migration to Cloud (MotherDuck)

When ready to migrate to MotherDuck, migrate each instrument's tables:

### Tables to migrate per instrument:
- `bars_1m` (or `bars_1m_mpl`, `bars_1m_nq`)
- `bars_5m` (or `bars_5m_mpl`, `bars_5m_nq`)
- `daily_features_v2` (or `daily_features_v2_mpl`, `daily_features_v2_nq`)

### Shared tables (migrate once):
- `validated_setups`

---

## Adding New Instruments

To add ES (E-mini S&P 500):

1. **Create tables:**
   - `bars_1m_es`
   - `bars_5m_es`
   - `daily_features_v2_es`

2. **Backfill data:**
   ```bash
   python backfill_databento_continuous.py 2024-01-01 2026-01-10 --instrument ES
   ```

3. **Add strategies:**
   ```sql
   INSERT INTO validated_setups (instrument, strategy_name, ...)
   VALUES ('ES', 'DAY_ORB', ...);
   ```

4. **Update apps:**
   - Add 'ES' to instrument selector
   - Update table name helpers

---

## Audit Compatibility

Audits currently run on MGC only. To audit other instruments, specify the table:

```python
# audit_master.py --instrument MPL
auditor = DataIntegrityAuditor(db_path="gold.db", instrument="MPL")
```

---

## Why Not Consolidate?

**Consolidation Issues We Avoided:**
- Schema corruption (VARCHAR vs DOUBLE)
- Complex multi-instrument queries
- Performance overhead (larger tables)
- Migration complexity
- Rollback difficulty

**Separate Tables Benefits:**
- **Simple**: One query pattern per instrument
- **Fast**: Smaller indexes, faster queries
- **Safe**: No cross-contamination
- **Clear**: Easy to debug and maintain

---

## Current Status

✅ **All instruments have clean, working data:**
- MGC: 720K bars, 740 days, 6 strategies
- MPL: 327K bars, 730 days, 6 strategies
- NQ: 350K bars, 310 days, 5 strategies

✅ **Schema validated:**
- All DOUBLE types correct
- No corruption
- Audits pass (38/38 for MGC)

✅ **Production ready:**
- Apps work with all instruments
- Data pipeline tested
- Backup strategy in place

---

## References

- **CLAUDE.md**: Project overview and commands
- **PROJECT_STRUCTURE.md**: File organization
- **AUDIT_STATUS_JAN17.md**: Audit results
- **APP_PRODUCTION_STATUS.md**: Trading app status

---

Generated: 2026-01-18
Validated: Audit System v1.0
Architecture: Separate Tables Per Instrument
