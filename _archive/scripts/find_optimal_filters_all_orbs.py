"""
Find Optimal Filter for Each ORB
=================================

Test structural filters for each ORB individually:
- Pre-session travel
- Prior session sweep
- Session range regime

Then identify best filter per ORB.
"""

import duckdb
import numpy as np

DB_PATH = "gold.db"


def test_orb_filters(orb_time, orb_hour, orb_min, pre_session_col, prior_session_orb, session_range_col):
    """
    Test multiple filters for a specific ORB.

    Args:
        orb_time: e.g., "0900"
        orb_hour, orb_min: ORB time
        pre_session_col: e.g., "pre_asia_range" for 0900
        prior_session_orb: e.g., None for 0900 (first of day), "0900" for 1000
        session_range_col: e.g., "asia_range" for later sessions
    """
    con = duckdb.connect(DB_PATH)

    print("=" * 100)
    print(f"ORB {orb_time}")
    print("=" * 100)
    print()

    # Baseline: no filter
    results_baseline = con.execute(f"""
        SELECT
            orb_{orb_time}_outcome as outcome,
            orb_{orb_time}_r_multiple as r_multiple,
            orb_{orb_time}_mae as mae,
            orb_{orb_time}_mfe as mfe
        FROM daily_features_v2_half
        WHERE orb_{orb_time}_break_dir IS NOT NULL
          AND orb_{orb_time}_break_dir != 'NONE'
    """).fetchall()

    baseline = compute_stats(results_baseline, "NO FILTER (baseline)")

    filters_tested = [baseline]

    # Filter 1: Pre-session travel
    if pre_session_col:
        median_travel = con.execute(f"""
            SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {pre_session_col})
            FROM daily_features_v2_half
            WHERE {pre_session_col} IS NOT NULL
        """).fetchone()[0]

        results_travel = con.execute(f"""
            SELECT
                orb_{orb_time}_outcome as outcome,
                orb_{orb_time}_r_multiple as r_multiple,
                orb_{orb_time}_mae as mae,
                orb_{orb_time}_mfe as mfe
            FROM daily_features_v2_half
            WHERE orb_{orb_time}_break_dir IS NOT NULL
              AND orb_{orb_time}_break_dir != 'NONE'
              AND {pre_session_col} > ?
        """, [median_travel]).fetchall()

        travel_filter = compute_stats(results_travel, f"{pre_session_col} > {median_travel/0.1:.0f} ticks")
        filters_tested.append(travel_filter)

    # Filter 2: Prior ORB sweep (if applicable)
    if prior_session_orb:
        results_sweep = con.execute(f"""
            SELECT
                orb_{orb_time}_outcome as outcome,
                orb_{orb_time}_r_multiple as r_multiple,
                orb_{orb_time}_mae as mae,
                orb_{orb_time}_mfe as mfe
            FROM daily_features_v2_half
            WHERE orb_{orb_time}_break_dir IS NOT NULL
              AND orb_{orb_time}_break_dir != 'NONE'
              AND orb_{prior_session_orb}_break_dir IS NOT NULL
              AND orb_{prior_session_orb}_break_dir != 'NONE'
              AND orb_{prior_session_orb}_mfe >= 1.0
        """).fetchall()

        sweep_filter = compute_stats(results_sweep, f"Prior {prior_session_orb} hit 1R MFE")
        filters_tested.append(sweep_filter)

    # Filter 3: Session range regime (if applicable)
    if session_range_col:
        median_range = con.execute(f"""
            SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {session_range_col})
            FROM daily_features_v2_half
            WHERE {session_range_col} IS NOT NULL
        """).fetchone()[0]

        results_range = con.execute(f"""
            SELECT
                orb_{orb_time}_outcome as outcome,
                orb_{orb_time}_r_multiple as r_multiple,
                orb_{orb_time}_mae as mae,
                orb_{orb_time}_mfe as mfe
            FROM daily_features_v2_half
            WHERE orb_{orb_time}_break_dir IS NOT NULL
              AND orb_{orb_time}_break_dir != 'NONE'
              AND {session_range_col} > ?
        """, [median_range]).fetchall()

        range_filter = compute_stats(results_range, f"{session_range_col} > {median_range/0.1:.0f} ticks")
        filters_tested.append(range_filter)

    con.close()

    # Print comparison
    print(f"{'Filter':<50} {'Trades':<10} {'Win%':<10} {'Exp':<12} {'Imp':<12} {'MFE/MAE':<10}")
    print("-" * 100)

    for f in filters_tested:
        improvement = ""
        if f != baseline and f["avg_r"] > baseline["avg_r"]:
            imp_pct = (f["avg_r"] - baseline["avg_r"]) / baseline["avg_r"] * 100
            improvement = f"+{imp_pct:.1f}%"

        print(f"{f['name']:<50} {f['n_trades']:<10} {f['win_rate']:<10.1f} {f['avg_r']:<12.4f} {improvement:<12} {f['mfe_mae_ratio']:<10.2f}")

    print()

    # Find best filter
    best = max(filters_tested, key=lambda x: x["avg_r"])

    if best != baseline and best["avg_r"] > baseline["avg_r"]:
        improvement_pct = (best["avg_r"] - baseline["avg_r"]) / baseline["avg_r"] * 100
        print(f"BEST FILTER: {best['name']}")
        print(f"  Improvement: +{improvement_pct:.1f}% ({baseline['avg_r']:+.4f}R -> {best['avg_r']:+.4f}R)")

        if improvement_pct > 15:
            print(f"  Status: STRONG improvement (>15%)")
        elif improvement_pct > 5:
            print(f"  Status: MODERATE improvement (5-15%)")
        else:
            print(f"  Status: WEAK improvement (<5%, likely noise)")
    else:
        print(f"NO FILTER IMPROVES: Keep baseline (no filter)")
        best = {"name": "NONE", "avg_r": baseline["avg_r"]}

    print()

    return best


def compute_stats(results, name):
    """Compute statistics from query results."""
    if not results:
        return {
            "name": name,
            "n_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0,
            "avg_r": 0,
            "mae_p50": 0,
            "mfe_p50": 0,
            "mfe_mae_ratio": 0
        }

    outcomes = [r[0] for r in results]
    r_multiples = [r[1] for r in results if r[1] is not None]
    maes = [r[2] for r in results if r[2] is not None]
    mfes = [r[3] for r in results if r[3] is not None]

    n_trades = len(outcomes)
    wins = sum(1 for o in outcomes if o == "WIN")
    losses = sum(1 for o in outcomes if o == "LOSS")
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    avg_r = np.mean(r_multiples) if r_multiples else 0
    mae_p50 = np.percentile(maes, 50) if maes else 0
    mfe_p50 = np.percentile(mfes, 50) if mfes else 0
    mfe_mae_ratio = mfe_p50 / mae_p50 if mae_p50 > 0 else 0

    return {
        "name": name,
        "n_trades": n_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "avg_r": avg_r,
        "mae_p50": mae_p50,
        "mfe_p50": mfe_p50,
        "mfe_mae_ratio": mfe_mae_ratio
    }


def main():
    print("=" * 100)
    print("FIND OPTIMAL FILTER FOR EACH ORB")
    print("=" * 100)
    print()

    optimal_filters = {}

    # 0900 - First ORB of Asia session
    best_0900 = test_orb_filters(
        orb_time="0900",
        orb_hour=9, orb_min=0,
        pre_session_col="pre_asia_range",
        prior_session_orb=None,  # First ORB of day
        session_range_col=None  # Can't use session range for first ORB
    )
    optimal_filters["0900"] = best_0900

    # 1000 - Second Asia ORB
    best_1000 = test_orb_filters(
        orb_time="1000",
        orb_hour=10, orb_min=0,
        pre_session_col="pre_asia_range",
        prior_session_orb="0900",  # Prior ORB
        session_range_col=None  # Still in Asia session
    )
    optimal_filters["1000"] = best_1000

    # 1100 - Third Asia ORB
    best_1100 = test_orb_filters(
        orb_time="1100",
        orb_hour=11, orb_min=0,
        pre_session_col="pre_asia_range",
        prior_session_orb="1000",  # Prior ORB
        session_range_col=None  # Still in Asia session
    )
    optimal_filters["1100"] = best_1100

    # 1800 - London ORB
    best_1800 = test_orb_filters(
        orb_time="1800",
        orb_hour=18, orb_min=0,
        pre_session_col="pre_london_range",
        prior_session_orb="1100",  # Last Asia ORB
        session_range_col="asia_range"  # Asia session complete
    )
    optimal_filters["1800"] = best_1800

    # 2300 - NY Futures ORB
    best_2300 = test_orb_filters(
        orb_time="2300",
        orb_hour=23, orb_min=0,
        pre_session_col="pre_ny_range",
        prior_session_orb="1800",  # London ORB
        session_range_col="london_range"  # London session complete
    )
    optimal_filters["2300"] = best_2300

    # 0030 - NYSE ORB
    best_0030 = test_orb_filters(
        orb_time="0030",
        orb_hour=0, orb_min=30,
        pre_session_col="pre_ny_range",
        prior_session_orb="2300",  # Prior NY ORB
        session_range_col="asia_range"  # Full day context
    )
    optimal_filters["0030"] = best_0030

    # Summary
    print("=" * 100)
    print("OPTIMAL FILTERS SUMMARY")
    print("=" * 100)
    print()

    print(f"{'ORB':<8} {'Optimal Filter':<60} {'Expectancy':<15}")
    print("-" * 100)

    for orb_time in ["0900", "1000", "1100", "1800", "2300", "0030"]:
        best = optimal_filters[orb_time]
        print(f"{orb_time:<8} {best['name']:<60} {best['avg_r']:+.4f}R")

    print()
    print("=" * 100)
    print("Next Step: Run final backtest with optimal filters applied to each ORB")
    print("=" * 100)

    return optimal_filters


if __name__ == "__main__":
    optimal_filters = main()
