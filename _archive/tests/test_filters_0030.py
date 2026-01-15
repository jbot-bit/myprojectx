"""
Run #3: Test Structural Filters for Weak Session (0030 ORB)
============================================================

0030 is the weakest ORB:
- Expectancy: +0.231R (vs +0.387-0.449R for others)
- MFE/MAE: 2.60x (vs 3.54-5.00x for others)
- Bad breaks: 38.4% (vs 27-32% for others)

Test filters one at a time:
1. Pre-session travel (high/low)
2. Prior session sweep/no sweep
3. Asia range regime

Purpose: See if context can improve weak session performance.
"""

import duckdb
import numpy as np

DB_PATH = "gold.db"


def test_no_filter():
    """Baseline: no filter"""
    con = duckdb.connect(DB_PATH)

    results = con.execute("""
        SELECT
            orb_0030_outcome as outcome,
            orb_0030_r_multiple as r_multiple,
            orb_0030_mae as mae,
            orb_0030_mfe as mfe
        FROM daily_features_v2_half
        WHERE orb_0030_break_dir IS NOT NULL
          AND orb_0030_break_dir != 'NONE'
    """).fetchall()

    con.close()

    outcomes = [r[0] for r in results]
    r_multiples = [r[1] for r in results if r[1] is not None]
    maes = [r[2] for r in results if r[2] is not None]
    mfes = [r[3] for r in results if r[3] is not None]

    n_trades = len(outcomes)
    wins = sum(1 for o in outcomes if o == "WIN")
    losses = sum(1 for o in outcomes if o == "LOSS")
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    avg_r = np.mean(r_multiples)
    mae_p50 = np.percentile(maes, 50)
    mfe_p50 = np.percentile(mfes, 50)
    mfe_mae_ratio = mfe_p50 / mae_p50 if mae_p50 > 0 else 0

    return {
        "name": "NO FILTER (baseline)",
        "n_trades": n_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "avg_r": avg_r,
        "mae_p50": mae_p50,
        "mfe_p50": mfe_p50,
        "mfe_mae_ratio": mfe_mae_ratio
    }


def test_pre_ny_travel_filter():
    """Filter: Only trade 0030 if pre_ny_travel (23:00-00:30) > threshold"""
    con = duckdb.connect(DB_PATH)

    # Calculate median pre_ny_travel
    median_travel = con.execute("""
        SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pre_ny_range)
        FROM daily_features_v2_half
        WHERE pre_ny_range IS NOT NULL
    """).fetchone()[0]

    print(f"  Median pre_ny_travel: {median_travel / 0.1:.1f} ticks")
    print()

    # Test filter: only trade if pre_ny_travel > median
    results = con.execute("""
        SELECT
            orb_0030_outcome as outcome,
            orb_0030_r_multiple as r_multiple,
            orb_0030_mae as mae,
            orb_0030_mfe as mfe
        FROM daily_features_v2_half
        WHERE orb_0030_break_dir IS NOT NULL
          AND orb_0030_break_dir != 'NONE'
          AND pre_ny_range > ?
    """, [median_travel]).fetchall()

    con.close()

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
        "name": f"Pre-NY travel > {median_travel / 0.1:.1f} ticks",
        "n_trades": n_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "avg_r": avg_r,
        "mae_p50": mae_p50,
        "mfe_p50": mfe_p50,
        "mfe_mae_ratio": mfe_mae_ratio
    }


def test_ny_session_sweep_filter():
    """Filter: Only trade 0030 if prior 2300 session swept high or low"""
    con = duckdb.connect(DB_PATH)

    # NY session = 2300 ORB
    # Sweep = 2300 ORB broke AND reached 1R target
    results = con.execute("""
        SELECT
            orb_0030_outcome as outcome,
            orb_0030_r_multiple as r_multiple,
            orb_0030_mae as mae,
            orb_0030_mfe as mfe
        FROM daily_features_v2_half
        WHERE orb_0030_break_dir IS NOT NULL
          AND orb_0030_break_dir != 'NONE'
          AND orb_2300_break_dir IS NOT NULL
          AND orb_2300_break_dir != 'NONE'
          AND orb_2300_mfe >= 1.0
    """).fetchall()

    con.close()

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
        "name": "Prior 2300 ORB hit 1R MFE",
        "n_trades": n_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "avg_r": avg_r,
        "mae_p50": mae_p50,
        "mfe_p50": mfe_p50,
        "mfe_mae_ratio": mfe_mae_ratio
    }


def test_asia_range_filter():
    """Filter: Only trade 0030 if Asia range (09:00-17:00) > threshold"""
    con = duckdb.connect(DB_PATH)

    # Calculate median Asia range
    median_asia_range = con.execute("""
        SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY asia_range)
        FROM daily_features_v2_half
        WHERE asia_range IS NOT NULL
    """).fetchone()[0]

    print(f"  Median Asia range: {median_asia_range / 0.1:.1f} ticks")
    print()

    # Test filter: only trade if Asia range > median (trending day)
    results = con.execute("""
        SELECT
            orb_0030_outcome as outcome,
            orb_0030_r_multiple as r_multiple,
            orb_0030_mae as mae,
            orb_0030_mfe as mfe
        FROM daily_features_v2_half
        WHERE orb_0030_break_dir IS NOT NULL
          AND orb_0030_break_dir != 'NONE'
          AND asia_range > ?
    """, [median_asia_range]).fetchall()

    con.close()

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
        "name": f"Asia range > {median_asia_range / 0.1:.1f} ticks",
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
    print("RUN #3: STRUCTURAL FILTERS FOR WEAK SESSION (0030 ORB)")
    print("=" * 100)
    print()

    # Test each filter
    print("Testing filters (one at a time)...")
    print()

    baseline = test_no_filter()

    print("Filter #1: Pre-NY Travel")
    print("-" * 100)
    filter1 = test_pre_ny_travel_filter()

    print("Filter #2: Prior 2300 ORB Sweep")
    print("-" * 100)
    filter2 = test_ny_session_sweep_filter()

    print("Filter #3: Asia Range Regime")
    print("-" * 100)
    filter3 = test_asia_range_filter()

    # Compare results
    print("=" * 100)
    print("RESULTS COMPARISON")
    print("=" * 100)
    print()

    results = [baseline, filter1, filter2, filter3]

    print(f"{'Filter':<40} {'Trades':<10} {'Win Rate':<12} {'Avg R':<12} {'MAE P50':<12} {'MFE P50':<12} {'MFE/MAE':<10}")
    print("-" * 100)

    for r in results:
        improvement = ""
        if r != baseline and r["avg_r"] > baseline["avg_r"]:
            improvement = f" (+{r['avg_r'] - baseline['avg_r']:.4f}R)"

        print(f"{r['name']:<40} {r['n_trades']:<10} {r['win_rate']:<12.1f} {r['avg_r']:<12.4f}{improvement:<12} {r['mae_p50']:<12.3f} {r['mfe_p50']:<12.3f} {r['mfe_mae_ratio']:<10.2f}")

    print()
    print("=" * 100)
    print("KEY FINDING: Do filters improve 0030 ORB performance?")
    print("=" * 100)
    print()

    # Find best filter
    best = max(results[1:], key=lambda x: x["avg_r"])

    if best["avg_r"] > baseline["avg_r"]:
        improvement_pct = (best["avg_r"] - baseline["avg_r"]) / baseline["avg_r"] * 100
        print(f"YES: '{best['name']}' improves expectancy by {improvement_pct:.1f}%")
        print(f"  Baseline: {baseline['avg_r']:+.4f}R per trade")
        print(f"  Filtered: {best['avg_r']:+.4f}R per trade")
        print(f"  Improvement: {best['avg_r'] - baseline['avg_r']:+.4f}R")
        print()

        if improvement_pct > 20:
            print("STRONG improvement (>20%) - filter is meaningful")
        elif improvement_pct > 10:
            print("MODERATE improvement (10-20%) - filter may be useful")
        else:
            print("WEAK improvement (<10%) - likely statistical noise")
    else:
        print("NO: None of the tested filters improve expectancy")
        print("The 0030 ORB is just structurally weaker (but still profitable)")
        print()
        print("Recommendation: Keep trading 0030 without filters OR skip it entirely")

    print()


if __name__ == "__main__":
    main()
