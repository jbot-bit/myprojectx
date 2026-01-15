"""
PHASE 1 — 09:00 ASIA SESSION BEHAVIOR MAPPING

STRICT RULES:
- NO trading logic
- NO impulses, reversals, ORB mid, or pattern assumptions
- Simply classify what price DOES after 09:00 ORB

CLASSIFY:
1. Drive continuation (breaks ORB, continues in that direction)
2. Drive failure (breaks ORB, reverses)
3. Balance → expansion (stays inside, then breaks and goes)
4. Balance → chop (stays inside, continues chopping)
5. Immediate rejection (breaks ORB immediately, reverses immediately)

DETERMINE:
- Is balance strength or weakness at 09:00?
- Is continuation or failure dominant at 09:00?

Output: Descriptive statistics + behavioral conclusions ONLY
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DB_PATH = "gold.db"
SYMBOL = "MGC"
ORB_CODE = "0900"

def classify_post_orb_behavior(con, date_local):
    """
    Classify what price does in 30 minutes after 09:00 ORB.

    NO TRADING LOGIC - pure observation.
    """

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    # 09:00 ORB: 09:00-09:05
    # Observe: 09:05-09:35 (30 minutes post-ORB)
    test_start = datetime.combine(date_obj, datetime.min.time()).replace(hour=9, minute=5)
    test_end = datetime.combine(date_obj, datetime.min.time()).replace(hour=9, minute=35)

    bars_1m = con.execute("""
        SELECT ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local, open, high, low, close
        FROM bars_1m
        WHERE symbol = ? AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, test_start, test_end]).df()

    orb_data = con.execute("""
        SELECT orb_0900_high, orb_0900_low
        FROM daily_features_v2
        WHERE date_local = ? AND instrument = ?
    """, [date_local, SYMBOL]).fetchone()

    if bars_1m.empty or orb_data is None:
        return None

    orb_high, orb_low = orb_data
    if orb_high is None or orb_low is None:
        return None

    bars_1m['ts_local'] = bars_1m['ts_local'].astype(str)

    if len(bars_1m) < 20:
        return None

    # Observation windows
    first_5_bars = bars_1m.head(5)  # 09:05-09:10 (immediate behavior)
    first_10_bars = bars_1m.head(10)  # 09:05-09:15 (early behavior)
    all_bars = bars_1m  # 09:05-09:35 (full observation)

    # Detect ORB breaks
    first_5_high = first_5_bars['high'].max()
    first_5_low = first_5_bars['low'].min()

    broke_up_immediate = (first_5_high > orb_high)
    broke_down_immediate = (first_5_low < orb_low)

    first_10_high = first_10_bars['high'].max()
    first_10_low = first_10_bars['low'].min()

    broke_up_early = (first_10_high > orb_high)
    broke_down_early = (first_10_low < orb_low)

    all_high = all_bars['high'].max()
    all_low = all_bars['low'].min()

    # Calculate travel distances
    up_travel = all_high - orb_high
    down_travel = orb_low - all_low

    # Determine behavior classification
    behavior = None
    details = {}

    # 1. IMMEDIATE REJECTION (breaks in first 5 bars, reverses by bar 15)
    if broke_up_immediate or broke_down_immediate:
        if broke_up_immediate:
            # Check if reversed back below ORB high by bar 15
            reversed = (bars_1m.iloc[:15]['low'].min() < orb_high) if len(bars_1m) >= 15 else False
            if reversed:
                behavior = 'IMMEDIATE_REJECTION'
                details['direction'] = 'UP_REJECTED'

        if broke_down_immediate and behavior is None:
            reversed = (bars_1m.iloc[:15]['high'].max() > orb_low) if len(bars_1m) >= 15 else False
            if reversed:
                behavior = 'IMMEDIATE_REJECTION'
                details['direction'] = 'DOWN_REJECTED'

    # 2. DRIVE CONTINUATION (breaks early, continues traveling)
    if behavior is None and (broke_up_early or broke_down_early):
        if broke_up_early:
            # Check if continued UP (made significant travel)
            if up_travel > 5.0:  # Traveled > 5 ticks beyond ORB
                behavior = 'DRIVE_CONTINUATION'
                details['direction'] = 'UP'
                details['travel'] = up_travel

        if broke_down_early and behavior is None:
            if down_travel > 5.0:
                behavior = 'DRIVE_CONTINUATION'
                details['direction'] = 'DOWN'
                details['travel'] = down_travel

    # 3. DRIVE FAILURE (breaks early, fails to continue, reverses)
    if behavior is None and (broke_up_early or broke_down_early):
        if broke_up_early:
            # Failed if didn't travel much AND reversed
            if up_travel < 5.0 and down_travel > up_travel:
                behavior = 'DRIVE_FAILURE'
                details['direction'] = 'UP_FAILED'
                details['up_travel'] = up_travel
                details['down_travel'] = down_travel

        if broke_down_early and behavior is None:
            if down_travel < 5.0 and up_travel > down_travel:
                behavior = 'DRIVE_FAILURE'
                details['direction'] = 'DOWN_FAILED'
                details['up_travel'] = up_travel
                details['down_travel'] = down_travel

    # 4. BALANCE → EXPANSION (stayed inside first 10 bars, then broke and traveled)
    if behavior is None and not broke_up_early and not broke_down_early:
        # Stayed inside for first 10 bars
        if up_travel > 5.0 or down_travel > 5.0:
            behavior = 'BALANCE_EXPANSION'
            if up_travel > down_travel:
                details['direction'] = 'UP'
                details['travel'] = up_travel
            else:
                details['direction'] = 'DOWN'
                details['travel'] = down_travel

    # 5. BALANCE → CHOP (stayed inside, continued chopping)
    if behavior is None:
        # Never broke significantly or stayed rangebound
        behavior = 'BALANCE_CHOP'
        details['up_travel'] = up_travel
        details['down_travel'] = down_travel

    return {
        'date': str(date_local).split()[0],
        'behavior': behavior,
        'details': details,
        'orb_high': orb_high,
        'orb_low': orb_low,
        'all_high': all_high,
        'all_low': all_low
    }


def analyze_baseline_breakout(con):
    """Baseline 09:00 breakout performance."""

    print("="*80)
    print("BASELINE 09:00 BREAKOUT ANALYSIS")
    print("="*80)
    print()

    baseline = con.execute("""
        SELECT
            COUNT(*) as n_trades,
            AVG(r_multiple) as avg_r,
            SUM(r_multiple) as total_r,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
        FROM orb_trades_1m_exec_nofilters
        WHERE orb = '0900'
            AND close_confirmations = 1
            AND rr = 1.0
    """).fetchone()

    n_trades, avg_r, total_r, win_rate = baseline

    print(f"Total trades: {n_trades}")
    print(f"Avg R: {avg_r:+.3f}R")
    print(f"Total R: {total_r:+.2f}R")
    print(f"Win rate: {win_rate:.1f}%")
    print()

    # ORB size distribution
    orb_sizes = con.execute("""
        SELECT orb_0900_size
        FROM daily_features_v2
        WHERE orb_0900_size IS NOT NULL AND instrument = 'MGC'
    """).df()

    if not orb_sizes.empty:
        print("ORB SIZE DISTRIBUTION:")
        print(f"  Min: {orb_sizes['orb_0900_size'].min():.1f} ticks")
        print(f"  Median: {orb_sizes['orb_0900_size'].median():.1f} ticks")
        print(f"  Mean: {orb_sizes['orb_0900_size'].mean():.1f} ticks")
        print(f"  Max: {orb_sizes['orb_0900_size'].max():.1f} ticks")
        print()


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("\n" + "*"*80)
    print("PHASE 1 — 09:00 ASIA SESSION BEHAVIOR MAPPING")
    print("*"*80 + "\n")

    print("REMINDER: NO TRADING LOGIC - PURE OBSERVATION ONLY")
    print()

    # Baseline analysis
    analyze_baseline_breakout(con)

    # Get all 09:00 dates
    dates = con.execute("""
        SELECT date_local
        FROM daily_features_v2
        WHERE orb_0900_high IS NOT NULL
            AND instrument = 'MGC'
        ORDER BY date_local
    """).df()

    print(f"Total 09:00 ORB dates: {len(dates)}")
    print()

    # Classify behaviors
    print("="*80)
    print("CLASSIFYING POST-ORB BEHAVIORS")
    print("="*80)
    print()

    behaviors = []

    for date in dates['date_local']:
        result = classify_post_orb_behavior(con, date)
        if result:
            behaviors.append(result)

    df = pd.DataFrame(behaviors)

    # Behavior distribution
    print("BEHAVIOR DISTRIBUTION:")
    print("-"*80)
    behavior_counts = df['behavior'].value_counts()

    for behavior, count in behavior_counts.items():
        pct = count / len(df) * 100
        print(f"{behavior:<25} {count:>4} ({pct:>5.1f}%)")

    print()

    # Analyze each behavior type
    print("="*80)
    print("DETAILED BEHAVIOR ANALYSIS")
    print("="*80)
    print()

    # 1. DRIVE CONTINUATION
    drive_cont = df[df['behavior'] == 'DRIVE_CONTINUATION']
    if len(drive_cont) > 0:
        print(f"1. DRIVE CONTINUATION: {len(drive_cont)} instances ({len(drive_cont)/len(df)*100:.1f}%)")

        # Direction split
        directions = drive_cont['details'].apply(lambda x: x.get('direction', 'UNKNOWN'))
        print(f"   - UP: {(directions == 'UP').sum()}")
        print(f"   - DOWN: {(directions == 'DOWN').sum()}")

        # Average travel
        travels = drive_cont['details'].apply(lambda x: x.get('travel', 0))
        print(f"   - Avg travel: {travels.mean():.1f} ticks")
        print()

    # 2. DRIVE FAILURE
    drive_fail = df[df['behavior'] == 'DRIVE_FAILURE']
    if len(drive_fail) > 0:
        print(f"2. DRIVE FAILURE: {len(drive_fail)} instances ({len(drive_fail)/len(df)*100:.1f}%)")

        directions = drive_fail['details'].apply(lambda x: x.get('direction', 'UNKNOWN'))
        print(f"   - UP_FAILED: {(directions == 'UP_FAILED').sum()}")
        print(f"   - DOWN_FAILED: {(directions == 'DOWN_FAILED').sum()}")
        print()

    # 3. BALANCE -> EXPANSION
    balance_exp = df[df['behavior'] == 'BALANCE_EXPANSION']
    if len(balance_exp) > 0:
        print(f"3. BALANCE -> EXPANSION: {len(balance_exp)} instances ({len(balance_exp)/len(df)*100:.1f}%)")

        directions = balance_exp['details'].apply(lambda x: x.get('direction', 'UNKNOWN'))
        print(f"   - UP: {(directions == 'UP').sum()}")
        print(f"   - DOWN: {(directions == 'DOWN').sum()}")

        travels = balance_exp['details'].apply(lambda x: x.get('travel', 0))
        print(f"   - Avg travel: {travels.mean():.1f} ticks")
        print()

    # 4. BALANCE -> CHOP
    balance_chop = df[df['behavior'] == 'BALANCE_CHOP']
    if len(balance_chop) > 0:
        print(f"4. BALANCE -> CHOP: {len(balance_chop)} instances ({len(balance_chop)/len(df)*100:.1f}%)")
        print()

    # 5. IMMEDIATE REJECTION
    imm_rej = df[df['behavior'] == 'IMMEDIATE_REJECTION']
    if len(imm_rej) > 0:
        print(f"5. IMMEDIATE REJECTION: {len(imm_rej)} instances ({len(imm_rej)/len(df)*100:.1f}%)")

        directions = imm_rej['details'].apply(lambda x: x.get('direction', 'UNKNOWN'))
        print(f"   - UP_REJECTED: {(directions == 'UP_REJECTED').sum()}")
        print(f"   - DOWN_REJECTED: {(directions == 'DOWN_REJECTED').sum()}")
        print()

    # Key findings
    print("="*80)
    print("KEY BEHAVIORAL FINDINGS")
    print("="*80)
    print()

    # Is balance strength or weakness?
    balance_total = len(balance_exp) + len(balance_chop)
    if balance_total > 0:
        balance_expansion_pct = len(balance_exp) / balance_total * 100
        print(f"BALANCE BEHAVIOR:")
        print(f"  When price stays inside ORB first 10min:")
        print(f"    - Expansion: {len(balance_exp)}/{balance_total} ({balance_expansion_pct:.1f}%)")
        print(f"    - Chop: {len(balance_chop)}/{balance_total} ({100-balance_expansion_pct:.1f}%)")

        if balance_expansion_pct > 60:
            print(f"  VERDICT: Balance is STRENGTH (expansion likely)")
        elif balance_expansion_pct < 40:
            print(f"  VERDICT: Balance is WEAKNESS (chop likely)")
        else:
            print(f"  VERDICT: Balance is NEUTRAL (mixed)")
        print()

    # Is continuation or failure dominant?
    drive_total = len(drive_cont) + len(drive_fail)
    if drive_total > 0:
        continuation_pct = len(drive_cont) / drive_total * 100
        print(f"DRIVE BEHAVIOR:")
        print(f"  When price breaks ORB early:")
        print(f"    - Continuation: {len(drive_cont)}/{drive_total} ({continuation_pct:.1f}%)")
        print(f"    - Failure: {len(drive_fail)}/{drive_total} ({100-continuation_pct:.1f}%)")

        if continuation_pct > 60:
            print(f"  VERDICT: CONTINUATION dominates (breakouts work)")
        elif continuation_pct < 40:
            print(f"  VERDICT: FAILURE dominates (breakouts fade)")
        else:
            print(f"  VERDICT: MIXED (no clear edge)")
        print()

    print("="*80)
    print("PHASE 1 COMPLETE - AWAITING APPROVAL FOR PHASE 2")
    print("="*80)
    print()
    print("DO NOT PROPOSE ENTRIES YET.")
    print()

    con.close()


if __name__ == '__main__':
    main()
