# MGC DAY-STATE FEATURE SPECIFICATION

**Purpose:** Market structure research dataset classifying each trading day using ONLY information available BEFORE each ORB open.

**Timezone:** Australia/Brisbane (UTC+10, NO DST)

**Date:** 2026-01-12

---

## FINAL SCHEMA

```sql
CREATE TABLE day_state_features (
    date_local DATE NOT NULL,
    orb_code VARCHAR NOT NULL,

    -- PRE-ORB WINDOW METRICS
    pre_orb_high DOUBLE,
    pre_orb_low DOUBLE,
    pre_orb_range DOUBLE,
    pre_orb_open DOUBLE,
    pre_orb_close DOUBLE,
    pre_orb_disp DOUBLE,
    pre_orb_n_bars INTEGER,

    -- NORMALIZED METRICS
    adr20 DOUBLE,
    range_ratio DOUBLE,
    disp_ratio DOUBLE,

    -- SHAPE METRICS
    pre_orb_close_pos DOUBLE,
    impulse_score DOUBLE,
    upper_wick_sum DOUBLE,
    lower_wick_sum DOUBLE,
    wick_ratio DOUBLE,

    -- RANGE CLASSIFICATION
    range_pct DOUBLE,
    range_bucket VARCHAR,  -- 'TIGHT', 'NORMAL', 'WIDE'

    -- DISPLACEMENT CLASSIFICATION
    disp_bucket VARCHAR,  -- 'D_SMALL', 'D_MED', 'D_LARGE'

    -- SESSION CONTEXT (populated based on orb_code)
    asia_high DOUBLE,
    asia_low DOUBLE,
    asia_range DOUBLE,
    asia_open DOUBLE,
    asia_close DOUBLE,
    asia_disp DOUBLE,
    asia_range_pct DOUBLE,
    asia_close_pos DOUBLE,
    asia_impulse DOUBLE,

    london_high DOUBLE,
    london_low DOUBLE,
    london_range DOUBLE,
    london_open DOUBLE,
    london_close DOUBLE,
    london_disp DOUBLE,
    london_range_pct DOUBLE,
    london_close_pos DOUBLE,
    london_impulse DOUBLE,

    nypre_high DOUBLE,
    nypre_low DOUBLE,
    nypre_range DOUBLE,
    nypre_open DOUBLE,
    nypre_close DOUBLE,
    nypre_disp DOUBLE,
    nypre_range_pct DOUBLE,

    -- SWEEP FLAGS (0030 only)
    london_swept_asia_high BOOLEAN,
    london_swept_asia_low BOOLEAN,
    nypre_swept_london_high_fail BOOLEAN,
    nypre_swept_london_low_fail BOOLEAN,

    -- METADATA
    computed_at TIMESTAMP,

    PRIMARY KEY (date_local, orb_code)
);
```

---

## A) PRE-ORB WINDOW DEFINITIONS

### Zero Look-Ahead Rule

For each ORB, the pre-ORB window ends **exactly at ORB open** and contains NO information from the ORB period or after.

### Window Specifications (Local Brisbane Time)

```python
PRE_ORB_WINDOWS = {
    '0900': {
        'start': (7, 0),   # 07:00 same day
        'end': (9, 0),     # 09:00 same day
        'context': None    # No prior session available
    },
    '1000': {
        'start': (9, 0),   # 09:00 same day
        'end': (10, 0),    # 10:00 same day
        'context': 'asia_partial_0900_1000'
    },
    '1100': {
        'start': (9, 0),   # 09:00 same day
        'end': (11, 0),    # 11:00 same day
        'context': 'asia_partial_0900_1100'
    },
    '1800': {
        'start': (17, 0),  # 17:00 same day
        'end': (18, 0),    # 18:00 same day
        'context': 'asia_complete_0900_1700'
    },
    '2300': {
        'start': (18, 0),  # 18:00 same day
        'end': (23, 0),    # 23:00 same day
        'context': 'london_partial_1800_2300'
    },
    '0030': {
        'start': (23, 0),  # 23:00 same day
        'end': (0, 30),    # 00:30 NEXT day (date rollover)
        'context': 'london_complete_1800_2300_plus_nypre_2300_0030'
    }
}
```

### Context Window Specifications

**Context windows** provide additional market structure information available before the ORB.

```python
CONTEXT_WINDOWS = {
    'asia_complete_0900_1700': {
        'start': (9, 0),
        'end': (17, 0),
        'same_day': True
    },
    'asia_partial_0900_1000': {
        'start': (9, 0),
        'end': (10, 0),
        'same_day': True
    },
    'asia_partial_0900_1100': {
        'start': (9, 0),
        'end': (11, 0),
        'same_day': True
    },
    'london_complete_1800_2300': {
        'start': (18, 0),
        'end': (23, 0),
        'same_day': True
    },
    'london_partial_1800_2300': {
        'start': (18, 0),
        'end': (23, 0),
        'same_day': True
    },
    'nypre_cash_2300_0030': {
        'start': (23, 0),
        'end': (0, 30),
        'same_day': False,  # Rolls to next calendar day
        'offset_days': 1
    }
}
```

---

## B) CORE FEATURES (ALL ORBs)

### 1. PRE-ORB RANGE METRICS

**SQL Definition:**
```sql
WITH pre_orb_bars AS (
    SELECT
        high,
        low,
        open,
        close
    FROM bars_1m
    WHERE symbol = 'MGC'
        AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= {pre_orb_start}
        AND ts_utc AT TIME ZONE 'Australia/Brisbane' < {pre_orb_end}
    ORDER BY ts_utc
)
SELECT
    MAX(high) as pre_orb_high,
    MIN(low) as pre_orb_low,
    (MAX(high) - MIN(low)) as pre_orb_range,
    (SELECT open FROM pre_orb_bars ORDER BY ts_utc LIMIT 1) as pre_orb_open,
    (SELECT close FROM pre_orb_bars ORDER BY ts_utc DESC LIMIT 1) as pre_orb_close,
    COUNT(*) as pre_orb_n_bars
FROM pre_orb_bars
```

**Pseudocode:**
```python
def compute_pre_orb_range(bars, start_ts, end_ts):
    """
    Compute range metrics for pre-ORB window.

    Args:
        bars: DataFrame with columns [ts_local, open, high, low, close]
        start_ts: Window start (inclusive)
        end_ts: Window end (exclusive)

    Returns:
        dict with keys: pre_orb_high, pre_orb_low, pre_orb_range,
                       pre_orb_open, pre_orb_close, pre_orb_n_bars
    """
    window_bars = bars[(bars['ts_local'] >= start_ts) &
                       (bars['ts_local'] < end_ts)]

    if len(window_bars) == 0:
        return None

    return {
        'pre_orb_high': window_bars['high'].max(),
        'pre_orb_low': window_bars['low'].min(),
        'pre_orb_range': window_bars['high'].max() - window_bars['low'].min(),
        'pre_orb_open': window_bars.iloc[0]['open'],
        'pre_orb_close': window_bars.iloc[-1]['close'],
        'pre_orb_n_bars': len(window_bars)
    }
```

### 2. PRE-ORB DISPLACEMENT (Signed)

```python
pre_orb_disp = pre_orb_close - pre_orb_open
```

**Sign interpretation:**
- Positive: Net upward movement in pre-ORB window
- Negative: Net downward movement in pre-ORB window
- Zero: Opened and closed at same price

### 3. NORMALIZED METRICS

#### ADR(20) Calculation

**Critical:** ADR(20) uses ONLY prior 20 complete trading days, EXCLUDING the current day.

**SQL Definition:**
```sql
WITH daily_ranges AS (
    SELECT
        DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') as date_local,
        MAX(high) - MIN(low) as daily_range
    FROM bars_1m
    WHERE symbol = 'MGC'
        AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') < {current_date}
    GROUP BY DATE(ts_utc AT TIME ZONE 'Australia/Brisbane')
    ORDER BY date_local DESC
    LIMIT 20
)
SELECT AVG(daily_range) as adr20
FROM daily_ranges
```

**Pseudocode:**
```python
def compute_adr20(date_local, bars_1m):
    """
    Compute ADR(20) using ONLY prior 20 complete trading days.

    Args:
        date_local: Current date (exclude this date)
        bars_1m: All 1-minute bars

    Returns:
        float: Average daily range over prior 20 days
    """
    # Get prior 20 complete days (exclude current date)
    prior_bars = bars_1m[bars_1m['date_local'] < date_local]

    # Compute daily range for each day
    daily_ranges = prior_bars.groupby('date_local').agg({
        'high': 'max',
        'low': 'min'
    })
    daily_ranges['range'] = daily_ranges['high'] - daily_ranges['low']

    # Take last 20 days
    last_20 = daily_ranges.sort_index().tail(20)

    if len(last_20) < 20:
        return None  # Insufficient history

    return last_20['range'].mean()
```

#### Range Ratio

```python
range_ratio = pre_orb_range / adr20
```

**Interpretation:**
- < 0.3: Very tight pre-ORB range
- 0.3-0.7: Normal pre-ORB range
- > 0.7: Wide pre-ORB range

#### Displacement Ratio

```python
disp_ratio = abs(pre_orb_disp) / adr20
```

**Interpretation:**
- < 0.3: Small displacement (consolidation)
- 0.3-0.7: Medium displacement (trend)
- > 0.7: Large displacement (strong trend)

### 4. SHAPE / STRUCTURE METRICS

#### Close Position in Range

**SQL:**
```sql
pre_orb_close_pos = (pre_orb_close - pre_orb_low) / NULLIF(pre_orb_range, 0)
```

**Interpretation:**
- 0.0: Closed at pre-ORB low (bearish)
- 0.5: Closed at pre-ORB midpoint (neutral)
- 1.0: Closed at pre-ORB high (bullish)

#### Impulse Score (Trendiness Proxy)

**SQL:**
```sql
impulse_score = ABS(pre_orb_disp) / NULLIF(pre_orb_range, 0)
```

**Interpretation:**
- Near 0: Choppy, no trend (open = close, lots of wicks)
- 0.5-0.7: Moderate trend
- > 0.8: Strong trend (small wicks, directional move)

#### Wickiness Proxy

**SQL:**
```sql
WITH bar_wicks AS (
    SELECT
        ts_local,
        open,
        high,
        low,
        close,
        CASE
            WHEN close >= open THEN high - close  -- Bull bar: upper wick
            ELSE high - open
        END as upper_wick,
        CASE
            WHEN close >= open THEN open - low    -- Bull bar: lower wick
            ELSE close - low
        END as lower_wick
    FROM bars_1m
    WHERE symbol = 'MGC'
        AND ts_local >= {pre_orb_start}
        AND ts_local < {pre_orb_end}
)
SELECT
    SUM(upper_wick) as upper_wick_sum,
    SUM(lower_wick) as lower_wick_sum,
    (SUM(upper_wick) + SUM(lower_wick)) /
        NULLIF({pre_orb_range} * {n_bars}, 0) as wick_ratio
FROM bar_wicks
```

**Pseudocode:**
```python
def compute_wickiness(bars):
    """
    Compute wick metrics for bar array.

    Wick definition:
    - Bull bar (close >= open): upper_wick = high - close, lower_wick = open - low
    - Bear bar (close < open):  upper_wick = high - open,  lower_wick = close - low
    """
    upper_wicks = []
    lower_wicks = []

    for bar in bars:
        if bar['close'] >= bar['open']:
            upper_wicks.append(bar['high'] - bar['close'])
            lower_wicks.append(bar['open'] - bar['low'])
        else:
            upper_wicks.append(bar['high'] - bar['open'])
            lower_wicks.append(bar['close'] - bar['low'])

    upper_wick_sum = sum(upper_wicks)
    lower_wick_sum = sum(lower_wicks)

    # Normalize by total possible range across all bars
    n_bars = len(bars)
    pre_orb_range = bars['high'].max() - bars['low'].min()
    wick_ratio = (upper_wick_sum + lower_wick_sum) / (pre_orb_range * n_bars)

    return {
        'upper_wick_sum': upper_wick_sum,
        'lower_wick_sum': lower_wick_sum,
        'wick_ratio': wick_ratio
    }
```

**Interpretation:**
- Low wick_ratio (< 0.3): Directional bars, little rejection
- High wick_ratio (> 0.5): Choppy bars, lots of rejection

### 5. RANGE PERCENTILE CLASSIFICATION

**Critical:** Compute percentile SEPARATELY for each ORB code using that ORB's trailing 60 occurrences.

**SQL:**
```sql
WITH orb_history AS (
    SELECT
        date_local,
        pre_orb_range,
        PERCENT_RANK() OVER (
            ORDER BY pre_orb_range
        ) * 100 as range_pct
    FROM day_state_features
    WHERE orb_code = {current_orb_code}
        AND date_local < {current_date}
    ORDER BY date_local DESC
    LIMIT 60
)
SELECT
    range_pct,
    CASE
        WHEN range_pct <= 20 THEN 'TIGHT'
        WHEN range_pct >= 80 THEN 'WIDE'
        ELSE 'NORMAL'
    END as range_bucket
FROM orb_history
WHERE date_local = (SELECT MAX(date_local) FROM orb_history)
```

**Pseudocode:**
```python
def compute_range_percentile(orb_code, date_local, current_range, history_df):
    """
    Compute percentile rank of current pre_orb_range vs trailing 60 occurrences
    of the same ORB code.

    Args:
        orb_code: ORB code (e.g., '0900', '1800')
        date_local: Current date
        current_range: Current pre_orb_range
        history_df: DataFrame with columns [date_local, orb_code, pre_orb_range]

    Returns:
        dict with keys: range_pct (0-100), range_bucket ('TIGHT'/'NORMAL'/'WIDE')
    """
    # Get trailing 60 occurrences of same ORB (exclude current date)
    orb_history = history_df[
        (history_df['orb_code'] == orb_code) &
        (history_df['date_local'] < date_local)
    ].sort_values('date_local', ascending=False).head(60)

    if len(orb_history) < 60:
        return None  # Insufficient history

    # Compute percentile rank
    rank = (orb_history['pre_orb_range'] < current_range).sum()
    range_pct = (rank / len(orb_history)) * 100

    # Bucket
    if range_pct <= 20:
        bucket = 'TIGHT'
    elif range_pct >= 80:
        bucket = 'WIDE'
    else:
        bucket = 'NORMAL'

    return {
        'range_pct': range_pct,
        'range_bucket': bucket
    }
```

### 6. DISPLACEMENT BUCKET CLASSIFICATION

**Based on disp_ratio:**

```python
def classify_displacement(disp_ratio):
    """
    Classify displacement magnitude.

    Args:
        disp_ratio: abs(pre_orb_disp) / adr20

    Returns:
        str: 'D_SMALL', 'D_MED', or 'D_LARGE'
    """
    if disp_ratio <= 0.3:
        return 'D_SMALL'
    elif disp_ratio <= 0.7:
        return 'D_MED'
    else:
        return 'D_LARGE'
```

---

## C) ORB-SPECIFIC CONTEXT FEATURES

### Context Applicability Matrix

| ORB Code | Pre-ORB Window | Asia Context | London Context | NY Pre-Cash Context |
|----------|----------------|--------------|----------------|---------------------|
| 0900 | 07:00-09:00 | ❌ None | ❌ None | ❌ None |
| 1000 | 09:00-10:00 | ✅ Partial (09:00-10:00) | ❌ None | ❌ None |
| 1100 | 09:00-11:00 | ✅ Partial (09:00-11:00) | ❌ None | ❌ None |
| 1800 | 17:00-18:00 | ✅ Complete (09:00-17:00) | ❌ None | ❌ None |
| 2300 | 18:00-23:00 | ✅ Complete (09:00-17:00) | ✅ Partial (18:00-23:00) | ❌ None |
| 0030 | 23:00-00:30 | ✅ Complete (09:00-17:00) | ✅ Complete (18:00-23:00) | ✅ Complete (23:00-00:30) |

### 1. ASIA SESSION METRICS

**Applies to:** 1000, 1100, 1800, 2300, 0030

**Window definitions:**
- For 1000: 09:00-10:00 (partial)
- For 1100: 09:00-11:00 (partial)
- For 1800, 2300, 0030: 09:00-17:00 (complete)

**SQL Template:**
```sql
WITH asia_bars AS (
    SELECT
        high,
        low,
        open,
        close
    FROM bars_1m
    WHERE symbol = 'MGC'
        AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') = {date_local}
        AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') >= 9
        AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < {asia_end_hour}
    ORDER BY ts_utc
)
SELECT
    MAX(high) as asia_high,
    MIN(low) as asia_low,
    (MAX(high) - MIN(low)) as asia_range,
    (SELECT open FROM asia_bars ORDER BY ts_utc LIMIT 1) as asia_open,
    (SELECT close FROM asia_bars ORDER BY ts_utc DESC LIMIT 1) as asia_close
FROM asia_bars
```

**Derived metrics:**
```python
asia_disp = asia_close - asia_open
asia_close_pos = (asia_close - asia_low) / asia_range
asia_impulse = abs(asia_disp) / asia_range
```

**Asia Range Percentile:**
```python
# Use same percentile logic as pre_orb_range, but against trailing 60 Asia sessions
asia_range_pct = percentile_rank(asia_range, trailing_60_asia_ranges)
```

### 2. LONDON SESSION METRICS

**Applies to:** 2300, 0030

**Window definition:**
- For both: 18:00-23:00 (complete)

**SQL Template:**
```sql
WITH london_bars AS (
    SELECT
        high,
        low,
        open,
        close
    FROM bars_1m
    WHERE symbol = 'MGC'
        AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') = {date_local}
        AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') >= 18
        AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < 23
    ORDER BY ts_utc
)
SELECT
    MAX(high) as london_high,
    MIN(low) as london_low,
    (MAX(high) - MIN(low)) as london_range,
    (SELECT open FROM london_bars ORDER BY ts_utc LIMIT 1) as london_open,
    (SELECT close FROM london_bars ORDER BY ts_utc DESC LIMIT 1) as london_close
FROM london_bars
```

**Derived metrics:**
```python
london_disp = london_close - london_open
london_close_pos = (london_close - london_low) / london_range
london_impulse = abs(london_disp) / london_range
london_range_pct = percentile_rank(london_range, trailing_60_london_ranges)
```

### 3. NY PRE-CASH METRICS

**Applies to:** 0030 only

**Window definition:** 23:00 (same day) → 00:30 (next calendar day)

**CRITICAL DATE HANDLING:**
```python
# For date_local = '2024-01-15' and orb_code = '0030':
# Window is:
#   start: '2024-01-15 23:00:00' (same day)
#   end:   '2024-01-16 00:30:00' (NEXT calendar day)
```

**SQL Template:**
```sql
WITH nypre_bars AS (
    SELECT
        high,
        low,
        open,
        close
    FROM bars_1m
    WHERE symbol = 'MGC'
        AND (
            -- Same day 23:00-23:59
            (DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') = {date_local}
             AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') = 23)
            OR
            -- Next day 00:00-00:29
            (DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') = {date_local + 1 day}
             AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') = 0
             AND EXTRACT(MINUTE FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < 30)
        )
    ORDER BY ts_utc
)
SELECT
    MAX(high) as nypre_high,
    MIN(low) as nypre_low,
    (MAX(high) - MIN(low)) as nypre_range,
    (SELECT open FROM nypre_bars ORDER BY ts_utc LIMIT 1) as nypre_open,
    (SELECT close FROM nypre_bars ORDER BY ts_utc DESC LIMIT 1) as nypre_close
FROM nypre_bars
```

**Derived metrics:**
```python
nypre_disp = nypre_close - nypre_open
nypre_range_pct = percentile_rank(nypre_range, trailing_60_nypre_ranges)
```

### 4. SWEEP FLAGS

**Applies to:** 0030 only

**Definition of "sweep":**
A sweep occurs when price extends beyond a prior session's boundary, then closes back inside that session's range.

**Parameters:**
```python
SWEEP_THRESHOLD_TICKS = 3  # Minimum extension beyond boundary
TICK_SIZE = 0.10  # MGC tick size
```

#### London Swept Asia High

```python
def london_swept_asia_high(asia_high, london_high, london_close, threshold_ticks=3):
    """
    Check if London swept Asia high and failed.

    Conditions:
    1. London high exceeded Asia high by threshold_ticks
    2. London close is back inside Asia range (< Asia high)

    Returns:
        bool
    """
    threshold = threshold_ticks * TICK_SIZE

    extended = london_high > (asia_high + threshold)
    closed_back_inside = london_close < asia_high

    return extended and closed_back_inside
```

#### London Swept Asia Low

```python
def london_swept_asia_low(asia_low, london_low, london_close, threshold_ticks=3):
    """
    Check if London swept Asia low and failed.

    Conditions:
    1. London low broke Asia low by threshold_ticks
    2. London close is back inside Asia range (> Asia low)

    Returns:
        bool
    """
    threshold = threshold_ticks * TICK_SIZE

    extended = london_low < (asia_low - threshold)
    closed_back_inside = london_close > asia_low

    return extended and closed_back_inside
```

#### NY Pre-Cash Swept London High (Failed)

```python
def nypre_swept_london_high_fail(london_high, nypre_high, nypre_close, threshold_ticks=3):
    """
    Check if NY pre-cash swept London high and failed.

    Conditions:
    1. NY pre-cash high exceeded London high by threshold_ticks
    2. NY pre-cash close is back inside London range (< London high)

    Returns:
        bool
    """
    threshold = threshold_ticks * TICK_SIZE

    extended = nypre_high > (london_high + threshold)
    closed_back_inside = nypre_close < london_high

    return extended and closed_back_inside
```

#### NY Pre-Cash Swept London Low (Failed)

```python
def nypre_swept_london_low_fail(london_low, nypre_low, nypre_close, threshold_ticks=3):
    """
    Check if NY pre-cash swept London low and failed.

    Conditions:
    1. NY pre-cash low broke London low by threshold_ticks
    2. NY pre-cash close is back inside London range (> London low)

    Returns:
        bool
    """
    threshold = threshold_ticks * TICK_SIZE

    extended = nypre_low < (london_low - threshold)
    closed_back_inside = nypre_close > london_low

    return extended and closed_back_inside
```

---

## D) IMPLEMENTATION PSEUDOCODE

### Main Build Function

```python
def build_day_state_features(start_date, end_date, bars_1m, db_conn):
    """
    Build day-state feature dataset for all ORBs across date range.

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        bars_1m: DataFrame with 1-minute bars
        db_conn: Database connection

    Returns:
        DataFrame with schema matching day_state_features table
    """
    ORB_CODES = ['0900', '1000', '1100', '1800', '2300', '0030']

    results = []

    for date in daterange(start_date, end_date):
        for orb_code in ORB_CODES:
            # Compute features for this (date, orb_code) pair
            features = compute_day_state_row(date, orb_code, bars_1m, db_conn)

            if features is not None:
                results.append(features)

    # Convert to DataFrame and save to database
    df = pd.DataFrame(results)
    df.to_sql('day_state_features', db_conn, if_exists='append', index=False)

    return df


def compute_day_state_row(date_local, orb_code, bars_1m, db_conn):
    """
    Compute single day-state row for given date and ORB code.

    Returns:
        dict with all feature columns, or None if insufficient data
    """
    # Get pre-ORB window definition
    pre_orb_start, pre_orb_end = get_pre_orb_window(date_local, orb_code)

    # Extract bars for pre-ORB window
    pre_orb_bars = bars_1m[
        (bars_1m['ts_local'] >= pre_orb_start) &
        (bars_1m['ts_local'] < pre_orb_end)
    ]

    if len(pre_orb_bars) == 0:
        return None  # No data for this ORB

    # Compute core features (all ORBs)
    row = {}
    row['date_local'] = date_local
    row['orb_code'] = orb_code

    # 1. Pre-ORB range metrics
    row.update(compute_pre_orb_range(pre_orb_bars))

    # 2. Pre-ORB displacement
    row['pre_orb_disp'] = row['pre_orb_close'] - row['pre_orb_open']

    # 3. Normalized metrics
    adr20 = compute_adr20(date_local, bars_1m)
    if adr20 is None or adr20 == 0:
        return None  # Cannot normalize

    row['adr20'] = adr20
    row['range_ratio'] = row['pre_orb_range'] / adr20
    row['disp_ratio'] = abs(row['pre_orb_disp']) / adr20

    # 4. Shape metrics
    if row['pre_orb_range'] > 0:
        row['pre_orb_close_pos'] = (row['pre_orb_close'] - row['pre_orb_low']) / row['pre_orb_range']
        row['impulse_score'] = abs(row['pre_orb_disp']) / row['pre_orb_range']
    else:
        row['pre_orb_close_pos'] = 0.5
        row['impulse_score'] = 0.0

    row.update(compute_wickiness(pre_orb_bars))

    # 5. Range percentile
    range_pct_data = compute_range_percentile(
        orb_code, date_local, row['pre_orb_range'], db_conn
    )
    if range_pct_data is not None:
        row.update(range_pct_data)

    # 6. Displacement bucket
    row['disp_bucket'] = classify_displacement(row['disp_ratio'])

    # 7. ORB-specific context features
    row.update(compute_context_features(date_local, orb_code, bars_1m, db_conn))

    # 8. Metadata
    row['computed_at'] = datetime.now()

    return row


def compute_context_features(date_local, orb_code, bars_1m, db_conn):
    """
    Compute ORB-specific context features.

    Returns:
        dict with context feature columns (NULL for non-applicable ORBs)
    """
    context = {
        'asia_high': None,
        'asia_low': None,
        'asia_range': None,
        'asia_open': None,
        'asia_close': None,
        'asia_disp': None,
        'asia_range_pct': None,
        'asia_close_pos': None,
        'asia_impulse': None,
        'london_high': None,
        'london_low': None,
        'london_range': None,
        'london_open': None,
        'london_close': None,
        'london_disp': None,
        'london_range_pct': None,
        'london_close_pos': None,
        'london_impulse': None,
        'nypre_high': None,
        'nypre_low': None,
        'nypre_range': None,
        'nypre_open': None,
        'nypre_close': None,
        'nypre_disp': None,
        'nypre_range_pct': None,
        'london_swept_asia_high': None,
        'london_swept_asia_low': None,
        'nypre_swept_london_high_fail': None,
        'nypre_swept_london_low_fail': None
    }

    # Asia context (for 1000, 1100, 1800, 2300, 0030)
    if orb_code in ['1000', '1100', '1800', '2300', '0030']:
        asia_metrics = compute_asia_metrics(date_local, orb_code, bars_1m, db_conn)
        if asia_metrics is not None:
            context.update(asia_metrics)

    # London context (for 2300, 0030)
    if orb_code in ['2300', '0030']:
        london_metrics = compute_london_metrics(date_local, bars_1m, db_conn)
        if london_metrics is not None:
            context.update(london_metrics)

    # NY pre-cash context (for 0030 only)
    if orb_code == '0030':
        nypre_metrics = compute_nypre_metrics(date_local, bars_1m, db_conn)
        if nypre_metrics is not None:
            context.update(nypre_metrics)

        # Sweep flags (requires Asia, London, and NY pre-cash data)
        if (context['asia_high'] is not None and
            context['london_high'] is not None and
            context['nypre_high'] is not None):

            context['london_swept_asia_high'] = london_swept_asia_high(
                context['asia_high'], context['london_high'], context['london_close']
            )
            context['london_swept_asia_low'] = london_swept_asia_low(
                context['asia_low'], context['london_low'], context['london_close']
            )
            context['nypre_swept_london_high_fail'] = nypre_swept_london_high_fail(
                context['london_high'], context['nypre_high'], context['nypre_close']
            )
            context['nypre_swept_london_low_fail'] = nypre_swept_london_low_fail(
                context['london_low'], context['nypre_low'], context['nypre_close']
            )

    return context
```

---

## E) VALIDATION CHECKS

### Zero Look-Ahead Verification

For each (date, orb_code) row, verify:

```python
def validate_zero_lookahead(date_local, orb_code, feature_row, bars_1m):
    """
    Verify that no feature uses information from ORB period or later.

    Checks:
    1. All timestamps in feature computation < ORB open time
    2. Context windows do not overlap with ORB period
    3. Historical percentiles use only prior dates

    Returns:
        bool: True if valid, False if look-ahead detected
    """
    orb_open_ts = get_orb_open_timestamp(date_local, orb_code)

    # Check: Pre-ORB window ends before ORB open
    pre_orb_end = get_pre_orb_window(date_local, orb_code)[1]
    if pre_orb_end != orb_open_ts:
        return False

    # Check: All context windows end before ORB open
    if orb_code == '1800':
        # Asia context must end at 17:00 (before 18:00 ORB)
        asia_end = datetime.combine(date_local, time(17, 0))
        if asia_end >= orb_open_ts:
            return False

    if orb_code == '2300':
        # London context must end at 23:00 (before 23:00 ORB)
        london_end = datetime.combine(date_local, time(23, 0))
        if london_end > orb_open_ts:
            return False

    if orb_code == '0030':
        # NY pre-cash context must end at 00:30 (before 00:30 ORB)
        nypre_end = datetime.combine(date_local + timedelta(days=1), time(0, 30))
        if nypre_end > orb_open_ts:
            return False

    # Check: ADR20 uses only prior dates
    # (Implicit in compute_adr20 function)

    # Check: Percentiles use only prior occurrences
    # (Implicit in compute_range_percentile function)

    return True
```

### Data Completeness Check

```python
def validate_completeness(feature_row):
    """
    Check that required features are populated for each ORB type.

    Returns:
        dict: {
            'valid': bool,
            'missing_required': list of missing field names
        }
    """
    orb_code = feature_row['orb_code']
    missing = []

    # Core features (required for ALL ORBs)
    core_required = [
        'pre_orb_high', 'pre_orb_low', 'pre_orb_range',
        'pre_orb_open', 'pre_orb_close', 'pre_orb_disp',
        'adr20', 'range_ratio', 'disp_ratio',
        'pre_orb_close_pos', 'impulse_score',
        'range_pct', 'range_bucket', 'disp_bucket'
    ]

    for field in core_required:
        if feature_row.get(field) is None:
            missing.append(field)

    # Context-specific requirements
    if orb_code in ['1000', '1100', '1800', '2300', '0030']:
        asia_required = ['asia_high', 'asia_low', 'asia_range']
        for field in asia_required:
            if feature_row.get(field) is None:
                missing.append(field)

    if orb_code in ['2300', '0030']:
        london_required = ['london_high', 'london_low', 'london_range']
        for field in london_required:
            if feature_row.get(field) is None:
                missing.append(field)

    if orb_code == '0030':
        nypre_required = ['nypre_high', 'nypre_low', 'nypre_range']
        sweep_required = [
            'london_swept_asia_high', 'london_swept_asia_low',
            'nypre_swept_london_high_fail', 'nypre_swept_london_low_fail'
        ]
        for field in nypre_required + sweep_required:
            if feature_row.get(field) is None:
                missing.append(field)

    return {
        'valid': len(missing) == 0,
        'missing_required': missing
    }
```

---

## F) USAGE EXAMPLES

### Example 1: Build Features for Date Range

```python
from datetime import date
import duckdb

# Connect to database
con = duckdb.connect('gold.db')

# Load 1-minute bars
bars_1m = con.execute("""
    SELECT
        ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local,
        open,
        high,
        low,
        close,
        volume
    FROM bars_1m
    WHERE symbol = 'MGC'
        AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') >= '2024-01-01'
        AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') <= '2026-01-10'
    ORDER BY ts_utc
""").df()

# Build features
features_df = build_day_state_features(
    start_date=date(2024, 1, 1),
    end_date=date(2026, 1, 10),
    bars_1m=bars_1m,
    db_conn=con
)

# Save to database
features_df.to_sql('day_state_features', con, if_exists='replace', index=False)

con.close()
```

### Example 2: Query Features for Specific ORB

```python
# Get all 0030 ORB day-states with London sweep signals
con = duckdb.connect('gold.db', read_only=True)

df = con.execute("""
    SELECT
        date_local,
        orb_code,
        pre_orb_range,
        range_bucket,
        disp_bucket,
        asia_range,
        london_range,
        nypre_range,
        london_swept_asia_high,
        london_swept_asia_low,
        nypre_swept_london_high_fail,
        nypre_swept_london_low_fail
    FROM day_state_features
    WHERE orb_code = '0030'
        AND (london_swept_asia_high = TRUE
             OR london_swept_asia_low = TRUE
             OR nypre_swept_london_high_fail = TRUE
             OR nypre_swept_london_low_fail = TRUE)
    ORDER BY date_local
""").df()

print(f"Found {len(df)} days with sweep signals at 0030 ORB")
con.close()
```

### Example 3: Classify Day by Combined Features

```python
def classify_day_state(feature_row):
    """
    Example day-state classifier combining multiple features.

    Returns:
        str: Day-state label
    """
    orb = feature_row['orb_code']

    # Example: Classify 0030 ORB days
    if orb == '0030':
        # Tight range + London swept Asia high = "London Rejection High"
        if (feature_row['range_bucket'] == 'TIGHT' and
            feature_row['london_swept_asia_high'] == True):
            return 'LONDON_REJECTION_HIGH'

        # Wide range + Large displacement = "Trending Day"
        if (feature_row['range_bucket'] == 'WIDE' and
            feature_row['disp_bucket'] == 'D_LARGE'):
            return 'TRENDING_DAY'

        # Normal range + Small displacement = "Consolidation"
        if (feature_row['range_bucket'] == 'NORMAL' and
            feature_row['disp_bucket'] == 'D_SMALL'):
            return 'CONSOLIDATION'

    return 'UNCLASSIFIED'


# Apply classifier
features_df['day_state_label'] = features_df.apply(classify_day_state, axis=1)
```

---

## G) PERFORMANCE OPTIMIZATION

### Batch Processing

```python
def build_features_batched(start_date, end_date, bars_1m, db_conn, batch_size=30):
    """
    Build features in batches to optimize memory usage and commit frequency.

    Args:
        batch_size: Number of days to process before committing to database
    """
    date_range = list(daterange(start_date, end_date))

    for i in range(0, len(date_range), batch_size):
        batch_dates = date_range[i:i+batch_size]

        print(f"Processing batch {i//batch_size + 1}: "
              f"{batch_dates[0]} to {batch_dates[-1]}")

        batch_features = build_day_state_features(
            start_date=batch_dates[0],
            end_date=batch_dates[-1],
            bars_1m=bars_1m,
            db_conn=db_conn
        )

        # Commit batch
        db_conn.commit()
```

### Caching ADR20

```python
def compute_adr20_cached(date_local, bars_1m, adr_cache):
    """
    Compute ADR20 with caching to avoid redundant calculations.

    Cache key: date_local - 1 day (since ADR20 uses prior 20 days)
    """
    cache_key = date_local - timedelta(days=1)

    if cache_key in adr_cache:
        return adr_cache[cache_key]

    adr20 = compute_adr20(date_local, bars_1m)
    adr_cache[cache_key] = adr20

    return adr20
```

---

## H) SUMMARY

### Feature Count by ORB

| ORB | Core Features | Context Features | Total |
|-----|---------------|------------------|-------|
| 0900 | 17 | 0 | 17 |
| 1000 | 17 | 9 (Asia partial) | 26 |
| 1100 | 17 | 9 (Asia partial) | 26 |
| 1800 | 17 | 9 (Asia complete) | 26 |
| 2300 | 17 | 18 (Asia + London) | 35 |
| 0030 | 17 | 31 (Asia + London + NY pre + Sweeps) | 48 |

### Key Principles

1. **Zero Look-Ahead:** All features computed using ONLY information available BEFORE ORB open
2. **ORB Independence:** Each ORB treated as separate event anchor with its own context
3. **Percentile Normalization:** Range/displacement classified relative to SAME ORB's history
4. **Session Context:** Only include completed sessions that end before ORB open
5. **Robust Metrics:** Simple, threshold-based features avoid over-fitting

### Next Steps

1. Implement `build_day_state_features.py` script
2. Backfill features for 2024-2026 date range
3. Validate zero look-ahead on random sample
4. Run exploratory analysis to identify significant features
5. Use features for day-state clustering or supervised classification

---

**This specification provides a complete, zero-bias foundation for market structure research on MGC ORBs.**
