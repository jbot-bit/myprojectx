"""
Phase 3 (Corrected): Compare ONLY Common Configs

Proper apples-to-apples comparison of the 24 configs that exist in BOTH tables.

For each common config:
- Compare trade count per day (should be same or nomax >= filtered)
- Compare R-multiples
- Determine if filters help or hurt

If nomax has MORE total trades, it means filtered table is missing that config entirely.
If nomax has SAME trades per day, filters had no impact.
If nomax has FEWER trades per day, something is wrong (filters can't add trades).
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def compare_common():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*100)
    print("PHASE 3 (CORRECTED): COMPARE COMMON CONFIGS ONLY")
    print("="*100)
    print()

    # Get the 24 common configs
    print("STEP 1: Identify Common Configs")
    print("-"*100)

    common = con.execute("""
        WITH filtered_configs AS (
            SELECT DISTINCT orb, close_confirmations, rr, sl_mode, buffer_ticks
            FROM orb_trades_5m_exec
        ),
        nomax_configs AS (
            SELECT DISTINCT orb, close_confirmations, rr, sl_mode, buffer_ticks
            FROM orb_trades_5m_exec_nomax
        )
        SELECT f.orb, f.close_confirmations, f.rr, f.sl_mode, f.buffer_ticks
        FROM filtered_configs f
        INNER JOIN nomax_configs n
            ON f.orb = n.orb
            AND f.close_confirmations = n.close_confirmations
            AND f.rr = n.rr
            AND f.sl_mode = n.sl_mode
            AND f.buffer_ticks = n.buffer_ticks
        ORDER BY f.orb, f.rr, f.close_confirmations
    """).fetchdf()

    print(f"Found {len(common)} common configurations")
    print()

    # For each common config, compare apples-to-apples
    print("STEP 2: Compare Each Config (Same Logic, Different Filters)")
    print("-"*100)
    print()

    results = []

    for _, config in common.iterrows():
        orb = config['orb']
        confirm = config['close_confirmations']
        rr = config['rr']
        sl_mode = config['sl_mode']
        buffer = config['buffer_ticks']

        # Filtered stats
        filtered = con.execute("""
            SELECT
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) FILTER (WHERE outcome IN ('WIN','LOSS')) as win_rate,
                SUM(r_multiple) FILTER (WHERE outcome IN ('WIN','LOSS')) as total_r,
                AVG(stop_ticks) FILTER (WHERE outcome IN ('WIN','LOSS')) as avg_stop
            FROM orb_trades_5m_exec
            WHERE orb = ? AND close_confirmations = ? AND rr = ? AND sl_mode = ? AND buffer_ticks = ?
              AND outcome IN ('WIN','LOSS')
        """, [orb, confirm, rr, sl_mode, buffer]).fetchone()

        # No-max stats
        nomax = con.execute("""
            SELECT
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) FILTER (WHERE outcome IN ('WIN','LOSS')) as win_rate,
                SUM(r_multiple) FILTER (WHERE outcome IN ('WIN','LOSS')) as total_r,
                AVG(stop_ticks) FILTER (WHERE outcome IN ('WIN','LOSS')) as avg_stop
            FROM orb_trades_5m_exec_nomax
            WHERE orb = ? AND close_confirmations = ? AND rr = ? AND sl_mode = ? AND buffer_ticks = ?
              AND outcome IN ('WIN','LOSS')
        """, [orb, confirm, rr, sl_mode, buffer]).fetchone()

        if filtered[0] > 0 and nomax[0] > 0:
            results.append({
                'orb': orb,
                'confirm': confirm,
                'rr': rr,
                'sl_mode': sl_mode if sl_mode else 'full',
                'buffer': buffer,
                'trades_filtered': filtered[0],
                'trades_nomax': nomax[0],
                'extra_trades': nomax[0] - filtered[0],
                'wr_filtered': filtered[1] * 100,
                'wr_nomax': nomax[1] * 100,
                'r_filtered': filtered[2],
                'r_nomax': nomax[2],
                'r_impact': nomax[2] - filtered[2],  # Positive = gained R by removing filters
                'avg_stop_filtered': filtered[3],
                'avg_stop_nomax': nomax[3],
            })

    df = pd.DataFrame(results)

    # Display top/bottom by R impact
    print("TOP 10: Configs Where Removing Filters HELPED (gained most R)")
    print("-"*100)
    df_top = df.nlargest(10, 'r_impact')[['orb', 'confirm', 'rr', 'sl_mode', 'trades_filtered', 'trades_nomax', 'extra_trades', 'r_filtered', 'r_nomax', 'r_impact']]
    print(df_top.to_string(index=False))
    print()

    print("TOP 10: Configs Where Keeping Filters HELPED (lost most R by removing)")
    print("-"*100)
    df_bottom = df.nsmallest(10, 'r_impact')[['orb', 'confirm', 'rr', 'sl_mode', 'trades_filtered', 'trades_nomax', 'extra_trades', 'r_filtered', 'r_nomax', 'r_impact']]
    print(df_bottom.to_string(index=False))
    print()

    # Overall summary for common configs only
    print("="*100)
    print("OVERALL SUMMARY (24 Common Configs Only)")
    print("="*100)
    print()

    total_filtered_trades = df['trades_filtered'].sum()
    total_nomax_trades = df['trades_nomax'].sum()
    total_extra_trades = df['extra_trades'].sum()

    total_r_filtered = df['r_filtered'].sum()
    total_r_nomax = df['r_nomax'].sum()
    total_r_impact = df['r_impact'].sum()

    print(f"Total trades (WITH filters):    {total_filtered_trades:,}")
    print(f"Total trades (WITHOUT filters): {total_nomax_trades:,}")
    print(f"Extra trades from removing filters: {total_extra_trades:,}")
    print()

    print(f"Total R (WITH filters):    {total_r_filtered:+.1f}R")
    print(f"Total R (WITHOUT filters): {total_r_nomax:+.1f}R")
    print(f"R gained by removing filters: {total_r_impact:+.1f}R")
    print()

    # Interpretation
    if total_r_impact > 10:
        print("[INSIGHT] Removing filters HELPED performance")
        print(f"          Gained {total_r_impact:.1f}R by removing MAX_STOP and ASIA_TP_CAP filters")
        print()
        print("RECOMMENDATION: Consider REMOVING filters for these 24 configs")
    elif total_r_impact < -10:
        print("[INSIGHT] Keeping filters HELPED performance")
        print(f"          Saved {abs(total_r_impact):.1f}R by applying MAX_STOP and ASIA_TP_CAP filters")
        print()
        print("RECOMMENDATION: KEEP filters")
    else:
        print("[INSIGHT] Filters had MINIMAL impact")
        print(f"          Net difference: {total_r_impact:+.1f}R")
        print()
        print("RECOMMENDATION: Filters are neutral - keep for risk management")

    print()

    # Check if extra_trades makes sense
    print("="*100)
    print("SANITY CHECK: Do Extra Trades Make Sense?")
    print("="*100)
    print()

    if total_extra_trades > 0:
        print(f"[EXPECTED] No-max has {total_extra_trades:,} MORE trades")
        print("           This is correct - removing filters allows more trades to execute")
        print()

        # Check if stops got bigger
        avg_stop_increase = (df['avg_stop_nomax'] - df['avg_stop_filtered']).mean()
        print(f"Average stop increase: {avg_stop_increase:+.2f} ticks")

        if avg_stop_increase > 0:
            print("[EXPECTED] Average stops got BIGGER without filters")
            print("           This confirms MAX_STOP filter was working")
        else:
            print("[UNEXPECTED] Average stops did NOT increase")
            print("              This suggests MAX_STOP filter may not have been active")

    elif total_extra_trades == 0:
        print("[UNEXPECTED] No difference in trade counts")
        print("             Filters had NO EFFECT on trade selection")
        print("             This suggests MAX_STOP and ASIA_TP_CAP were never triggered")

    else:
        print("[ERROR] No-max has FEWER trades than filtered!")
        print("        This is impossible - filters can't add trades")
        print("        Something is wrong with the data or comparison")

    print()
    print("="*100)

    con.close()

if __name__ == "__main__":
    compare_common()
