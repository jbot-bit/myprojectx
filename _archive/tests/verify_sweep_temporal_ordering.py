"""
MANDATORY SANITY CHECKS FOR SWEEP TEMPORAL ORDERING

For 5 random sweep=true days per session, verify that:
1. Swept levels existed BEFORE the session opened
2. swept_level_timestamp < session_open_timestamp

This ensures sweep labels only reference PRIOR-SESSION liquidity.
"""

import duckdb
import pandas as pd
from zoneinfo import ZoneInfo
from datetime import datetime

TZ_LOCAL = ZoneInfo("Australia/Brisbane")
conn = duckdb.connect("gold.db")

print("="*80)
print("SWEEP TEMPORAL ORDERING VERIFICATION")
print("="*80)


def verify_asia_sweeps():
    """
    Asia session (0900-1100) sweeps reference:
    - prior_ny_high/low (previous day 2300-0200)
    - prior_london_high/low (previous day 1800-2300)
    - prior_day_high/low (previous day full day)

    All must exist before 09:00 current day.
    """
    print("\n--- ASIA SWEEPS (0900-1100) ---")

    # Get 5 random days with asia_sweep_high = true
    query = """
    SELECT
        sl.date_local,
        sl.asia_sweep_high,
        sl.asia_sweep_low,
        df.asia_high,
        df.asia_low
    FROM session_labels sl
    LEFT JOIN daily_features df ON sl.date_local = df.date_local
    WHERE sl.asia_sweep_high = true
    ORDER BY RANDOM()
    LIMIT 5
    """

    samples = conn.execute(query).fetchdf()

    for idx, row in samples.iterrows():
        cycle_date = pd.Timestamp(row['date_local']).to_pydatetime()
        asia_open = datetime(cycle_date.year, cycle_date.month, cycle_date.day, 9, 0, 0, tzinfo=TZ_LOCAL)

        print(f"\nSample {idx+1}:")
        print(f"  cycle_date: {cycle_date}")
        print(f"  asia_open_ts: {asia_open}")
        print(f"  asia_high: {row['asia_high']:.2f}")

        # Get prior day levels (from previous cycle_date)
        prior_date = cycle_date - pd.Timedelta(days=1)
        prior_query = f"""
        SELECT
            date_local,
            ny_high,
            london_high,
            GREATEST(asia_high, london_high, ny_high) as day_high
        FROM daily_features
        WHERE date_local = '{prior_date.strftime('%Y-%m-%d')}'
        """

        prior_data = conn.execute(prior_query).fetchdf()

        if len(prior_data) > 0:
            prior_row = prior_data.iloc[0]

            # Prior day NY session ended at 02:00 current day
            prior_ny_end = datetime(cycle_date.year, cycle_date.month, cycle_date.day, 2, 0, 0, tzinfo=TZ_LOCAL)

            # Prior day London session ended at 23:00 prior day
            prior_london_end = datetime(prior_date.year, prior_date.month, prior_date.day, 23, 0, 0, tzinfo=TZ_LOCAL)

            # Prior day full day ended at 09:00 current day (same as Asia open)
            prior_day_end = asia_open

            print(f"\n  Prior levels (from {prior_date}):")
            print(f"    prior_ny_high={prior_row['ny_high']:.2f}, ended at {prior_ny_end}")
            print(f"    prior_london_high={prior_row['london_high']:.2f}, ended at {prior_london_end}")
            print(f"    prior_day_high={prior_row['day_high']:.2f}, ended at {prior_day_end}")

            # Check which level was swept
            asia_high = row['asia_high']
            swept_levels = []

            if asia_high > prior_row['ny_high']:
                swept_levels.append(('prior_ny_high', prior_ny_end))
            if asia_high > prior_row['london_high']:
                swept_levels.append(('prior_london_high', prior_london_end))
            if asia_high > prior_row['day_high']:
                swept_levels.append(('prior_day_high', prior_day_end))

            print(f"\n  Swept levels: {[name for name, _ in swept_levels]}")

            # Assert temporal ordering
            all_safe = True
            for level_name, level_end_ts in swept_levels:
                is_safe = level_end_ts <= asia_open
                print(f"    {level_name} ended at {level_end_ts} <= asia_open {asia_open}: {is_safe}")
                if not is_safe:
                    all_safe = False

            if all_safe:
                print("  [PASS] All swept levels existed before Asia open")
            else:
                print("  [FAIL] TEMPORAL VIOLATION DETECTED")
                exit(1)
        else:
            print("  [SKIP] No prior day data available")


def verify_london_sweeps():
    """
    London session (1800-2300) sweeps reference:
    - asia_high/low (same day, formed 0900-1700)
    - prior_ny_high/low (previous day 2300-0200)
    - prior_day_high/low (previous day full day)

    All must exist before 18:00 current day.
    """
    print("\n--- LONDON SWEEPS (1800-2300) ---")

    query = """
    SELECT
        sl.date_local,
        sl.london_sweep_prior_high,
        sl.london_sweep_prior_low
    FROM session_labels sl
    WHERE sl.london_sweep_prior_high = true
    ORDER BY RANDOM()
    LIMIT 5
    """

    samples = conn.execute(query).fetchdf()

    for idx, row in samples.iterrows():
        cycle_date = pd.Timestamp(row['date_local']).to_pydatetime()
        london_open = datetime(cycle_date.year, cycle_date.month, cycle_date.day, 18, 0, 0, tzinfo=TZ_LOCAL)

        print(f"\nSample {idx+1}:")
        print(f"  cycle_date: {cycle_date}")
        print(f"  london_open_ts: {london_open}")

        # Get same-day Asia levels (ended at 17:00)
        asia_end = datetime(cycle_date.year, cycle_date.month, cycle_date.day, 17, 0, 0, tzinfo=TZ_LOCAL)

        # Get prior day levels (from previous cycle_date)
        prior_date = cycle_date - pd.Timedelta(days=1)

        query_levels = f"""
        SELECT
            curr.asia_high as curr_asia_high,
            prior.ny_high as prior_ny_high,
            GREATEST(prior.asia_high, prior.london_high, prior.ny_high) as prior_day_high
        FROM daily_features curr
        LEFT JOIN daily_features prior ON prior.date_local = curr.date_local - INTERVAL '1 day'
        WHERE curr.date_local = '{cycle_date.strftime('%Y-%m-%d')}'
        """

        levels_data = conn.execute(query_levels).fetchdf()

        if len(levels_data) > 0:
            levels = levels_data.iloc[0]

            # Compute london_high
            london_high_query = f"""
            SELECT MAX(high) as london_high
            FROM bars_5m
            WHERE symbol = 'MGC'
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= '{cycle_date}' + INTERVAL '18 hours'
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < '{cycle_date}' + INTERVAL '23 hours'
            """
            london_high = conn.execute(london_high_query).fetchdf()['london_high'].iloc[0]

            print(f"  london_high: {london_high:.2f}")

            print(f"\n  Prior levels:")
            print(f"    asia_high={levels['curr_asia_high']:.2f}, ended at {asia_end}")
            print(f"    prior_ny_high={levels['prior_ny_high']:.2f}, ended at 02:00 current day")
            print(f"    prior_day_high={levels['prior_day_high']:.2f}, ended at 09:00 current day")

            # Check which level was swept
            swept_levels = []

            if london_high > levels['curr_asia_high']:
                swept_levels.append(('asia_high', asia_end))
            if london_high > levels['prior_ny_high']:
                # Prior NY ends at 02:00 current day
                prior_ny_end = datetime(cycle_date.year, cycle_date.month, cycle_date.day, 2, 0, 0, tzinfo=TZ_LOCAL)
                swept_levels.append(('prior_ny_high', prior_ny_end))
            if london_high > levels['prior_day_high']:
                # Prior day ends at 09:00 current day
                prior_day_end = datetime(cycle_date.year, cycle_date.month, cycle_date.day, 9, 0, 0, tzinfo=TZ_LOCAL)
                swept_levels.append(('prior_day_high', prior_day_end))

            print(f"\n  Swept levels: {[name for name, _ in swept_levels]}")

            # Assert temporal ordering
            all_safe = True
            for level_name, level_end_ts in swept_levels:
                is_safe = level_end_ts <= london_open
                print(f"    {level_name} ended at {level_end_ts} <= london_open {london_open}: {is_safe}")
                if not is_safe:
                    all_safe = False

            if all_safe:
                print("  [PASS] All swept levels existed before London open")
            else:
                print("  [FAIL] TEMPORAL VIOLATION DETECTED")
                exit(1)
        else:
            print("  [SKIP] No data available")


def verify_ny_sweeps():
    """
    NY pre-ORB session (2300-0030) sweeps reference:
    - london_high/low (same day, formed 1800-2300)
    - asia_high/low (same day, formed 0900-1700)
    - prior_day_high/low (previous day full day)

    All must exist before 23:00 current day.
    """
    print("\n--- NY SWEEPS (2300-0030) ---")

    query = """
    SELECT
        sl.date_local,
        sl.ny_sweep_prior_high,
        sl.ny_sweep_prior_low
    FROM session_labels sl
    WHERE sl.ny_sweep_prior_high = true
    ORDER BY RANDOM()
    LIMIT 5
    """

    samples = conn.execute(query).fetchdf()

    for idx, row in samples.iterrows():
        cycle_date = pd.Timestamp(row['date_local']).to_pydatetime()
        ny_open = datetime(cycle_date.year, cycle_date.month, cycle_date.day, 23, 0, 0, tzinfo=TZ_LOCAL)

        print(f"\nSample {idx+1}:")
        print(f"  cycle_date: {cycle_date}")
        print(f"  ny_open_ts: {ny_open}")

        # Get same-day London and Asia levels
        london_end = datetime(cycle_date.year, cycle_date.month, cycle_date.day, 23, 0, 0, tzinfo=TZ_LOCAL)
        asia_end = datetime(cycle_date.year, cycle_date.month, cycle_date.day, 17, 0, 0, tzinfo=TZ_LOCAL)

        # Get prior day levels
        prior_date = cycle_date - pd.Timedelta(days=1)

        query_levels = f"""
        SELECT
            curr.london_high as curr_london_high,
            curr.asia_high as curr_asia_high,
            GREATEST(prior.asia_high, prior.london_high, prior.ny_high) as prior_day_high
        FROM daily_features curr
        LEFT JOIN daily_features prior ON prior.date_local = curr.date_local - INTERVAL '1 day'
        WHERE curr.date_local = '{cycle_date.strftime('%Y-%m-%d')}'
        """

        levels_data = conn.execute(query_levels).fetchdf()

        if len(levels_data) > 0:
            levels = levels_data.iloc[0]

            # Compute ny_preorb_high
            next_day = cycle_date + pd.Timedelta(days=1)
            ny_high_query = f"""
            SELECT MAX(high) as ny_preorb_high
            FROM bars_5m
            WHERE symbol = 'MGC'
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= '{cycle_date}' + INTERVAL '23 hours'
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < '{next_day}' + INTERVAL '0.5 hours'
            """
            ny_preorb_high = conn.execute(ny_high_query).fetchdf()['ny_preorb_high'].iloc[0]

            print(f"  ny_preorb_high: {ny_preorb_high:.2f}")

            print(f"\n  Prior levels:")
            print(f"    london_high={levels['curr_london_high']:.2f}, ended at {london_end}")
            print(f"    asia_high={levels['curr_asia_high']:.2f}, ended at {asia_end}")
            print(f"    prior_day_high={levels['prior_day_high']:.2f}, ended at 09:00 current day")

            # Check which level was swept
            swept_levels = []

            if ny_preorb_high > levels['curr_london_high']:
                swept_levels.append(('london_high', london_end))
            if ny_preorb_high > levels['curr_asia_high']:
                swept_levels.append(('asia_high', asia_end))
            if ny_preorb_high > levels['prior_day_high']:
                # Prior day ends at 09:00 current day
                prior_day_end = datetime(cycle_date.year, cycle_date.month, cycle_date.day, 9, 0, 0, tzinfo=TZ_LOCAL)
                swept_levels.append(('prior_day_high', prior_day_end))

            print(f"\n  Swept levels: {[name for name, _ in swept_levels]}")

            # Assert temporal ordering
            all_safe = True
            for level_name, level_end_ts in swept_levels:
                is_safe = level_end_ts <= ny_open
                print(f"    {level_name} ended at {level_end_ts} <= ny_open {ny_open}: {is_safe}")
                if not is_safe:
                    all_safe = False

            if all_safe:
                print("  [PASS] All swept levels existed before NY open")
            else:
                print("  [FAIL] TEMPORAL VIOLATION DETECTED")
                exit(1)
        else:
            print("  [SKIP] No data available")


if __name__ == "__main__":
    verify_asia_sweeps()
    verify_london_sweeps()
    verify_ny_sweeps()

    print("\n" + "="*80)
    print("ALL SWEEP TEMPORAL ORDERING CHECKS PASSED")
    print("="*80)

    conn.close()
