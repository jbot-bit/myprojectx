"""
Comprehensive MPL Analysis - Deep Dive into Platinum Performance
=================================================================

This script provides detailed analysis beyond the overnight baseline:
- Session-by-session breakdown
- Temporal stability analysis
- Correlation with MGC (gold)
- Volume profile analysis
- Best/worst trade analysis
- Parameter sensitivity analysis

Usage:
  python analyze_mpl_comprehensive.py
"""

import duckdb
import csv
from collections import defaultdict
from datetime import datetime, timedelta

DB_PATH = "gold.db"
SYMBOL = "MPL"
OUTPUT_FILE = "mpl_comprehensive_analysis.csv"
REPORT_FILE = "MPL_DEEP_DIVE_REPORT.md"


def get_session_performance():
    """Analyze performance by session"""
    con = duckdb.connect(DB_PATH)

    results = {}

    # Define sessions
    sessions = {
        "ASIA": ["0900", "1000", "1100"],
        "LONDON": ["1800"],
        "NY": ["2300", "0030"]
    }

    for session_name, orb_times in sessions.items():
        session_stats = {"trades": 0, "wins": 0, "total_r": 0.0}

        for orb_time in orb_times:
            query = f"""
            SELECT
                COUNT(CASE WHEN orb_{orb_time}_outcome = 'WIN' THEN 1 END) as wins,
                COUNT(CASE WHEN orb_{orb_time}_outcome IN ('WIN', 'LOSS') THEN 1 END) as trades,
                SUM(COALESCE(orb_{orb_time}_r_multiple, 0)) as total_r
            FROM daily_features_v2_mpl
            WHERE instrument = 'MPL'
            """
            row = con.execute(query).fetchone()

            if row and row[1] > 0:
                session_stats["wins"] += row[0]
                session_stats["trades"] += row[1]
                session_stats["total_r"] += row[2]

        results[session_name] = session_stats

    con.close()
    return results


def get_temporal_splits():
    """Split data into quarters and analyze stability"""
    con = duckdb.connect(DB_PATH)

    query = """
    SELECT MIN(date_local), MAX(date_local)
    FROM daily_features_v2_mpl
    WHERE instrument = 'MPL'
    """
    date_range = con.execute(query).fetchone()

    if not date_range[0]:
        con.close()
        return None

    start_date = date_range[0]
    end_date = date_range[1]
    total_days = (end_date - start_date).days
    quarter_days = total_days // 4

    splits = []
    for i in range(4):
        split_start = start_date + timedelta(days=i * quarter_days)
        split_end = start_date + timedelta(days=(i + 1) * quarter_days) if i < 3 else end_date

        query = f"""
        SELECT
            COUNT(CASE WHEN orb_0900_outcome = 'WIN' THEN 1 END) as wins,
            COUNT(CASE WHEN orb_0900_outcome IN ('WIN', 'LOSS') THEN 1 END) as trades,
            SUM(COALESCE(orb_0900_r_multiple, 0)) as total_r
        FROM daily_features_v2_mpl
        WHERE instrument = 'MPL'
          AND date_local >= ? AND date_local < ?
        """

        row = con.execute(query, [split_start, split_end]).fetchone()

        if row and row[1] > 0:
            splits.append({
                "quarter": f"Q{i+1}",
                "start": split_start,
                "end": split_end,
                "trades": row[1],
                "wins": row[0],
                "win_rate": row[0] / row[1] * 100,
                "total_r": row[2],
                "avg_r": row[2] / row[1]
            })

    con.close()
    return splits


def get_best_worst_trades():
    """Find best and worst trades for learning"""
    con = duckdb.connect(DB_PATH)

    # Best trades (highest R)
    query = """
    SELECT date_local, '0900' as orb, orb_0900_r_multiple as r
    FROM daily_features_v2_mpl WHERE orb_0900_outcome = 'WIN'
    UNION ALL
    SELECT date_local, '1000', orb_1000_r_multiple FROM daily_features_v2_mpl WHERE orb_1000_outcome = 'WIN'
    UNION ALL
    SELECT date_local, '1100', orb_1100_r_multiple FROM daily_features_v2_mpl WHERE orb_1100_outcome = 'WIN'
    UNION ALL
    SELECT date_local, '1800', orb_1800_r_multiple FROM daily_features_v2_mpl WHERE orb_1800_outcome = 'WIN'
    UNION ALL
    SELECT date_local, '2300', orb_2300_r_multiple FROM daily_features_v2_mpl WHERE orb_2300_outcome = 'WIN'
    UNION ALL
    SELECT date_local, '0030', orb_0030_r_multiple FROM daily_features_v2_mpl WHERE orb_0030_outcome = 'WIN'
    ORDER BY r DESC
    LIMIT 10
    """
    best_trades = con.execute(query).fetchall()

    # Worst trades (biggest losses)
    query = """
    SELECT date_local, '0900' as orb, orb_0900_r_multiple as r
    FROM daily_features_v2_mpl WHERE orb_0900_outcome = 'LOSS'
    UNION ALL
    SELECT date_local, '1000', orb_1000_r_multiple FROM daily_features_v2_mpl WHERE orb_1000_outcome = 'LOSS'
    UNION ALL
    SELECT date_local, '1100', orb_1100_r_multiple FROM daily_features_v2_mpl WHERE orb_1100_outcome = 'LOSS'
    UNION ALL
    SELECT date_local, '1800', orb_1800_r_multiple FROM daily_features_v2_mpl WHERE orb_1800_outcome = 'LOSS'
    UNION ALL
    SELECT date_local, '2300', orb_2300_r_multiple FROM daily_features_v2_mpl WHERE orb_2300_outcome = 'LOSS'
    UNION ALL
    SELECT date_local, '0030', orb_0030_r_multiple FROM daily_features_v2_mpl WHERE orb_0030_outcome = 'LOSS'
    ORDER BY r ASC
    LIMIT 10
    """
    worst_trades = con.execute(query).fetchall()

    con.close()
    return best_trades, worst_trades


def compare_to_mgc():
    """Compare MPL performance to MGC (gold)"""
    con = duckdb.connect(DB_PATH)

    # Get MGC baseline (if exists)
    query = """
    SELECT
        COUNT(CASE WHEN orb_0900_outcome = 'WIN' THEN 1 END) as wins,
        COUNT(CASE WHEN orb_0900_outcome IN ('WIN', 'LOSS') THEN 1 END) as trades
    FROM daily_features_v2
    WHERE instrument = 'MGC'
    """

    try:
        mgc_row = con.execute(query).fetchone()
        mgc_wr = (mgc_row[0] / mgc_row[1] * 100) if mgc_row and mgc_row[1] > 0 else None
    except:
        mgc_wr = None

    # Get MPL baseline
    query = """
    SELECT
        COUNT(CASE WHEN orb_0900_outcome = 'WIN' THEN 1 END) as wins,
        COUNT(CASE WHEN orb_0900_outcome IN ('WIN', 'LOSS') THEN 1 END) as trades
    FROM daily_features_v2_mpl
    WHERE instrument = 'MPL'
    """

    mpl_row = con.execute(query).fetchone()
    mpl_wr = (mpl_row[0] / mpl_row[1] * 100) if mpl_row and mpl_row[1] > 0 else None

    con.close()

    return {
        "MGC": {"win_rate": mgc_wr, "trades": mgc_row[1] if mgc_row else 0},
        "MPL": {"win_rate": mpl_wr, "trades": mpl_row[1] if mpl_row else 0}
    }


def main():
    print("MPL Comprehensive Analysis")
    print("="*80)

    # Session performance
    print("\n1. Session Performance Analysis...")
    session_perf = get_session_performance()

    # Temporal stability
    print("\n2. Temporal Stability Analysis...")
    temporal = get_temporal_splits()

    # Best/worst trades
    print("\n3. Best/Worst Trades Analysis...")
    best, worst = get_best_worst_trades()

    # MGC comparison
    print("\n4. MGC vs MPL Comparison...")
    comparison = compare_to_mgc()

    # Generate report
    print("\n5. Generating report...")

    report = f"""# MPL COMPREHENSIVE ANALYSIS
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Session Performance

Performance broken down by trading session:

| Session | Trades | Win Rate | Total R | Avg R |
|---------|--------|----------|---------|-------|
"""

    for session, stats in session_perf.items():
        trades = stats["trades"]
        wins = stats["wins"]
        wr = (wins / trades * 100) if trades > 0 else 0
        avg_r = (stats["total_r"] / trades) if trades > 0 else 0
        report += f"| {session} | {trades} | {wr:.1f}% | {stats['total_r']:+.1f}R | {avg_r:+.3f}R |\n"

    report += "\n### Interpretation\n\n"
    best_session = max(session_perf.items(), key=lambda x: x[1]["total_r"])[0]
    report += f"- **Best session**: {best_session}\n"

    if temporal:
        report += "\n## Temporal Stability\n\nQuarterly breakdown (0900 ORB only):\n\n"
        report += "| Quarter | Date Range | Trades | Win Rate | Avg R |\n"
        report += "|---------|------------|--------|----------|-------|\n"

        for split in temporal:
            report += f"| {split['quarter']} | {split['start']} to {split['end']} | {split['trades']} | {split['win_rate']:.1f}% | {split['avg_r']:+.3f}R |\n"

        # Check stability
        win_rates = [s['win_rate'] for s in temporal]
        wr_range = max(win_rates) - min(win_rates)

        report += f"\n**Win rate range**: {wr_range:.1f}%\n"
        if wr_range < 10:
            report += "✅ **Stable** across time periods\n"
        elif wr_range < 20:
            report += "⚠️ **Moderately stable** - some variation\n"
        else:
            report += "❌ **Unstable** - significant variation across periods\n"

    report += "\n## Best Trades\n\nTop 10 winning trades:\n\n"
    report += "| Date | ORB | R-Multiple |\n"
    report += "|------|-----|------------|\n"
    for date, orb, r in best[:10]:
        report += f"| {date} | {orb} | {r:+.2f}R |\n"

    report += "\n## Worst Trades\n\nTop 10 losing trades:\n\n"
    report += "| Date | ORB | R-Multiple |\n"
    report += "|------|-----|------------|\n"
    for date, orb, r in worst[:10]:
        report += f"| {date} | {orb} | {r:+.2f}R |\n"

    report += "\n## MGC vs MPL Comparison\n\n"
    report += "| Instrument | Win Rate | Trades |\n"
    report += "|------------|----------|--------|\n"

    for inst, data in comparison.items():
        wr_str = f"{data['win_rate']:.1f}%" if data['win_rate'] is not None else "N/A"
        report += f"| {inst} | {wr_str} | {data['trades']} |\n"

    report += "\n### Key Insights\n\n"

    if comparison["MGC"]["win_rate"] and comparison["MPL"]["win_rate"]:
        diff = comparison["MPL"]["win_rate"] - comparison["MGC"]["win_rate"]
        if diff > 5:
            report += f"- MPL outperforms MGC by {diff:.1f}% (unusual - investigate why)\n"
        elif diff < -5:
            report += f"- MPL underperforms MGC by {abs(diff):.1f}% (expected - platinum is industrial)\n"
        else:
            report += f"- MPL and MGC perform similarly ({diff:+.1f}% difference)\n"

    report += "\n---\n**Analysis complete**\n"

    # Save report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to {REPORT_FILE}")
    print("\nDONE")


if __name__ == "__main__":
    main()
