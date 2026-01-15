"""
Phase 4: Identify Real Edges

Finds configurations that are profitable in BOTH filtered and no-max scenarios.
These represent robust edges that aren't dependent on specific filter values.

Criteria for "real edge":
1. Total R > +20 (meaningful profit)
2. Trades > 100 (adequate sample size)
3. Win rate > breakeven for the RR
4. Works in BOTH filtered and no-max (robust)
"""

import duckdb

DB_PATH = "gold.db"

def identify_edges():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*100)
    print("PHASE 4: IDENTIFY ROBUST EDGES")
    print("="*100)
    print()

    # Find configs profitable in BOTH scenarios
    query = """
    WITH filtered_perf AS (
        SELECT
            orb, close_confirmations, rr, sl_mode, buffer_ticks,
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as wr,
            SUM(r_multiple) as total_r
        FROM orb_trades_5m_exec
        GROUP BY orb, close_confirmations, rr, sl_mode, buffer_ticks
        HAVING total_r > 20 AND trades > 100
    ),
    nomax_perf AS (
        SELECT
            orb, close_confirmations, rr, sl_mode, buffer_ticks,
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as wr,
            SUM(r_multiple) as total_r
        FROM orb_trades_5m_exec_nomax
        GROUP BY orb, close_confirmations, rr, sl_mode, buffer_ticks
        HAVING total_r > 20 AND trades > 100
    )
    SELECT
        f.orb,
        f.close_confirmations as confirm,
        f.rr,
        f.sl_mode,
        f.buffer_ticks,
        f.total_r as r_filtered,
        n.total_r as r_nomax,
        f.wr as wr_filtered,
        n.wr as wr_nomax,
        f.trades as trades_filtered,
        n.trades as trades_nomax,
        CASE
            WHEN f.total_r > n.total_r THEN 'KEEP FILTERS'
            WHEN n.total_r > f.total_r THEN 'REMOVE FILTERS'
            ELSE 'NEUTRAL'
        END as recommendation,
        LEAST(f.total_r, n.total_r) as worst_case_r,
        GREATEST(f.total_r, n.total_r) as best_case_r
    FROM filtered_perf f
    INNER JOIN nomax_perf n
        ON f.orb = n.orb
        AND f.close_confirmations = n.close_confirmations
        AND f.rr = n.rr
        AND f.sl_mode = n.sl_mode
        AND f.buffer_ticks = n.buffer_ticks
    ORDER BY worst_case_r DESC
    """

    edges = con.execute(query).fetchdf()

    if len(edges) == 0:
        print("No robust edges found.")
        print()
        print("Possible reasons:")
        print("1. test_winners_nomax.py hasn't been run yet")
        print("2. None of the configs meet criteria (>20R, >100 trades) in both scenarios")
        print()
    else:
        print(f"Found {len(edges)} robust edge(s) that work in BOTH scenarios")
        print("-"*100)
        print()

        # Display with proper formatting
        for idx, row in edges.iterrows():
            sl_info = f", SL={row['sl_mode']}, buffer={row['buffer_ticks']}" if row['sl_mode'] else ""
            print(f"{idx+1}. {row['orb']} ORB | RR={row['rr']}, confirm={row['confirm']}{sl_info}")
            print(f"   WITH Filters:    {row['r_filtered']:+6.1f}R ({row['trades_filtered']:4d} trades, WR={row['wr_filtered']:.1%})")
            print(f"   NO MAX Filters:  {row['r_nomax']:+6.1f}R ({row['trades_nomax']:4d} trades, WR={row['wr_nomax']:.1%})")
            print(f"   Worst Case:      {row['worst_case_r']:+6.1f}R (robust)")
            print(f"   Best Case:       {row['best_case_r']:+6.1f}R (optimal)")
            print(f"   Recommendation:  {row['recommendation']}")
            print()

        print("-"*100)
        print()
        print("TRADING RECOMMENDATIONS:")
        print()

        for idx, row in edges.iterrows():
            orb_name = {
                '0900': '09:00', '1000': '10:00', '1100': '11:00',
                '1800': '18:00', '2300': '23:00', '0030': '00:30'
            }.get(row['orb'], row['orb'])

            if row['worst_case_r'] > 50:
                strength = "STRONG"
                action = "Trade Live"
            elif row['worst_case_r'] > 30:
                strength = "MODERATE"
                action = "Paper Trade First"
            else:
                strength = "WEAK"
                action = "Monitor Only"

            sl_info = f", {row['sl_mode']}-SL, buffer={row['buffer_ticks']}" if row['sl_mode'] else ""
            print(f"  {orb_name} ORB (RR={row['rr']}, confirm={row['confirm']}{sl_info})")
            print(f"    Strength: {strength} | Action: {action}")
            print(f"    Use: {row['recommendation']}")

    print()
    print("="*100)

    con.close()

if __name__ == "__main__":
    identify_edges()
