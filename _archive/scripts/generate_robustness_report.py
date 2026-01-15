"""
Step 5: Generate Robustness Report

Joins filtered results vs no-max robustness results.
Shows deltas and flags "ROBUST" where both scenarios are profitable.

Criteria for ROBUST:
- Both filtered and no-max have total_r >= 0
- Both have trades >= 100
- Config performs well regardless of filter choice
"""

import duckdb
import os
import sys
import pandas as pd
from datetime import datetime

DB_PATH = "gold.db"

def generate_robustness_report():
    """Step 5: Final SQL report comparing filtered vs robustness results"""

    print("="*100)
    print("STEP 5: GENERATE ROBUSTNESS REPORT")
    print("="*100)
    print()

    # Fail fast: Check DB exists
    if not os.path.exists(DB_PATH):
        print(f"[FAIL] Database not found: {DB_PATH}")
        sys.exit(1)

    con = duckdb.connect(DB_PATH, read_only=True)

    # Check required tables exist
    tables = con.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name IN ('orb_trades_5m_exec', 'orb_robustness_results')
    """).fetchall()

    table_names = [t[0] for t in tables]

    if 'orb_trades_5m_exec' not in table_names:
        print("[FAIL] orb_trades_5m_exec table not found")
        con.close()
        sys.exit(1)

    if 'orb_robustness_results' not in table_names:
        print("[FAIL] orb_robustness_results table not found")
        print("       Run run_robustness_batch.py first")
        con.close()
        sys.exit(1)

    print("[PASS] Required tables found")
    print()

    # Build comparison query
    print("STEP 5A: Compare Filtered vs Robustness Results")
    print("-"*100)
    print()

    query = """
    WITH filtered_perf AS (
        SELECT
            orb,
            close_confirmations,
            rr,
            sl_mode,
            buffer_ticks,
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
            COUNT(*) FILTER (WHERE outcome = 'LOSS') as losses,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) FILTER (WHERE outcome IN ('WIN','LOSS')) as win_rate,
            SUM(r_multiple) FILTER (WHERE outcome IN ('WIN','LOSS')) as total_r,
            AVG(r_multiple) FILTER (WHERE outcome IN ('WIN','LOSS')) as avg_r
        FROM orb_trades_5m_exec
        GROUP BY orb, close_confirmations, rr, sl_mode, buffer_ticks
    ),
    robustness_perf AS (
        SELECT
            orb,
            close_confirmations,
            rr,
            sl_mode,
            buffer_ticks,
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
            COUNT(*) FILTER (WHERE outcome = 'LOSS') as losses,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) FILTER (WHERE outcome IN ('WIN','LOSS')) as win_rate,
            SUM(r_multiple) FILTER (WHERE outcome IN ('WIN','LOSS')) as total_r,
            AVG(r_multiple) FILTER (WHERE outcome IN ('WIN','LOSS')) as avg_r
        FROM orb_robustness_results
        GROUP BY orb, close_confirmations, rr, sl_mode, buffer_ticks
    )
    SELECT
        f.orb,
        f.close_confirmations,
        f.rr,
        f.sl_mode,
        f.buffer_ticks,
        f.trades as filtered_trades,
        f.wins as filtered_wins,
        f.losses as filtered_losses,
        f.win_rate as filtered_wr,
        f.total_r as filtered_r,
        r.trades as nomax_trades,
        r.wins as nomax_wins,
        r.losses as nomax_losses,
        r.win_rate as nomax_wr,
        r.total_r as nomax_r,
        (r.trades - f.trades) as extra_trades,
        (r.total_r - f.total_r) as r_delta,
        LEAST(f.total_r, r.total_r) as worst_case_r,
        GREATEST(f.total_r, r.total_r) as best_case_r,
        CASE
            WHEN f.total_r >= 20 AND r.total_r >= 20 AND f.trades >= 100 AND r.trades >= 100 THEN 'ROBUST'
            WHEN f.total_r >= 20 AND f.trades >= 100 AND r.total_r < 20 THEN 'FILTER-DEPENDENT'
            WHEN r.total_r >= 20 AND r.trades >= 100 AND f.total_r < 20 THEN 'NO-FILTER-BETTER'
            ELSE 'MARGINAL'
        END as classification
    FROM filtered_perf f
    INNER JOIN robustness_perf r
        ON f.orb = r.orb
        AND f.close_confirmations = r.close_confirmations
        AND f.rr = r.rr
        AND f.sl_mode = r.sl_mode
        AND f.buffer_ticks = r.buffer_ticks
    ORDER BY worst_case_r DESC, classification
    """

    comparison = con.execute(query).fetchdf()

    if len(comparison) == 0:
        print("[WARN] No matching configs found between filtered and robustness tables")
        print("       This means no candidate configs were tested in robustness batch")
        con.close()
        return

    print(f"[FOUND] {len(comparison)} configs with both filtered and robustness results")
    print()

    # Classification summary
    print("STEP 5B: Classification Summary")
    print("-"*100)
    print()

    classification_counts = comparison['classification'].value_counts()

    for classification, count in classification_counts.items():
        print(f"  {classification:20s}: {count:3d} configs")

    print()

    # Display ROBUST edges
    print("="*100)
    print("ROBUST EDGES (Profitable in BOTH scenarios)")
    print("="*100)
    print()

    robust = comparison[comparison['classification'] == 'ROBUST'].copy()

    if len(robust) > 0:
        print(f"Found {len(robust)} ROBUST edges")
        print()

        for idx, row in robust.iterrows():
            sl_display = row['sl_mode'] if row['sl_mode'] else 'full'
            orb_name = {'0900': '09:00', '1000': '10:00', '1100': '11:00', '1800': '18:00', '2300': '23:00', '0030': '00:30'}.get(row['orb'], row['orb'])

            print(f"{orb_name} | RR={row['rr']} | Confirm={row['close_confirmations']} | SL={sl_display} | Buffer={row['buffer_ticks']}")
            print(f"  WITH Filters:    {row['filtered_r']:+6.1f}R ({int(row['filtered_trades']):4d} trades, {row['filtered_wr']:.1%} WR)")
            print(f"  WITHOUT Filters: {row['nomax_r']:+6.1f}R ({int(row['nomax_trades']):4d} trades, {row['nomax_wr']:.1%} WR)")
            print(f"  Worst Case:      {row['worst_case_r']:+6.1f}R")
            print(f"  Extra Trades:    {int(row['extra_trades'])} (+{int(row['extra_trades'])/int(row['filtered_trades'])*100:.1f}%)")
            print(f"  R Delta:         {row['r_delta']:+.1f}R ({'filters help' if row['r_delta'] < 0 else 'filters hurt'})")
            print()

    else:
        print("No ROBUST edges found")
        print()

    # Display FILTER-DEPENDENT edges
    print("="*100)
    print("FILTER-DEPENDENT EDGES (Only work WITH filters)")
    print("="*100)
    print()

    filter_dep = comparison[comparison['classification'] == 'FILTER-DEPENDENT'].copy()

    if len(filter_dep) > 0:
        print(f"Found {len(filter_dep)} FILTER-DEPENDENT edges")
        print()

        for idx, row in filter_dep.head(10).iterrows():
            sl_display = row['sl_mode'] if row['sl_mode'] else 'full'
            orb_name = {'0900': '09:00', '1000': '10:00', '1100': '11:00', '1800': '18:00', '2300': '23:00', '0030': '00:30'}.get(row['orb'], row['orb'])

            print(f"{orb_name} | RR={row['rr']} | Confirm={row['close_confirmations']} | SL={sl_display} | Buffer={row['buffer_ticks']}")
            print(f"  WITH Filters:    {row['filtered_r']:+6.1f}R ({int(row['filtered_trades']):4d} trades)")
            print(f"  WITHOUT Filters: {row['nomax_r']:+6.1f}R ({int(row['nomax_trades']):4d} trades)")
            print(f"  [CAUTION] Loses {abs(row['r_delta']):.1f}R without filters")
            print()

    else:
        print("None")
        print()

    # Overall summary
    print("="*100)
    print("OVERALL SUMMARY")
    print("="*100)
    print()

    total_filtered_r = comparison['filtered_r'].sum()
    total_nomax_r = comparison['nomax_r'].sum()
    r_saved = total_filtered_r - total_nomax_r

    print(f"Configs analyzed: {len(comparison)}")
    print(f"ROBUST edges: {len(robust)}")
    print(f"FILTER-DEPENDENT edges: {len(filter_dep)}")
    print()
    print(f"Total R (WITH filters): {total_filtered_r:+.1f}R")
    print(f"Total R (WITHOUT filters): {total_nomax_r:+.1f}R")
    print(f"R saved by filters: {r_saved:+.1f}R")
    print()

    if r_saved > 50:
        print("[RECOMMENDATION] KEEP FILTERS")
        print(f"  Filters saved {r_saved:.1f}R by preventing large-stop trades")
    elif r_saved < -50:
        print("[RECOMMENDATION] REMOVE FILTERS")
        print(f"  Filters cost you {abs(r_saved):.1f}R by filtering out profitable trades")
    else:
        print("[RECOMMENDATION] NEUTRAL")
        print(f"  Filters have minimal impact ({r_saved:+.1f}R)")

    print()

    # Export results to CSV
    print("STEP 5C: Export Results")
    print("-"*100)

    csv_path = "robustness_comparison.csv"
    comparison.to_csv(csv_path, index=False)
    print(f"[SAVED] {csv_path}")

    # Export ROBUST edges only
    if len(robust) > 0:
        robust_path = "robust_edges.csv"
        robust.to_csv(robust_path, index=False)
        print(f"[SAVED] {robust_path} ({len(robust)} robust edges)")

    print()

    # Generate markdown report
    print("STEP 5D: Generate Markdown Report")
    print("-"*100)

    report_lines = []

    report_lines.append("# ROBUSTNESS TEST RESULTS")
    report_lines.append("")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("**Test Parameters:**")
    report_lines.append("- Filtered: MAX_STOP=100, ASIA_TP_CAP=150")
    report_lines.append("- No-Max: MAX_STOP=999999, ASIA_TP_CAP=999999")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    report_lines.append("## Summary")
    report_lines.append("")
    report_lines.append(f"- **Configs Tested:** {len(comparison)}")
    report_lines.append(f"- **ROBUST Edges:** {len(robust)}")
    report_lines.append(f"- **FILTER-DEPENDENT Edges:** {len(filter_dep)}")
    report_lines.append(f"- **Total R (WITH filters):** {total_filtered_r:+.1f}R")
    report_lines.append(f"- **Total R (WITHOUT filters):** {total_nomax_r:+.1f}R")
    report_lines.append(f"- **R Saved by Filters:** {r_saved:+.1f}R")
    report_lines.append("")

    if r_saved > 50:
        report_lines.append("**Recommendation:** ✅ **KEEP FILTERS**")
    elif r_saved < -50:
        report_lines.append("**Recommendation:** ❌ **REMOVE FILTERS**")
    else:
        report_lines.append("**Recommendation:** ⚖️ **NEUTRAL**")

    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    if len(robust) > 0:
        report_lines.append("## Robust Edges")
        report_lines.append("")

        for idx, row in robust.iterrows():
            sl_display = row['sl_mode'] if row['sl_mode'] else 'full'
            orb_name = {'0900': '09:00', '1000': '10:00', '1100': '11:00', '1800': '18:00', '2300': '23:00', '0030': '00:30'}.get(row['orb'], row['orb'])

            report_lines.append(f"### {orb_name} ORB | RR={row['rr']} | Confirm={row['close_confirmations']} | SL={sl_display} | Buffer={row['buffer_ticks']}")
            report_lines.append("")
            report_lines.append(f"- **WITH Filters:** {row['filtered_r']:+.1f}R ({int(row['filtered_trades'])} trades, {row['filtered_wr']:.1%} WR)")
            report_lines.append(f"- **WITHOUT Filters:** {row['nomax_r']:+.1f}R ({int(row['nomax_trades'])} trades, {row['nomax_wr']:.1%} WR)")
            report_lines.append(f"- **Worst Case:** {row['worst_case_r']:+.1f}R")
            report_lines.append(f"- **Robustness:** EXCELLENT - Works in both scenarios")
            report_lines.append("")

    report_path = "ROBUSTNESS_REPORT.md"
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))

    print(f"[SAVED] {report_path}")
    print()

    print("="*100)
    print("ROBUSTNESS ANALYSIS COMPLETE")
    print("="*100)
    print()
    print("Files created:")
    print(f"  - {csv_path} (full comparison)")
    if len(robust) > 0:
        print(f"  - {robust_path} (robust edges only)")
    print(f"  - {report_path} (markdown report)")
    print()
    print("="*100)

    con.close()

if __name__ == "__main__":
    generate_robustness_report()
