"""
Compute session structural labels for conditional expectancy analysis.

CRITICAL: All labels computed ONLY from data available BEFORE the next ORB opens.
No lookahead. No optimization. Deterministic thresholds only.
"""

import duckdb
import pandas as pd
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

TZ_LOCAL = ZoneInfo("Australia/Brisbane")
conn = duckdb.connect("gold.db")

# HARD-CODED THRESHOLDS (NOT OPTIMIZED)
ASIA_TIGHT_THRESHOLD = 12.0    # ticks
ASIA_EXPANDED_THRESHOLD = 32.0  # ticks
NET_DIRECTION_THRESHOLD = 5.0   # ticks (0.5 price points)

# NY THRESHOLDS (NOT OPTIMIZED) - FIXED
NY_TIGHT_RATIO = 0.20           # ny_range / adr_20 <= 0.20
NY_EXPANDED_RATIO = 0.50        # ny_range / adr_20 >= 0.50
NY_NEUTRAL_THRESHOLD_PCT = 0.10  # abs(close - open) <= 0.10 * ny_range
NY_EXHAUSTION_MIDPOINT_THRESHOLD = 0.4  # Close within 40% of range from midpoint

def compute_asia_labels():
    """
    Compute Asia session labels (0900-1100 local).

    FIXED: Sweeps now reference PRIOR-SESSION liquidity only.

    Labels:
    - asia_sweep_high: True if Asia (0900-1100) traded above PRIOR session highs
      (previous day NY high, London high, or day high)
    - asia_sweep_low: True if Asia (0900-1100) traded below PRIOR session lows
    - asia_range_type: tight/normal/expanded (based on asia_range)
    - asia_net_direction: up/down/neutral (1100 close vs 0900 open)
    - asia_failure: True if 2+ Asia ORBs resulted in LOSS
    """

    print("Computing Asia session labels...")

    query = """
    WITH prior_day_levels AS (
        -- Get PRIOR day levels (day before current cycle_date)
        SELECT
            date_local + INTERVAL '1 day' as next_date,
            ny_high as prior_ny_high,
            ny_low as prior_ny_low,
            london_high as prior_london_high,
            london_low as prior_london_low,
            GREATEST(asia_high, london_high, ny_high) as prior_day_high,
            LEAST(asia_low, london_low, ny_low) as prior_day_low
        FROM daily_features
        WHERE asia_high IS NOT NULL
        AND london_high IS NOT NULL
        AND ny_high IS NOT NULL
    ),
    asia_bars AS (
        SELECT
            df.date_local,
            df.asia_high,
            df.asia_low,
            df.asia_range,
            df.orb_0900_outcome,
            df.orb_1000_outcome,
            df.orb_1100_outcome,
            -- Get prior day levels
            p.prior_ny_high,
            p.prior_ny_low,
            p.prior_london_high,
            p.prior_london_low,
            p.prior_day_high,
            p.prior_day_low,
            -- Get 0900 open (first bar at 09:00)
            (SELECT open FROM bars_5m b
             WHERE b.symbol = 'MGC'
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' >= (df.date_local + INTERVAL '9 hours')
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' < (df.date_local + INTERVAL '9 hours 5 minutes')
             ORDER BY ts_utc LIMIT 1) as asia_open,
            -- Get 1100 close (last bar before 11:00)
            (SELECT close FROM bars_5m b
             WHERE b.symbol = 'MGC'
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' >= (df.date_local + INTERVAL '10 hours 55 minutes')
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' < (df.date_local + INTERVAL '11 hours')
             ORDER BY ts_utc DESC LIMIT 1) as asia_close
        FROM daily_features df
        LEFT JOIN prior_day_levels p ON df.date_local = p.next_date
        WHERE df.asia_high IS NOT NULL
    )
    SELECT
        date_local,
        -- Sweep labels: Did Asia trade above/below PRIOR session levels?
        CASE
            WHEN asia_high > prior_ny_high
            OR asia_high > prior_london_high
            OR asia_high > prior_day_high
            THEN true
            ELSE false
        END as asia_sweep_high,
        CASE
            WHEN asia_low < prior_ny_low
            OR asia_low < prior_london_low
            OR asia_low < prior_day_low
            THEN true
            ELSE false
        END as asia_sweep_low,
        -- Range type (deterministic thresholds)
        CASE
            WHEN asia_range < 12.0 THEN 'tight'
            WHEN asia_range > 32.0 THEN 'expanded'
            ELSE 'normal'
        END as asia_range_type,
        -- Net direction (1100 close vs 0900 open)
        CASE
            WHEN asia_close IS NULL OR asia_open IS NULL THEN 'neutral'
            WHEN (asia_close - asia_open) > 0.5 THEN 'up'
            WHEN (asia_close - asia_open) < -0.5 THEN 'down'
            ELSE 'neutral'
        END as asia_net_direction,
        -- Failure: 2 or more Asia ORBs resulted in LOSS
        CASE
            WHEN (CASE WHEN orb_0900_outcome = 'LOSS' THEN 1 ELSE 0 END +
                  CASE WHEN orb_1000_outcome = 'LOSS' THEN 1 ELSE 0 END +
                  CASE WHEN orb_1100_outcome = 'LOSS' THEN 1 ELSE 0 END) >= 2
            THEN true
            ELSE false
        END as asia_failure
    FROM asia_bars
    """

    df = conn.execute(query).fetchdf()
    return df


def compute_london_labels():
    """
    Compute London session labels (1800-2300 local).

    FIXED: Sweeps now reference PRIOR-SESSION liquidity only.

    Labels:
    - london_sweep_prior_high: True if London (1800-2300) traded above PRIOR levels
      (Asia high, previous day high, previous NY high)
    - london_sweep_prior_low: True if London (1800-2300) traded below PRIOR levels
    - london_orb_outcome: hold/fail/reject (from orb_1800_outcome)
    """

    print("Computing London session labels...")

    query = """
    WITH prior_day_levels AS (
        -- Get PRIOR day levels (day before current cycle_date)
        SELECT
            date_local + INTERVAL '1 day' as next_date,
            ny_high as prior_ny_high,
            ny_low as prior_ny_low,
            GREATEST(asia_high, london_high, ny_high) as prior_day_high,
            LEAST(asia_low, london_low, ny_low) as prior_day_low
        FROM daily_features
        WHERE asia_high IS NOT NULL
        AND london_high IS NOT NULL
        AND ny_high IS NOT NULL
    ),
    london_bars AS (
        SELECT
            df.date_local,
            df.asia_high,
            df.asia_low,
            df.orb_1800_outcome,
            -- Get prior day levels
            p.prior_ny_high,
            p.prior_ny_low,
            p.prior_day_high,
            p.prior_day_low,
            -- London session high/low (1800-2300)
            (SELECT MAX(high) FROM bars_5m b
             WHERE b.symbol = 'MGC'
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' >= (df.date_local + INTERVAL '18 hours')
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' < (df.date_local + INTERVAL '23 hours')
            ) as london_high,
            (SELECT MIN(low) FROM bars_5m b
             WHERE b.symbol = 'MGC'
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' >= (df.date_local + INTERVAL '18 hours')
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' < (df.date_local + INTERVAL '23 hours')
            ) as london_low
        FROM daily_features df
        LEFT JOIN prior_day_levels p ON df.date_local = p.next_date
        WHERE df.orb_1800_high IS NOT NULL
    )
    SELECT
        date_local,
        -- Sweep labels: Did London trade above/below PRIOR levels?
        CASE
            WHEN london_high > asia_high
            OR london_high > prior_ny_high
            OR london_high > prior_day_high
            THEN true
            ELSE false
        END as london_sweep_prior_high,
        CASE
            WHEN london_low < asia_low
            OR london_low < prior_ny_low
            OR london_low < prior_day_low
            THEN true
            ELSE false
        END as london_sweep_prior_low,
        -- Map ORB outcome to hold/fail/reject
        CASE
            WHEN orb_1800_outcome = 'WIN' THEN 'hold'
            WHEN orb_1800_outcome = 'LOSS' THEN 'fail'
            WHEN orb_1800_outcome = 'NO_TRADE' THEN 'reject'
            ELSE 'reject'
        END as london_orb_outcome
    FROM london_bars
    """

    df = conn.execute(query).fetchdf()
    return df


def compute_ny_labels():
    """
    Compute NY pre-ORB session labels (2300-0030 local).

    CRITICAL: NY pre-ORB is an INVENTORY BUILD WINDOW, not a full session.
    It creates liquidity for NYSE 00:30 ORB to resolve (inventory handoff).
    We measure INVENTORY STATE, not prior-session sweeps.

    Labels:
    - ny_range_type: tight/normal/expanded (compression state, based on ny_range / adr_20 ratio)
    - ny_net_direction: up/down/neutral (balance state, scale-based: abs(close-open) vs 0.10 * ny_range)
    - ny_exhaustion: True if directional push then close back toward midpoint (potential reversal)
    - ny_orb_outcome: hold/fail/reject (from orb_0030_outcome)
    """

    print("Computing NY session labels...")

    query = """
    WITH daily_ranges AS (
        -- Compute full-day range for each day (for ADR calculation)
        SELECT
            date_local,
            GREATEST(asia_high, london_high, ny_high) - LEAST(asia_low, london_low, ny_low) as daily_range
        FROM daily_features
        WHERE asia_high IS NOT NULL
        AND london_high IS NOT NULL
        AND ny_high IS NOT NULL
    ),
    adr_20_window AS (
        -- Compute 20-day median daily range (ADR_20)
        SELECT
            date_local,
            daily_range,
            MEDIAN(daily_range) OVER (
                ORDER BY date_local
                ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
            ) as adr_20
        FROM daily_ranges
    ),
    ny_bars AS (
        SELECT
            df.date_local,
            adr.adr_20,
            df.orb_0030_outcome,
            -- Get 2300 open (first bar at 23:00)
            (SELECT open FROM bars_5m b
             WHERE b.symbol = 'MGC'
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' >= (df.date_local + INTERVAL '23 hours')
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' < (df.date_local + INTERVAL '23 hours 5 minutes')
             ORDER BY ts_utc LIMIT 1) as ny_open,
            -- Get 0030 close (last bar before 00:30, which is next day + 0.5 hours)
            (SELECT close FROM bars_5m b
             WHERE b.symbol = 'MGC'
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' >= (df.date_local + INTERVAL '1 day 0 hours 25 minutes')
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' < (df.date_local + INTERVAL '1 day 0 hours 30 minutes')
             ORDER BY ts_utc DESC LIMIT 1) as ny_close,
            -- NY pre-ORB range (2300-0030)
            (SELECT MAX(high) FROM bars_5m b
             WHERE b.symbol = 'MGC'
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' >= (df.date_local + INTERVAL '23 hours')
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' < (df.date_local + INTERVAL '1 day 0 hours 30 minutes')
            ) as ny_preorb_high,
            (SELECT MIN(low) FROM bars_5m b
             WHERE b.symbol = 'MGC'
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' >= (df.date_local + INTERVAL '23 hours')
             AND b.ts_utc AT TIME ZONE 'Australia/Brisbane' < (df.date_local + INTERVAL '1 day 0 hours 30 minutes')
            ) as ny_preorb_low
        FROM daily_features df
        LEFT JOIN adr_20_window adr ON df.date_local = adr.date_local
        WHERE df.orb_0030_high IS NOT NULL
    ),
    ny_inventory_state AS (
        SELECT
            *,
            -- NY range size (in ticks)
            (ny_preorb_high - ny_preorb_low) as ny_range,
            -- Midpoint of NY pre-ORB range
            (ny_preorb_high + ny_preorb_low) / 2.0 as ny_preorb_mid,
            -- Ratio: ny_range / adr_20
            CASE
                WHEN adr_20 IS NOT NULL AND adr_20 > 0 THEN (ny_preorb_high - ny_preorb_low) / adr_20
                ELSE NULL
            END as ny_range_ratio
        FROM ny_bars
    )
    SELECT
        date_local,
        -- Range type (based on ny_range / adr_20 ratio)
        CASE
            WHEN ny_range_ratio IS NULL THEN 'normal'
            WHEN ny_range_ratio <= 0.20 THEN 'tight'
            WHEN ny_range_ratio >= 0.50 THEN 'expanded'
            ELSE 'normal'
        END as ny_range_type,
        -- Net direction (scale-based: abs(close-open) vs 0.10 * ny_range)
        CASE
            WHEN ny_close IS NULL OR ny_open IS NULL OR ny_range IS NULL THEN 'neutral'
            WHEN ABS(ny_close - ny_open) <= (ny_range * 0.10) THEN 'neutral'
            WHEN (ny_close - ny_open) > 0 THEN 'up'
            ELSE 'down'
        END as ny_net_direction,
        -- Exhaustion: directional push then close back toward midpoint
        -- Definition: range > 0.20 * adr_20 AND close within 40% of range from midpoint
        CASE
            WHEN ny_range IS NULL OR ny_preorb_mid IS NULL OR ny_close IS NULL THEN false
            WHEN ny_range_ratio > 0.20  -- Sufficient range (not too tight)
            AND ABS(ny_close - ny_preorb_mid) < (ny_range * 0.4)  -- Close near midpoint
            THEN true
            ELSE false
        END as ny_exhaustion,
        -- NY ORB outcome (from 0030 ORB)
        CASE
            WHEN orb_0030_outcome = 'WIN' THEN 'hold'
            WHEN orb_0030_outcome = 'LOSS' THEN 'fail'
            WHEN orb_0030_outcome = 'NO_TRADE' THEN 'reject'
            ELSE 'reject'
        END as ny_orb_outcome,
        -- Store ratio for sanity checks
        ny_range_ratio,
        ny_range as ny_range_ticks,
        adr_20 as adr_20_ticks
    FROM ny_inventory_state
    """

    df = conn.execute(query).fetchdf()

    # SANITY CHECKS
    print("\n=== NY LABEL SANITY CHECKS ===")

    # Check range_type distribution
    print("\nny_range_type distribution:")
    print(df['ny_range_type'].value_counts())

    range_type_pcts = df['ny_range_type'].value_counts(normalize=True) * 100
    if any(range_type_pcts < 5) or any(range_type_pcts > 95):
        print("  [WARN] ny_range_type distribution is heavily skewed")

    # Check ny_range_ratio statistics
    if 'ny_range_ratio' in df.columns:
        ratio_valid = df['ny_range_ratio'].dropna()
        if len(ratio_valid) > 0:
            print(f"\nny_range_ratio statistics (n={len(ratio_valid)}):")
            print(f"  p10: {ratio_valid.quantile(0.10):.3f}")
            print(f"  p50: {ratio_valid.quantile(0.50):.3f}")
            print(f"  p90: {ratio_valid.quantile(0.90):.3f}")
            print(f"  min: {ratio_valid.min():.3f}")
            print(f"  max: {ratio_valid.max():.3f}")

    # Check net_direction distribution
    print("\nny_net_direction distribution:")
    print(df['ny_net_direction'].value_counts())

    # Drop diagnostic columns before returning
    df = df.drop(columns=['ny_range_ratio', 'ny_range_ticks', 'adr_20_ticks'], errors='ignore')

    return df


def create_session_labels_table():
    """
    Create and populate session_labels table with all structural labels.
    """

    print("\n=== CREATING SESSION LABELS TABLE ===\n")

    # Drop and recreate table
    conn.execute("DROP TABLE IF EXISTS session_labels")

    conn.execute("""
        CREATE TABLE session_labels (
            date_local DATE PRIMARY KEY,
            -- Asia labels (sweep = resolution of prior-session inventory)
            asia_sweep_high BOOLEAN,
            asia_sweep_low BOOLEAN,
            asia_range_type VARCHAR,
            asia_net_direction VARCHAR,
            asia_failure BOOLEAN,
            -- London labels (sweep = resolution of prior-session inventory)
            london_sweep_prior_high BOOLEAN,
            london_sweep_prior_low BOOLEAN,
            london_orb_outcome VARCHAR,
            -- NY labels (inventory state for NYSE 00:30 ORB handoff)
            ny_range_type VARCHAR,
            ny_net_direction VARCHAR,
            ny_exhaustion BOOLEAN,
            ny_orb_outcome VARCHAR
        )
    """)

    # Compute labels
    asia_labels = compute_asia_labels()
    london_labels = compute_london_labels()
    ny_labels = compute_ny_labels()

    # Merge labels on date_local
    labels = asia_labels.merge(london_labels, on='date_local', how='outer')
    labels = labels.merge(ny_labels, on='date_local', how='outer')

    # Insert into table
    conn.execute("INSERT INTO session_labels SELECT * FROM labels")
    conn.commit()

    # Show summary
    print("\n=== LABEL DISTRIBUTION ===\n")

    print("Asia Sweep High:", conn.execute("SELECT asia_sweep_high, COUNT(*) FROM session_labels GROUP BY asia_sweep_high").fetchdf())
    print("\nAsia Sweep Low:", conn.execute("SELECT asia_sweep_low, COUNT(*) FROM session_labels GROUP BY asia_sweep_low").fetchdf())
    print("\nAsia Range Type:", conn.execute("SELECT asia_range_type, COUNT(*) FROM session_labels GROUP BY asia_range_type ORDER BY COUNT(*) DESC").fetchdf())
    print("\nAsia Net Direction:", conn.execute("SELECT asia_net_direction, COUNT(*) FROM session_labels GROUP BY asia_net_direction ORDER BY COUNT(*) DESC").fetchdf())
    print("\nAsia Failure:", conn.execute("SELECT asia_failure, COUNT(*) FROM session_labels GROUP BY asia_failure").fetchdf())
    print("\nLondon Sweep Prior High:", conn.execute("SELECT london_sweep_prior_high, COUNT(*) FROM session_labels GROUP BY london_sweep_prior_high").fetchdf())
    print("\nLondon Sweep Prior Low:", conn.execute("SELECT london_sweep_prior_low, COUNT(*) FROM session_labels GROUP BY london_sweep_prior_low").fetchdf())
    print("\nLondon ORB Outcome:", conn.execute("SELECT london_orb_outcome, COUNT(*) FROM session_labels GROUP BY london_orb_outcome ORDER BY COUNT(*) DESC").fetchdf())

    print("\nNY Range Type:", conn.execute("SELECT ny_range_type, COUNT(*) FROM session_labels GROUP BY ny_range_type ORDER BY COUNT(*) DESC").fetchdf())
    print("\nNY Net Direction:", conn.execute("SELECT ny_net_direction, COUNT(*) FROM session_labels GROUP BY ny_net_direction ORDER BY COUNT(*) DESC").fetchdf())
    print("\nNY Exhaustion:", conn.execute("SELECT ny_exhaustion, COUNT(*) FROM session_labels GROUP BY ny_exhaustion").fetchdf())
    print("\nNY ORB Outcome:", conn.execute("SELECT ny_orb_outcome, COUNT(*) FROM session_labels GROUP BY ny_orb_outcome ORDER BY COUNT(*) DESC").fetchdf())

    print(f"\nCreated session_labels table with {len(labels)} rows")


if __name__ == "__main__":
    create_session_labels_table()
    conn.close()
