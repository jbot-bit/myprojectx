"""
LOSS CLUSTERING & CORRELATION ANALYSIS

Quantifies:
1. Same-day ORB loss correlation (how often multiple ORBs lose on same day)
2. Max losing streak in CALENDAR DAYS (not just trade count)
3. Max weekly drawdown (R)
4. Frequency of -2R, -3R, -6R daily loss events

Critical for understanding real-world risk.
"""

import duckdb
import pandas as pd
from datetime import timedelta

DB_PATH = "gold.db"
TICK_SIZE = 0.10

def get_all_trades(con, orb_params):
    """
    Get all trades for all ORBs using their optimal parameters.
    Returns DataFrame with date, orb, outcome, R
    """
    all_trades = []

    for _, params in orb_params.iterrows():
        orb = params['orb']
        rr = params['optimal_rr']
        sl_mode = params['optimal_sl']

        # Standard backtest logic (can be replaced with worst-case later)
        query = f"""
        SELECT
            date_local,
            orb_{orb}_high as orb_high,
            orb_{orb}_low as orb_low,
            orb_{orb}_break_dir as break_dir
        FROM daily_features_v2
        WHERE instrument = 'MGC'
            AND orb_{orb}_break_dir IS NOT NULL
        ORDER BY date_local
        """

        df_setups = con.execute(query).df()

        if len(df_setups) == 0:
            continue

        dates_str = "', '".join(df_setups['date_local'].astype(str).unique())

        hour_map = {'0900': 9, '1000': 10, '1100': 11, '1800': 18, '2300': 23, '0030': 0}
        orb_hour = hour_map[orb]

        if orb in ['0900', '1000', '1100']:
            end_hour = 18
        elif orb == '1800':
            end_hour = 23
        elif orb in ['2300', '0030']:
            end_hour = 2

        if orb in ['2300', '0030']:
            query_bars = f"""
            SELECT
                DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') as date_local,
                ts_utc,
                high,
                low,
                close
            FROM bars_5m
            WHERE symbol = 'MGC'
                AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') IN ('{dates_str}')
                AND (
                    EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') >= {orb_hour}
                    OR EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < {end_hour}
                )
            ORDER BY ts_utc
            """
        else:
            query_bars = f"""
            SELECT
                DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') as date_local,
                ts_utc,
                high,
                low,
                close
            FROM bars_5m
            WHERE symbol = 'MGC'
                AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') IN ('{dates_str}')
                AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') >= {orb_hour}
                AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < {end_hour}
            ORDER BY ts_utc
            """

        bars = con.execute(query_bars).df()

        # Simulate each trade
        for _, setup in df_setups.iterrows():
            date = setup['date_local']
            orb_high = setup['orb_high']
            orb_low = setup['orb_low']
            direction = setup['break_dir']
            orb_midpoint = (orb_high + orb_low) / 2

            if direction == 'UP':
                entry = orb_high
                if sl_mode == 'HALF':
                    stop = orb_midpoint
                else:
                    stop = orb_low
                risk = entry - stop
                target = entry + rr * risk
            else:
                entry = orb_low
                if sl_mode == 'HALF':
                    stop = orb_midpoint
                else:
                    stop = orb_high
                risk = stop - entry
                target = entry - rr * risk

            trade_bars = bars[bars['date_local'] == date].sort_values('ts_utc')

            if len(trade_bars) == 0:
                continue

            # Find entry
            entry_bar_idx = None
            for idx, bar in trade_bars.iterrows():
                if direction == 'UP' and bar['close'] > orb_high:
                    entry_bar_idx = idx
                    break
                elif direction == 'DOWN' and bar['close'] < orb_low:
                    entry_bar_idx = idx
                    break

            if entry_bar_idx is None:
                continue

            # Simulate (worst-case)
            entry_bars = trade_bars.loc[entry_bar_idx:].copy()

            outcome = None
            r_multiple = None

            for idx, bar in entry_bars.iterrows():
                if direction == 'UP':
                    stop_hit = bar['low'] <= stop
                    target_hit = bar['high'] >= target

                    if stop_hit and target_hit:
                        outcome = 'LOSS'
                        r_multiple = -1.0
                        break
                    elif stop_hit:
                        outcome = 'LOSS'
                        r_multiple = -1.0
                        break
                    elif target_hit:
                        outcome = 'WIN'
                        r_multiple = rr
                        break
                else:
                    stop_hit = bar['high'] >= stop
                    target_hit = bar['low'] <= target

                    if stop_hit and target_hit:
                        outcome = 'LOSS'
                        r_multiple = -1.0
                        break
                    elif stop_hit:
                        outcome = 'LOSS'
                        r_multiple = -1.0
                        break
                    elif target_hit:
                        outcome = 'WIN'
                        r_multiple = rr
                        break

            if outcome in ['WIN', 'LOSS']:
                all_trades.append({
                    'date': date,
                    'orb': orb,
                    'outcome': outcome,
                    'r_multiple': r_multiple
                })

    return pd.DataFrame(all_trades)

def analyze_clustering(trades_df):
    """
    Analyze loss clustering and correlation.
    """
    print("=" * 80)
    print("LOSS CLUSTERING ANALYSIS")
    print("=" * 80)
    print()

    # 1. Same-day multi-ORB loss correlation
    print("1. SAME-DAY MULTI-ORB LOSSES:")
    print("-" * 80)

    daily_summary = trades_df.groupby('date').agg({
        'r_multiple': 'sum',
        'orb': 'count'
    }).rename(columns={'orb': 'num_trades', 'r_multiple': 'daily_r'})

    # Count days by loss severity
    minus_1r_days = len(daily_summary[daily_summary['daily_r'] == -1.0])
    minus_2r_days = len(daily_summary[daily_summary['daily_r'] == -2.0])
    minus_3r_days = len(daily_summary[daily_summary['daily_r'] == -3.0])
    minus_4r_days = len(daily_summary[daily_summary['daily_r'] <= -4.0])
    minus_6r_days = len(daily_summary[daily_summary['daily_r'] <= -6.0])

    total_days = len(daily_summary)

    print(f"Total trading days: {total_days}")
    print()
    print(f"Daily loss distribution:")
    print(f"  -1R days: {minus_1r_days} ({minus_1r_days/total_days*100:.1f}%)")
    print(f"  -2R days: {minus_2r_days} ({minus_2r_days/total_days*100:.1f}%)")
    print(f"  -3R days: {minus_3r_days} ({minus_3r_days/total_days*100:.1f}%)")
    print(f"  -4R+ days: {minus_4r_days} ({minus_4r_days/total_days*100:.1f}%)")
    print(f"  -6R+ days: {minus_6r_days} ({minus_6r_days/total_days*100:.1f}%)")
    print()

    # Worst daily loss
    worst_day = daily_summary.loc[daily_summary['daily_r'].idxmin()]
    print(f"Worst single day: {worst_day.name} with {worst_day['daily_r']:.1f}R ({int(worst_day['num_trades'])} trades)")
    print()

    # 2. ORB-specific loss correlation
    print("2. ORB-TO-ORB LOSS CORRELATION:")
    print("-" * 80)

    # Pivot to wide format (date x orb)
    pivot = trades_df.pivot(index='date', columns='orb', values='r_multiple')

    # Calculate correlation matrix for losses only
    loss_pivot = pivot.copy()
    loss_pivot[loss_pivot > 0] = 0  # Set wins to 0
    loss_pivot[loss_pivot < 0] = 1  # Set losses to 1

    corr_matrix = loss_pivot.corr()

    print("Loss correlation matrix:")
    print(corr_matrix.to_string())
    print()

    # 3. Calendar-day losing streaks
    print("3. CALENDAR-DAY LOSING STREAKS:")
    print("-" * 80)

    daily_summary_sorted = daily_summary.sort_index()

    max_streak = 0
    current_streak = 0
    current_streak_start = None
    max_streak_start = None
    max_streak_end = None

    for date, row in daily_summary_sorted.iterrows():
        if row['daily_r'] < 0:
            if current_streak == 0:
                current_streak_start = date
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
                max_streak_start = current_streak_start
                max_streak_end = date
        else:
            current_streak = 0

    print(f"Max calendar-day losing streak: {max_streak} days")
    if max_streak > 0:
        print(f"  Period: {max_streak_start} to {max_streak_end}")
        streak_r = daily_summary_sorted.loc[max_streak_start:max_streak_end, 'daily_r'].sum()
        print(f"  Total R lost: {streak_r:.1f}R")
    print()

    # 4. Weekly drawdown
    print("4. WEEKLY DRAWDOWN:")
    print("-" * 80)

    # Convert date to datetime for week grouping
    daily_summary_sorted.index = pd.to_datetime(daily_summary_sorted.index)
    weekly = daily_summary_sorted.groupby(pd.Grouper(freq='W'))['daily_r'].sum()

    worst_week = weekly.min()
    worst_week_date = weekly.idxmin()

    print(f"Worst weekly drawdown: {worst_week:.1f}R")
    print(f"  Week ending: {worst_week_date.strftime('%Y-%m-%d')}")
    print()

    # Distribution of weekly returns
    print("Weekly return distribution:")
    print(f"  Mean: {weekly.mean():.1f}R")
    print(f"  Median: {weekly.median():.1f}R")
    print(f"  Std Dev: {weekly.std():.1f}R")
    print(f"  Min: {weekly.min():.1f}R")
    print(f"  Max: {weekly.max():.1f}R")
    print()

    # Count weeks with losses
    losing_weeks = len(weekly[weekly < 0])
    total_weeks = len(weekly)
    print(f"Losing weeks: {losing_weeks} / {total_weeks} ({losing_weeks/total_weeks*100:.1f}%)")
    print()

    return {
        'max_daily_loss': worst_day['daily_r'],
        'max_calendar_losing_streak': max_streak,
        'max_weekly_drawdown': worst_week,
        'minus_2r_days': minus_2r_days,
        'minus_3r_days': minus_3r_days,
        'minus_6r_days': minus_6r_days,
        'losing_weeks_pct': losing_weeks/total_weeks*100
    }

def main():
    print("=" * 80)
    print("LOSS CLUSTERING & CORRELATION ANALYSIS")
    print("=" * 80)
    print()

    con = duckdb.connect(DB_PATH, read_only=True)

    # Load optimal parameters
    try:
        orb_params = pd.read_csv('worst_case_parameters.csv', dtype={'orb': str})
        print("Using optimal parameters from worst-case test")
    except FileNotFoundError:
        print("Warning: worst_case_parameters.csv not found, using canonical")
        orb_params = pd.read_csv('canonical_session_parameters.csv', dtype={'orb': str})

    print()
    print("Collecting all trades...")

    trades_df = get_all_trades(con, orb_params)

    con.close()

    if len(trades_df) == 0:
        print("ERROR: No trades found")
        return

    print(f"Collected {len(trades_df)} trades across {len(trades_df['date'].unique())} days")
    print()

    # Analyze
    metrics = analyze_clustering(trades_df)

    # Save trades for further analysis
    trades_df.to_csv('all_trades_clustering.csv', index=False)

    print("=" * 80)
    print("RISK ASSESSMENT")
    print("=" * 80)
    print()

    print("CRITICAL METRICS:")
    print(f"  Max daily loss: {metrics['max_daily_loss']:.1f}R")
    print(f"  Max calendar losing streak: {metrics['max_calendar_losing_streak']} days")
    print(f"  Max weekly drawdown: {metrics['max_weekly_drawdown']:.1f}R")
    print()

    print("PROP ACCOUNT COMPATIBILITY:")
    if abs(metrics['max_daily_loss']) <= 3:
        print(f"  -3R daily limit: COMPATIBLE (worst day: {metrics['max_daily_loss']:.1f}R)")
    else:
        print(f"  -3R daily limit: RISK (worst day: {metrics['max_daily_loss']:.1f}R)")

    if abs(metrics['max_daily_loss']) <= 2:
        print(f"  -2R daily limit: COMPATIBLE (worst day: {metrics['max_daily_loss']:.1f}R)")
    else:
        print(f"  -2R daily limit: RISK (worst day: {metrics['max_daily_loss']:.1f}R)")

    print()

    print("PSYCHOLOGICAL TOLERANCE:")
    if metrics['max_calendar_losing_streak'] <= 5:
        print(f"  Max losing streak: MANAGEABLE ({metrics['max_calendar_losing_streak']} days)")
    elif metrics['max_calendar_losing_streak'] <= 10:
        print(f"  Max losing streak: CHALLENGING ({metrics['max_calendar_losing_streak']} days)")
    else:
        print(f"  Max losing streak: SEVERE ({metrics['max_calendar_losing_streak']} days)")

    if abs(metrics['max_weekly_drawdown']) <= 10:
        print(f"  Max weekly DD: TOLERABLE ({metrics['max_weekly_drawdown']:.1f}R)")
    elif abs(metrics['max_weekly_drawdown']) <= 20:
        print(f"  Max weekly DD: SIGNIFICANT ({metrics['max_weekly_drawdown']:.1f}R)")
    else:
        print(f"  Max weekly DD: SEVERE ({metrics['max_weekly_drawdown']:.1f}R)")

    print()

    print("FREQUENCY OF CLUSTERED LOSSES:")
    print(f"  -2R days: {metrics['minus_2r_days']} (expect ~{metrics['minus_2r_days']/2:.0f} per year)")
    print(f"  -3R days: {metrics['minus_3r_days']} (expect ~{metrics['minus_3r_days']/2:.0f} per year)")
    if metrics['minus_6r_days'] > 0:
        print(f"  -6R days: {metrics['minus_6r_days']} (expect ~{metrics['minus_6r_days']/2:.0f} per year) [EXTREME]")

    print()
    print("Files saved: all_trades_clustering.csv")
    print()

if __name__ == "__main__":
    main()
