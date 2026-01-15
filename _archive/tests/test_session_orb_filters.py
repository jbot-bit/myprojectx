"""
Test Session-Specific ORB Range Filters

IMPORTANT HONESTY DISCLAIMER:
- These filters are derived FROM the same data we're testing ON
- This is IN-SAMPLE optimization (curve-fitting risk!)
- Real performance may be worse in live trading
- These rules need forward validation on NEW data

BUT: If patterns are genuine (session personality), they should persist.

Filter Rules Discovered:
- 1800: Trade when ORB < 30 ticks (tight ranges)
- 1100: Trade when ORB > 30 ticks (large ORBs)
- 1000: Trade when ORB 20-40 ticks (goldilocks)
- 0900: Trade when ORB > 50 ticks (high volatility only)
- 2300: Skip entirely (losing session)
- 0030: Skip entirely (losing session)
"""

import duckdb

DB_PATH = "gold.db"

def test_filters():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*100)
    print("SESSION-SPECIFIC ORB RANGE FILTER TEST")
    print("="*100)
    print()
    print("HONESTY WARNING:")
    print("  This is IN-SAMPLE optimization on the same data")
    print("  Risk of curve-fitting / overfitting")
    print("  Real edge may be smaller in live trading")
    print("  Needs validation on future data")
    print()
    print("="*100)
    print()

    # Define filters per session
    filters = {
        '0900': {'min': 50, 'max': 999, 'rationale': 'High volatility only'},
        '1000': {'min': 20, 'max': 40, 'rationale': 'Goldilocks zone'},
        '1100': {'min': 30, 'max': 999, 'rationale': 'Large ORBs only'},
        '1800': {'min': 0, 'max': 30, 'rationale': 'Tight ranges preferred'},
        '2300': {'min': 999, 'max': 0, 'rationale': 'SKIP - losing session'},
        '0030': {'min': 999, 'max': 0, 'rationale': 'SKIP - losing session'},
    }

    total_unfiltered_trades = 0
    total_unfiltered_r = 0
    total_filtered_trades = 0
    total_filtered_r = 0

    for session in ['0900', '1000', '1100', '1800', '2300', '0030']:
        filter_min = filters[session]['min']
        filter_max = filters[session]['max']
        rationale = filters[session]['rationale']

        # Unfiltered performance
        unfiltered = con.execute("""
            SELECT
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
                AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
                SUM(r_multiple) as total_r,
                AVG(orb_range_ticks) as avg_orb_range
            FROM orb_trades_5m_exec_orbr
            WHERE orb = ?
                AND rr = 2.0
                AND close_confirmations = 1
                AND sl_mode = 'half'
                AND buffer_ticks = 0
                AND outcome IN ('WIN', 'LOSS')
        """, [session]).fetchone()

        # Filtered performance
        filtered = con.execute("""
            SELECT
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
                AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
                SUM(r_multiple) as total_r,
                AVG(orb_range_ticks) as avg_orb_range
            FROM orb_trades_5m_exec_orbr
            WHERE orb = ?
                AND rr = 2.0
                AND close_confirmations = 1
                AND sl_mode = 'half'
                AND buffer_ticks = 0
                AND outcome IN ('WIN', 'LOSS')
                AND orb_range_ticks >= ?
                AND orb_range_ticks < ?
        """, [session, filter_min, filter_max]).fetchone()

        if not unfiltered or unfiltered[0] == 0:
            continue

        u_trades, u_wins, u_wr, u_r, u_avg_orb = unfiltered

        if not filtered or filtered[0] == 0:
            f_trades, f_wins, f_wr, f_r, f_avg_orb = 0, 0, 0, 0, 0
        else:
            f_trades, f_wins, f_wr, f_r, f_avg_orb = filtered

        print(f"{session} ORB: {rationale}")
        print("-"*100)
        print(f"  Filter: ORB range {filter_min}-{filter_max} ticks")
        print()
        print(f"  UNFILTERED (all ORB sizes):")
        print(f"    {u_trades} trades | {u_wins}W | WR={u_wr:.1%} | R={u_r:+.1f} | Avg ORB={u_avg_orb:.1f} ticks")
        print()
        print(f"  FILTERED (optimal ORB range only):")
        print(f"    {f_trades} trades | {f_wins}W | WR={f_wr:.1%} | R={f_r:+.1f} | Avg ORB={f_avg_orb:.1f} ticks")
        print()

        if f_trades > 0:
            trades_kept = f_trades / u_trades * 100
            r_improvement = f_r - u_r
            wr_improvement = (f_wr - u_wr) * 100

            print(f"  IMPACT:")
            print(f"    Trades kept: {f_trades}/{u_trades} ({trades_kept:.0f}%)")
            print(f"    R improvement: {r_improvement:+.1f}R")
            print(f"    WR improvement: {wr_improvement:+.1f} percentage points")

            if r_improvement > 10:
                print(f"    >>> FILTER HELPS: +{r_improvement:.0f}R improvement")
            elif r_improvement > 0:
                print(f"    >>> FILTER HELPS SLIGHTLY: +{r_improvement:.0f}R improvement")
            else:
                print(f"    >>> FILTER HURTS: {r_improvement:.0f}R worse")
        else:
            print(f"  IMPACT: Session filtered out entirely (intentional)")

        print()

        total_unfiltered_trades += u_trades
        total_unfiltered_r += u_r
        total_filtered_trades += f_trades
        total_filtered_r += f_r

    print("="*100)
    print("OVERALL PORTFOLIO IMPACT")
    print("="*100)
    print()
    print(f"UNFILTERED (trade all sessions, all ORB sizes):")
    print(f"  {total_unfiltered_trades} trades | Total R: {total_unfiltered_r:+.1f}")
    print()
    print(f"FILTERED (session-specific ORB range rules):")
    print(f"  {total_filtered_trades} trades | Total R: {total_filtered_r:+.1f}")
    print()

    r_improvement = total_filtered_r - total_unfiltered_r
    trades_reduction = total_unfiltered_trades - total_filtered_trades
    reduction_pct = trades_reduction / total_unfiltered_trades * 100

    print(f"NET IMPACT:")
    print(f"  R improvement: {r_improvement:+.1f}R ({r_improvement/total_unfiltered_r*100:+.0f}%)")
    print(f"  Trades reduced: {trades_reduction} ({reduction_pct:.0f}% fewer trades)")
    if total_filtered_trades > 0:
        print(f"  Avg R per trade (filtered): {total_filtered_r/total_filtered_trades:+.3f}R")
        print(f"  Avg R per trade (unfiltered): {total_unfiltered_r/total_unfiltered_trades:+.3f}R")
    print()

    if r_improvement > 20:
        print(">>> STRONG IMPROVEMENT: Filters significantly improve results")
        print("    BUT: In-sample optimization - validate on new data!")
    elif r_improvement > 0:
        print(">>> MODEST IMPROVEMENT: Filters help slightly")
        print("    BUT: In-sample optimization - validate on new data!")
    else:
        print(">>> NO IMPROVEMENT: Filters don't help")
        print("    This is actually GOOD - means we're not overfitting!")

    print()
    print("="*100)
    print("HONEST ASSESSMENT")
    print("="*100)
    print()
    print("RISKS:")
    print("  1. In-sample optimization (curve-fitting)")
    print("  2. May not work on future data")
    print("  3. Fewer trades = higher variance")
    print("  4. Filters found by looking at outcomes (cheating)")
    print()
    print("STRENGTHS:")
    print("  1. Based on logical session personalities")
    print("  2. Rules are simple and intuitive")
    print("  3. Consistent with market behavior (volatility regimes)")
    print("  4. Can be validated going forward")
    print()
    print("RECOMMENDATION:")
    print("  - Paper trade filtered rules for 1-2 months")
    print("  - Compare filtered vs unfiltered in LIVE conditions")
    print("  - Only use in live trading if edge persists")
    print("  - Be prepared to abandon if doesn't work")
    print()
    print("="*100)

    con.close()

if __name__ == "__main__":
    test_filters()
