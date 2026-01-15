"""
Run #2: Per-Session Detailed Analysis
======================================

For each ORB time, output:
- Win rate, avg R
- P50/P90 MAE and MFE
- % trades with MFE >= 1R but still lost (execution/stop issue)

Purpose: Shows whether losses are "normal drawdown" or structural failure.
"""

import duckdb
import numpy as np

DB_PATH = "gold.db"

con = duckdb.connect(DB_PATH)

print("=" * 100)
print("PER-SESSION DETAILED ANALYSIS")
print("=" * 100)
print("Source: daily_features_v2_half (Half SL, ORB-anchored)")
print()

orb_times = ["0900", "1000", "1100", "1800", "2300", "0030"]

for orb_time in orb_times:
    print("=" * 100)
    print(f"ORB {orb_time}")
    print("=" * 100)
    print()

    # Get all metrics for this ORB
    query = f"""
        SELECT
            date_local,
            orb_{orb_time}_break_dir as break_dir,
            orb_{orb_time}_outcome as outcome,
            orb_{orb_time}_r_multiple as r_multiple,
            orb_{orb_time}_mae as mae,
            orb_{orb_time}_mfe as mfe,
            orb_{orb_time}_size / 0.1 as orb_ticks,
            orb_{orb_time}_risk_ticks as risk_ticks
        FROM daily_features_v2_half
        WHERE orb_{orb_time}_break_dir IS NOT NULL
          AND orb_{orb_time}_break_dir != 'NONE'
    """

    results = con.execute(query).fetchall()

    if not results:
        print("No trades found")
        print()
        continue

    # Parse data
    trades = []
    for row in results:
        date_local, break_dir, outcome, r_multiple, mae, mfe, orb_ticks, risk_ticks = row
        if mae is not None and mfe is not None:
            trades.append({
                "date": date_local,
                "break_dir": break_dir,
                "outcome": outcome,
                "r_multiple": r_multiple,
                "mae": mae,
                "mfe": mfe,
                "orb_ticks": orb_ticks,
                "risk_ticks": risk_ticks
            })

    n_trades = len(trades)
    wins = sum(1 for t in trades if t["outcome"] == "WIN")
    losses = sum(1 for t in trades if t["outcome"] == "LOSS")
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    avg_r = np.mean([t["r_multiple"] for t in trades if t["r_multiple"] is not None])
    total_r = sum(t["r_multiple"] for t in trades if t["r_multiple"] is not None)

    # MAE/MFE distributions
    maes = [t["mae"] for t in trades if t["mae"] is not None]
    mfes = [t["mfe"] for t in trades if t["mfe"] is not None]

    mae_p50 = np.percentile(maes, 50) if maes else 0
    mae_p90 = np.percentile(maes, 90) if maes else 0
    mfe_p50 = np.percentile(mfes, 50) if mfes else 0
    mfe_p90 = np.percentile(mfes, 90) if mfes else 0

    avg_orb_ticks = np.mean([t["orb_ticks"] for t in trades])
    avg_risk_ticks = np.mean([t["risk_ticks"] for t in trades])

    # Failure mode: MFE >= 1R but still lost
    mfe_1r_but_lost = sum(1 for t in trades if t["mfe"] >= 1.0 and t["outcome"] == "LOSS")
    pct_mfe_1r_but_lost = (mfe_1r_but_lost / losses * 100) if losses > 0 else 0

    # Additional failure modes
    mae_gt_mfe = sum(1 for t in trades if t["mae"] > t["mfe"])
    pct_mae_gt_mfe = (mae_gt_mfe / n_trades * 100) if n_trades > 0 else 0

    # Print results
    print(f"BASIC STATS")
    print("-" * 100)
    print(f"Trades: {n_trades}")
    print(f"Wins: {wins} | Losses: {losses}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Total R: {total_r:+.1f}R")
    print(f"Avg R per trade: {avg_r:+.4f}R")
    print(f"Avg ORB size: {avg_orb_ticks:.1f} ticks")
    print(f"Avg Risk (Half SL): {avg_risk_ticks:.1f} ticks")
    print()

    print(f"MAE/MFE DISTRIBUTIONS (ORB-anchored, in R-multiples)")
    print("-" * 100)
    print(f"MAE P50: {mae_p50:.3f}R | MAE P90: {mae_p90:.3f}R")
    print(f"MFE P50: {mfe_p50:.3f}R | MFE P90: {mfe_p90:.3f}R")
    print(f"MFE/MAE ratio (median): {mfe_p50/mae_p50:.2f}x" if mae_p50 > 0 else "MFE/MAE ratio: N/A")
    print()

    print(f"FAILURE MODE ANALYSIS")
    print("-" * 100)
    print(f"Trades with MFE >= 1R but still LOST: {mfe_1r_but_lost} ({pct_mfe_1r_but_lost:.1f}% of losses)")
    print(f"Trades with MAE > MFE (bad breaks): {mae_gt_mfe} ({pct_mae_gt_mfe:.1f}% of all trades)")
    print()

    if pct_mfe_1r_but_lost > 30:
        print("WARNING: >30% of losses hit 1R profit but still lost")
        print("         => Stop placement or execution issue")
    elif pct_mfe_1r_but_lost > 15:
        print("NOTE: 15-30% of losses hit 1R profit but still lost")
        print("      => Some pullback after favorable move (normal)")
    else:
        print("OK: <15% of losses hit 1R profit but still lost")
        print("    => Losses are clean stops, not execution failures")

    print()

    if pct_mae_gt_mfe > 40:
        print("WARNING: >40% of trades have MAE > MFE (bad breaks)")
        print("         => Poor entry timing or adverse selection")
    else:
        print("OK: Most trades have MFE > MAE (good directional follow-through)")

    print()

# Session summary
print("=" * 100)
print("SESSION SUMMARY")
print("=" * 100)
print()

sessions = {
    "ASIA": ["0900", "1000", "1100"],
    "LONDON": ["1800"],
    "NY": ["2300", "0030"]
}

for session_name, orb_list in sessions.items():
    print(f"--- {session_name} ---")

    session_data = []
    for orb_time in orb_list:
        query = f"""
            SELECT
                orb_{orb_time}_outcome as outcome,
                orb_{orb_time}_r_multiple as r_multiple,
                orb_{orb_time}_mae as mae,
                orb_{orb_time}_mfe as mfe
            FROM daily_features_v2_half
            WHERE orb_{orb_time}_break_dir IS NOT NULL
              AND orb_{orb_time}_break_dir != 'NONE'
              AND orb_{orb_time}_mae IS NOT NULL
        """
        results = con.execute(query).fetchall()
        session_data.extend(results)

    if not session_data:
        continue

    outcomes = [r[0] for r in session_data]
    r_multiples = [r[1] for r in session_data if r[1] is not None]
    maes = [r[2] for r in session_data if r[2] is not None]
    mfes = [r[3] for r in session_data if r[3] is not None]

    n_trades = len(outcomes)
    wins = sum(1 for o in outcomes if o == "WIN")
    losses = sum(1 for o in outcomes if o == "LOSS")
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    avg_r = np.mean(r_multiples)
    mae_p50 = np.percentile(maes, 50)
    mfe_p50 = np.percentile(mfes, 50)

    mfe_1r_but_lost = sum(1 for r in session_data if r[3] >= 1.0 and r[0] == "LOSS")
    pct_mfe_1r_but_lost = (mfe_1r_but_lost / losses * 100) if losses > 0 else 0

    print(f"  ORBs: {', '.join(orb_list)}")
    print(f"  Trades: {n_trades} | Win Rate: {win_rate:.1f}% | Avg R: {avg_r:+.4f}R")
    print(f"  MAE P50: {mae_p50:.3f}R | MFE P50: {mfe_p50:.3f}R | Ratio: {mfe_p50/mae_p50:.2f}x")
    print(f"  MFE >= 1R but lost: {mfe_1r_but_lost} ({pct_mfe_1r_but_lost:.1f}% of losses)")
    print()

con.close()

print("=" * 100)
print("KEY FINDING: Failure modes by session")
print("=" * 100)
print()
print("Look for sessions with:")
print("- High % of MFE >= 1R but lost (>30%) => stop/execution issue")
print("- High % of MAE > MFE (>40%) => poor directional follow-through")
print("- Low MFE/MAE ratio (<2x) => weak edge")
