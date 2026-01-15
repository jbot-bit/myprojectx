"""
Compare Winners: Filtered vs No-Filters

Shows exact impact of filters on your winning configs.
Simple before/after comparison.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def compare():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*100)
    print("FILTER IMPACT ANALYSIS - WINNERS ONLY")
    print("="*100)
    print()

    # Winner configs to compare
    winners = [
        ("1000", 3.0, 2, "", 0, "10:00 ORB (5m exec)"),
        ("1800", 2.0, 1, "half", 0, "18:00 ORB (half-SL)"),
        ("1100", 3.0, 1, "half", 0, "11:00 ORB (half-SL)"),
        ("0030", 1.5, 2, "half", 0, "00:30 ORB (half-SL)"),
        ("0900", 3.0, 2, "", 0, "09:00 ORB (5m exec)"),
    ]

    total_filtered_r = 0
    total_nofilter_r = 0

    for orb, rr, confirm, sl_mode, buffer, name in winners:
        print(f"{name}")
        print("-"*100)

        # Get filtered results
        filtered = con.execute("""
            SELECT
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
                SUM(r_multiple) as total_r,
                AVG(r_multiple) as avg_r,
                AVG(stop_ticks) as avg_stop_ticks
            FROM orb_trades_5m_exec
            WHERE orb = ?
              AND rr = ?
              AND close_confirmations = ?
              AND sl_mode = ?
              AND buffer_ticks = ?
        """, [orb, rr, confirm, sl_mode, buffer]).fetchone()

        # Get no-filter results
        nofilter = con.execute("""
            SELECT
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
                SUM(r_multiple) as total_r,
                AVG(r_multiple) as avg_r,
                AVG(stop_ticks) as avg_stop_ticks
            FROM orb_trades_5m_exec_nofilters
            WHERE orb = ?
              AND rr = ?
              AND close_confirmations = ?
              AND sl_mode = ?
              AND buffer_ticks = ?
        """, [orb, rr, confirm, sl_mode, buffer]).fetchone()

        if not filtered or not nofilter:
            print("  Data missing - run test_winners_nofilters.py first")
            print()
            continue

        f_trades, f_wr, f_r, f_avg_r, f_avg_stop = filtered
        n_trades, n_wr, n_r, n_avg_r, n_avg_stop = nofilter

        print(f"  WITH FILTERS:")
        print(f"    Trades: {f_trades} | Win Rate: {f_wr:.1%} | Total R: {f_r:+.1f} | Avg Stop: {f_avg_stop:.1f} ticks")

        print(f"  NO FILTERS:")
        print(f"    Trades: {n_trades} | Win Rate: {n_wr:.1%} | Total R: {n_r:+.1f} | Avg Stop: {n_avg_stop:.1f} ticks")

        # Calculate impact
        trade_diff = n_trades - f_trades
        r_diff = n_r - f_r
        wr_diff = (n_wr - f_wr) * 100

        print(f"  IMPACT:")
        print(f"    Extra Trades: {trade_diff:+d} ({trade_diff/f_trades*100:+.1f}%)")
        print(f"    R Change: {r_diff:+.1f}R ({r_diff/f_r*100:+.1f}% change)")
        print(f"    Win Rate Change: {wr_diff:+.1f} percentage points")

        if r_diff > 10:
            print(f"    >>> FILTERS HURT: Removing filters adds {r_diff:+.1f}R!")
        elif r_diff < -10:
            print(f"    >>> FILTERS HELP: Filters protect you from {abs(r_diff):.1f}R in losses")
        else:
            print(f"    >>> NEUTRAL: Filters don't matter much for this session")

        print()

        total_filtered_r += f_r
        total_nofilter_r += n_r

    # Overall summary
    print("="*100)
    print("OVERALL IMPACT")
    print("="*100)
    print(f"Total R (WITH filters): {total_filtered_r:+.1f}R")
    print(f"Total R (NO filters): {total_nofilter_r:+.1f}R")
    print(f"Difference: {total_nofilter_r - total_filtered_r:+.1f}R")
    print()

    if total_nofilter_r > total_filtered_r + 20:
        print(">>> RECOMMENDATION: REMOVE FILTERS - They're costing you money!")
    elif total_filtered_r > total_nofilter_r + 20:
        print(">>> RECOMMENDATION: KEEP FILTERS - They're protecting your edge!")
    else:
        print(">>> RECOMMENDATION: Filters don't matter much - use whichever you prefer")

    con.close()

if __name__ == "__main__":
    compare()
