"""
Prepare manual replay data for 0030 strongest state.

State: NORMAL + D_MED + HIGH close + HIGH impulse
Expected: 70% UP-favored, +44.5 tick median tail skew

Purpose: Pull 10-15 dates for manual chart replay validation.
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "gold.db"
SYMBOL = "MGC"

# Strongest state definition
STATE_FILTERS = {
    'orb_code': '0030',
    'range_bucket': 'NORMAL',
    'disp_bucket': 'D_MED',
    'close_pos_bucket': 'HIGH',
    'impulse_bucket': 'HIGH'
}

def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*80)
    print("MANUAL REPLAY PREPARATION - 0030 STRONGEST STATE")
    print("="*80)
    print()

    # STEP 1: Get all dates for this state
    print("STEP 1: Query dates matching state definition")
    print("-"*80)

    query = """
        SELECT
            date_local,
            pre_orb_range,
            pre_orb_disp,
            pre_orb_close_pos,
            impulse_score,
            range_bucket,
            disp_bucket,
            close_pos_bucket,
            impulse_bucket
        FROM day_state_features
        WHERE orb_code = ?
            AND range_bucket = ?
            AND disp_bucket = ?
            AND close_pos_bucket = ?
            AND impulse_bucket = ?
        ORDER BY date_local DESC
    """

    dates_df = con.execute(query, [
        STATE_FILTERS['orb_code'],
        STATE_FILTERS['range_bucket'],
        STATE_FILTERS['disp_bucket'],
        STATE_FILTERS['close_pos_bucket'],
        STATE_FILTERS['impulse_bucket']
    ]).df()

    print(f"State matched: {len(dates_df)} dates")
    print()

    if len(dates_df) == 0:
        print("[ERROR] No dates found for this state. Check state definition.")
        con.close()
        return

    # Select 15 most recent dates for replay
    replay_dates = dates_df.head(15)['date_local'].tolist()

    print(f"Selected {len(replay_dates)} most recent dates for manual replay:")
    for i, d in enumerate(replay_dates, 1):
        print(f"  {i:2d}. {d}")
    print()

    # STEP 2: Extract bar data for each date
    print("STEP 2: Extract 1m and 5m bar data")
    print("-"*80)

    all_replay_data = []

    for date_local in replay_dates:
        # Handle both date and datetime objects
        if isinstance(date_local, str):
            date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
        elif hasattr(date_local, 'date'):
            date_obj = date_local.date()
        else:
            date_obj = date_local

        # ORB window: 00:30-00:35 on D+1
        # Replay window: 00:15-01:30 on D+1 (15min before ORB + 60min after)
        replay_start = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=15)
        replay_end = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=1, minute=30)

        # Get 1m bars
        bars_1m = con.execute("""
            SELECT
                ts_utc,
                ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local,
                open, high, low, close, volume
            FROM bars_1m
            WHERE symbol = ?
                AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
                AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
            ORDER BY ts_utc
        """, [SYMBOL, replay_start, replay_end]).df()

        # Get 5m bars
        bars_5m = con.execute("""
            SELECT
                ts_utc,
                ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local,
                open, high, low, close, volume
            FROM bars_5m
            WHERE symbol = ?
                AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
                AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
            ORDER BY ts_utc
        """, [SYMBOL, replay_start, replay_end]).df()

        # Get ORB boundaries
        orb_data = con.execute("""
            SELECT orb_0030_high, orb_0030_low, orb_0030_size
            FROM daily_features
            WHERE date_local = ? AND instrument = ?
        """, [date_local, SYMBOL]).fetchone()

        if bars_1m.empty or bars_5m.empty or orb_data is None:
            print(f"  [SKIP] {date_local} - Insufficient data")
            continue

        orb_high, orb_low, orb_size = orb_data

        # Skip if any ORB value is None
        if orb_high is None or orb_low is None or orb_size is None:
            print(f"  [SKIP] {date_local} - ORB data is NULL")
            continue

        all_replay_data.append({
            'date_local': date_local,
            'bars_1m': bars_1m,
            'bars_5m': bars_5m,
            'orb_high': orb_high,
            'orb_low': orb_low,
            'orb_size': orb_size
        })

        print(f"  [OK] {date_local} - {len(bars_1m)} 1m bars, {len(bars_5m)} 5m bars, ORB={orb_size:.1f} ticks")

    print()
    print(f"Total dates ready for replay: {len(all_replay_data)}")
    print()

    # STEP 3: Create replay analysis template
    print("STEP 3: Generate replay analysis template")
    print("-"*80)

    # Save detailed bar data to CSV for each date
    for replay in all_replay_data:
        # Format date as YYYYMMDD (extract date only)
        date_local = replay['date_local']
        if isinstance(date_local, str):
            date_str = date_local.split()[0].replace('-', '')
        elif hasattr(date_local, 'date'):
            date_str = date_local.date().strftime('%Y%m%d')
        else:
            date_str = date_local.strftime('%Y%m%d')

        # Save 1m bars
        bars_1m_file = f"replay_0030_{date_str}_1m.csv"
        replay['bars_1m'].to_csv(bars_1m_file, index=False)

        # Save 5m bars
        bars_5m_file = f"replay_0030_{date_str}_5m.csv"
        replay['bars_5m'].to_csv(bars_5m_file, index=False)

    print(f"Saved {len(all_replay_data) * 2} CSV files (1m + 5m for each date)")
    print()

    # STEP 4: Create analysis template
    print("STEP 4: Create manual analysis template")
    print("-"*80)

    template_rows = []
    for replay in all_replay_data:
        template_rows.append({
            'date_local': replay['date_local'],
            'orb_high': replay['orb_high'],
            'orb_low': replay['orb_low'],
            'orb_size_ticks': replay['orb_size'],
            'invalidation_check': '',  # Manual: YES/NO (strong DOWN drive?)
            'reaction_pattern': '',    # Manual: A/B/C/NONE
            'entry_triggered': '',     # Manual: YES/NO (5m reclaim high?)
            'entry_price': '',         # Manual: price if triggered
            'stop_price': '',          # Manual: structural stop
            'outcome_60m': '',         # Manual: WIN/LOSS/TIMEOUT
            'r_multiple': '',          # Manual: estimated R
            'notes': ''                # Manual: observations
        })

    template_df = pd.DataFrame(template_rows)
    template_file = "replay_0030_analysis_template.csv"
    template_df.to_csv(template_file, index=False)

    print(f"Created analysis template: {template_file}")
    print()

    # STEP 5: Print instructions
    print("="*80)
    print("MANUAL REPLAY INSTRUCTIONS")
    print("="*80)
    print()
    print("For each date, review the 1m and 5m bar CSVs:")
    print()
    print("1. INVALIDATION CHECK (00:30-00:40):")
    print("   - Is there strong DOWN drive with clean expansion?")
    print("   - If YES -> mark 'YES' in invalidation_check, skip to next date")
    print("   - If NO -> proceed to reaction analysis")
    print()
    print("2. REACTION PATTERN (00:30-00:45):")
    print("   - A) Absorption/Stall: Initial push fails, range compresses, wicks grow")
    print("   - B) Fake Downside: Quick drop, no follow-through, fast reclaim")
    print("   - C) Delayed Lift: Chop 10-20 min, THEN expansion UP")
    print("   - NONE: No clear reaction pattern visible")
    print()
    print("3. ENTRY TRIGGER:")
    print("   - Did a 5m bar close ABOVE the 5m range high during reaction?")
    print("   - If YES -> mark entry_triggered='YES', record price")
    print("   - If NO -> mark entry_triggered='NO'")
    print()
    print("4. STOP PLACEMENT:")
    print("   - Where is the structural low? (reaction base, fake-out extreme, etc.)")
    print("   - Record stop_price")
    print()
    print("5. OUTCOME (60-minute window from entry OR timeout):")
    print("   - WIN: Hit +20-30 ticks OR clean expansion before stop")
    print("   - LOSS: Hit stop")
    print("   - TIMEOUT: 60 minutes expired, no clear outcome")
    print()
    print("6. CALCULATE R-MULTIPLE:")
    print("   - R = (entry_price - stop_price)")
    print("   - If WIN: estimate profit in ticks, divide by R")
    print("   - If LOSS: -1R or worse (if slippage)")
    print()
    print("="*80)
    print("ANALYSIS TEMPLATE COLUMNS")
    print("="*80)
    print()
    print("  date_local          - Trading day")
    print("  orb_high/low        - ORB boundaries (reference only)")
    print("  orb_size_ticks      - ORB range size")
    print("  invalidation_check  - YES/NO (strong DOWN drive?)")
    print("  reaction_pattern    - A/B/C/NONE")
    print("  entry_triggered     - YES/NO (5m reclaim?)")
    print("  entry_price         - Entry level if triggered")
    print("  stop_price          - Structural stop")
    print("  outcome_60m         - WIN/LOSS/TIMEOUT")
    print("  r_multiple          - Estimated R (positive for wins, negative for losses)")
    print("  notes               - Free-form observations")
    print()
    print("="*80)
    print("NEXT STEPS")
    print("="*80)
    print()
    print("1. Open each date's CSV files in Excel or text editor")
    print("2. Mentally replay the price action (or plot if needed)")
    print("3. Fill in the analysis template")
    print("4. When complete, analyze results:")
    print("   - How many show reaction patterns? (X/15)")
    print("   - How many trigger entry? (X/15)")
    print("   - How many win? (X/triggered)")
    print("   - Average R-multiple?")
    print("   - Is there positive expectancy?")
    print()
    print("5. Decision: Worth coding full backtest? Or kill state?")
    print()

    con.close()

if __name__ == '__main__':
    main()
