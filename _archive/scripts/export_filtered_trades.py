"""
Export High-Confidence Filtered Trades to CSV

Exports trades from the ultra-conservative ruleset:
- 10:00, 11:00, 18:00 ORBs only
- RR=2.0, confirm=1, half-SL, buffer=0
- Using ORB-R logic (1R = ORB range)

Creates:
- filtered_trades_all.csv (all 3 sessions combined)
- filtered_trades_1000.csv (10:00 ORB only)
- filtered_trades_1100.csv (11:00 ORB only)
- filtered_trades_1800.csv (18:00 ORB only)
"""

import duckdb
import pandas as pd
from datetime import datetime

DB_PATH = "gold.db"

def export_trades():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*100)
    print("EXPORTING HIGH-CONFIDENCE FILTERED TRADES")
    print("="*100)
    print()

    # Query all filtered trades
    query = """
        SELECT
            date_local,
            orb,
            direction,
            entry_ts,
            entry_price,
            stop_price,
            target_price,
            stop_ticks,
            orb_range_ticks,
            outcome,
            r_multiple,
            entry_delay_bars,
            mae_r,
            mfe_r,
            close_confirmations,
            rr,
            sl_mode,
            buffer_ticks
        FROM orb_trades_5m_exec_orbr
        WHERE orb IN ('1000', '1100', '1800')
            AND rr = 2.0
            AND close_confirmations = 1
            AND sl_mode = 'half'
            AND buffer_ticks = 0
        ORDER BY date_local, orb
    """

    df_all = con.execute(query).fetchdf()

    # Export all trades
    filename_all = "filtered_trades_all.csv"
    df_all.to_csv(filename_all, index=False)
    print(f"Exported ALL filtered trades: {filename_all}")
    print(f"  Rows: {len(df_all)}")
    print(f"  Columns: {len(df_all.columns)}")
    print()

    # Export by session
    sessions = {
        '1000': '10:00 ORB',
        '1100': '11:00 ORB',
        '1800': '18:00 ORB'
    }

    for orb_code, orb_name in sessions.items():
        df_session = df_all[df_all['orb'] == orb_code].copy()

        filename = f"filtered_trades_{orb_code}.csv"
        df_session.to_csv(filename, index=False)

        # Calculate stats
        total = len(df_session)
        wins = len(df_session[df_session['outcome'] == 'WIN'])
        losses = len(df_session[df_session['outcome'] == 'LOSS'])
        no_trade = len(df_session[df_session['outcome'] == 'NO_TRADE'])
        total_r = df_session['r_multiple'].sum()

        print(f"Exported {orb_name}: {filename}")
        print(f"  Rows: {total} ({wins}W / {losses}L / {no_trade}NT)")
        print(f"  Total R: {total_r:+.1f}R")
        print()

    # Create summary stats file
    summary_data = []

    for orb_code, orb_name in sessions.items():
        df_session = df_all[df_all['orb'] == orb_code]

        traded = df_session[df_session['outcome'].isin(['WIN', 'LOSS'])]

        summary_data.append({
            'session': orb_name,
            'total_trades': len(traded),
            'wins': len(traded[traded['outcome'] == 'WIN']),
            'losses': len(traded[traded['outcome'] == 'LOSS']),
            'win_rate': len(traded[traded['outcome'] == 'WIN']) / len(traded) if len(traded) > 0 else 0,
            'total_r': traded['r_multiple'].sum(),
            'avg_r_per_trade': traded['r_multiple'].mean(),
            'avg_orb_range': traded['orb_range_ticks'].mean(),
            'avg_stop_size': traded['stop_ticks'].mean(),
            'max_orb_range': traded['orb_range_ticks'].max(),
            'min_orb_range': traded['orb_range_ticks'].min(),
        })

    df_summary = pd.DataFrame(summary_data)
    df_summary.to_csv('filtered_trades_summary.csv', index=False)

    print("Exported summary stats: filtered_trades_summary.csv")
    print()

    # Display summary
    print("="*100)
    print("SUMMARY OF EXPORTED TRADES")
    print("="*100)
    print()

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.float_format', '{:.2f}'.format)

    print(df_summary.to_string(index=False))
    print()

    print("="*100)
    print("COLUMN DESCRIPTIONS")
    print("="*100)
    print()
    print("date_local:           Trading day (Brisbane time)")
    print("orb:                  Session code (1000/1100/1800)")
    print("direction:            Trade direction (UP/DOWN)")
    print("entry_ts:             Entry timestamp (Brisbane time)")
    print("entry_price:          Actual entry price")
    print("stop_price:           Stop loss price (ORB midpoint)")
    print("target_price:         Target price (entry ± 2.0 × ORB_range)")
    print("stop_ticks:           Actual stop distance in ticks")
    print("orb_range_ticks:      ORB range (1R definition) in ticks")
    print("outcome:              WIN, LOSS, or NO_TRADE")
    print("r_multiple:           Result in R-multiples (based on ORB range)")
    print("entry_delay_bars:     5m bars after ORB close until entry")
    print("mae_r:                Max Adverse Excursion (vs actual stop)")
    print("mfe_r:                Max Favorable Excursion (vs actual stop)")
    print("close_confirmations:  Entry trigger (1 = single close)")
    print("rr:                   Risk:Reward ratio (2.0)")
    print("sl_mode:              Stop mode (half = midpoint)")
    print("buffer_ticks:         Buffer on stop (0 = exact midpoint)")
    print()

    print("="*100)
    print("FILES CREATED")
    print("="*100)
    print()
    print("1. filtered_trades_all.csv      - All 3 sessions combined")
    print("2. filtered_trades_1000.csv     - 10:00 ORB only")
    print("3. filtered_trades_1100.csv     - 11:00 ORB only")
    print("4. filtered_trades_1800.csv     - 18:00 ORB only")
    print("5. filtered_trades_summary.csv  - Summary statistics")
    print()
    print("="*100)

    con.close()

if __name__ == "__main__":
    export_trades()
