"""
Compare Filtered vs No-Max Results

Apples-to-apples comparison using identical logic.
Only difference: filter values (100/150 vs 999999/999999)
"""

import duckdb

DB_PATH = "gold.db"

def compare():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*100)
    print("FILTER IMPACT ANALYSIS - IDENTICAL LOGIC")
    print("="*100)
    print("Comparing: MAX_STOP 100 vs 999999 | ASIA_TP_CAP 150 vs 999999")
    print("="*100)
    print()

    winners = [
        ("1000", 3.0, 2, "", 0, "10:00 ORB (5m exec)"),
        ("0900", 3.0, 2, "", 0, "09:00 ORB (5m exec)"),
        ("1800", 2.0, 1, "half", 0, "18:00 ORB (half-SL)"),
        ("1100", 3.0, 1, "half", 0, "11:00 ORB (half-SL)"),
        ("0030", 1.5, 2, "half", 0, "00:30 ORB (half-SL)"),
    ]

    total_r_filtered = 0
    total_r_nomax = 0
    total_trades_filtered = 0
    total_trades_nomax = 0

    for orb, rr, confirm, sl_mode, buffer, name in winners:
        print(f"{name}")
        print("-"*100)

        # Filtered results
        filtered = con.execute("""
            SELECT
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
                COUNT(*) FILTER (WHERE outcome = 'LOSS') as losses,
                AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
                SUM(r_multiple) as total_r,
                AVG(stop_ticks) as avg_stop
            FROM orb_trades_5m_exec
            WHERE orb = ?
              AND rr = ?
              AND close_confirmations = ?
              AND sl_mode = ?
              AND buffer_ticks = ?
        """, [orb, rr, confirm, sl_mode, buffer]).fetchone()

        # No-max results
        nomax = con.execute("""
            SELECT
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
                COUNT(*) FILTER (WHERE outcome = 'LOSS') as losses,
                AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
                SUM(r_multiple) as total_r,
                AVG(stop_ticks) as avg_stop
            FROM orb_trades_5m_exec_nomax
            WHERE orb = ?
              AND rr = ?
              AND close_confirmations = ?
              AND sl_mode = ?
              AND buffer_ticks = ?
        """, [orb, rr, confirm, sl_mode, buffer]).fetchone()

        if not filtered:
            print("  [WARNING] No filtered data found")
            print()
            continue

        if not nomax:
            print("  [WARNING] No no-max data found - run test_winners_nomax.py first")
            print()
            continue

        f_trades, f_wins, f_losses, f_wr, f_r, f_stop = filtered
        n_trades, n_wins, n_losses, n_wr, n_r, n_stop = nomax

        print(f"  WITH FILTERS (MAX_STOP=100, ASIA_TP_CAP=150):")
        print(f"    Trades: {f_trades} ({f_wins}W / {f_losses}L) | Win Rate: {f_wr:.1%} | Total R: {f_r:+.1f} | Avg Stop: {f_stop:.1f} ticks")

        print(f"  NO MAX FILTERS (MAX_STOP=999999, ASIA_TP_CAP=999999):")
        print(f"    Trades: {n_trades} ({n_wins}W / {n_losses}L) | Win Rate: {n_wr:.1%} | Total R: {n_r:+.1f} | Avg Stop: {n_stop:.1f} ticks")

        trade_diff = n_trades - f_trades
        r_diff = n_r - f_r
        wr_diff = (n_wr - f_wr) * 100
        stop_diff = n_stop - f_stop

        print(f"  IMPACT:")
        print(f"    Trade Change: {trade_diff:+d} ({trade_diff/f_trades*100:+.1f}%)")
        print(f"    R Change: {r_diff:+.1f}R")
        print(f"    Win Rate Change: {wr_diff:+.1f} percentage points")
        print(f"    Avg Stop Change: {stop_diff:+.1f} ticks")

        if r_diff > 10:
            print(f"    >>> FILTERS HURT: +{r_diff:.0f}R without filters")
        elif r_diff < -10:
            print(f"    >>> FILTERS HELP: Avoiding {abs(r_diff):.0f}R in losses")
        else:
            print(f"    >>> NEUTRAL: Small impact")

        print()

        total_r_filtered += f_r
        total_r_nomax += n_r
        total_trades_filtered += f_trades
        total_trades_nomax += n_trades

    print("="*100)
    print("OVERALL SUMMARY")
    print("="*100)
    print(f"Total Trades WITH filters: {total_trades_filtered}")
    print(f"Total Trades NO MAX: {total_trades_nomax} ({total_trades_nomax - total_trades_filtered:+d})")
    print()
    print(f"Total R WITH filters: {total_r_filtered:+.1f}R")
    print(f"Total R NO MAX: {total_r_nomax:+.1f}R")
    print(f"Difference: {total_r_nomax - total_r_filtered:+.1f}R")
    print()

    if total_r_nomax > total_r_filtered + 20:
        print(">>> RECOMMENDATION: REMOVE FILTERS - They're limiting your edge")
        print(f"    Expected improvement: {total_r_nomax - total_r_filtered:+.0f}R")
    elif total_r_filtered > total_r_nomax + 20:
        print(">>> RECOMMENDATION: KEEP FILTERS - They're protecting you")
        print(f"    Filters save you: {total_r_filtered - total_r_nomax:+.0f}R")
    else:
        print(">>> RECOMMENDATION: NEUTRAL - Filters don't matter much")
        print("    Use whichever you prefer")

    print()
    print("="*100)

    con.close()

if __name__ == "__main__":
    compare()
