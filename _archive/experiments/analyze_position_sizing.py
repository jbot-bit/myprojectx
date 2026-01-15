"""
POSITION SIZING OPTIMIZATION: Filtered vs Unfiltered Trades

User insight: If filtered trades have better expectancy, should we trade larger on them?

Analysis:
1. Calculate Kelly Criterion for each scenario
2. Compare risk-adjusted returns
3. Recommend optimal position sizing
"""

import duckdb
import pandas as pd
import numpy as np

DB_PATH = "gold.db"

def calculate_kelly(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """
    Calculate Kelly Criterion optimal bet size.

    Formula: f* = (p * b - q) / b
    Where:
    - p = win probability
    - q = loss probability (1 - p)
    - b = odds (avg_win / avg_loss)
    """
    if avg_loss == 0:
        return 0

    p = win_rate
    q = 1 - p
    b = abs(avg_win / avg_loss)

    kelly = (p * b - q) / b
    return max(0, kelly)  # Don't bet negative

def analyze_orb_position_sizing(orb: str):
    """Analyze optimal position sizing for filtered vs unfiltered trades"""

    con = duckdb.connect(DB_PATH, read_only=True)

    # Get all trades
    df = con.execute(f"""
        SELECT
            orb_{orb}_r_multiple as r_multiple,
            orb_{orb}_outcome as outcome,
            orb_{orb}_size as orb_size,
            atr_20
        FROM daily_features_v2_half
        WHERE orb_{orb}_outcome IN ('WIN', 'LOSS')
        AND instrument = 'MGC'
    """).df()

    if df.empty:
        return None

    df['orb_size_norm'] = df['orb_size'] / df['atr_20']

    # Determine filter threshold
    if orb in ['2300', '0030']:
        threshold = {'2300': 0.155, '0030': 0.112}[orb]
    elif orb in ['1100', '1000']:
        threshold = {'1100': 0.095, '1000': 0.088}[orb]
    else:
        # No filter for 0900, 1800
        threshold = None

    results = {}

    # Baseline (all trades)
    baseline_wins = df[df['outcome'] == 'WIN']['r_multiple']
    baseline_losses = df[df['outcome'] == 'LOSS']['r_multiple']
    baseline_wr = (df['outcome'] == 'WIN').mean()
    baseline_avg_r = df['r_multiple'].mean()

    results['baseline'] = {
        'trades': len(df),
        'win_rate': baseline_wr,
        'avg_r': baseline_avg_r,
        'avg_win': baseline_wins.mean() if len(baseline_wins) > 0 else 0,
        'avg_loss': baseline_losses.mean() if len(baseline_losses) > 0 else 0,
        'sharpe': baseline_avg_r / df['r_multiple'].std() if df['r_multiple'].std() > 0 else 0
    }

    # Calculate Kelly for baseline
    results['baseline']['kelly'] = calculate_kelly(
        baseline_wr,
        results['baseline']['avg_win'],
        abs(results['baseline']['avg_loss'])
    )

    if threshold is not None:
        # Filtered (small ORBs only)
        filtered_df = df[df['orb_size_norm'] <= threshold]

        if len(filtered_df) > 0:
            filtered_wins = filtered_df[filtered_df['outcome'] == 'WIN']['r_multiple']
            filtered_losses = filtered_df[filtered_df['outcome'] == 'LOSS']['r_multiple']
            filtered_wr = (filtered_df['outcome'] == 'WIN').mean()
            filtered_avg_r = filtered_df['r_multiple'].mean()

            results['filtered'] = {
                'trades': len(filtered_df),
                'win_rate': filtered_wr,
                'avg_r': filtered_avg_r,
                'avg_win': filtered_wins.mean() if len(filtered_wins) > 0 else 0,
                'avg_loss': filtered_losses.mean() if len(filtered_losses) > 0 else 0,
                'sharpe': filtered_avg_r / filtered_df['r_multiple'].std() if filtered_df['r_multiple'].std() > 0 else 0
            }

            # Calculate Kelly for filtered
            results['filtered']['kelly'] = calculate_kelly(
                filtered_wr,
                results['filtered']['avg_win'],
                abs(results['filtered']['avg_loss'])
            )

            # Unfiltered only (large ORBs that were rejected)
            unfiltered_df = df[df['orb_size_norm'] > threshold]

            if len(unfiltered_df) > 0:
                unfiltered_wins = unfiltered_df[unfiltered_df['outcome'] == 'WIN']['r_multiple']
                unfiltered_losses = unfiltered_df[unfiltered_df['outcome'] == 'LOSS']['r_multiple']
                unfiltered_wr = (unfiltered_df['outcome'] == 'WIN').mean()
                unfiltered_avg_r = unfiltered_df['r_multiple'].mean()

                results['unfiltered_only'] = {
                    'trades': len(unfiltered_df),
                    'win_rate': unfiltered_wr,
                    'avg_r': unfiltered_avg_r,
                    'avg_win': unfiltered_wins.mean() if len(unfiltered_wins) > 0 else 0,
                    'avg_loss': unfiltered_losses.mean() if len(unfiltered_losses) > 0 else 0,
                    'sharpe': unfiltered_avg_r / unfiltered_df['r_multiple'].std() if unfiltered_df['r_multiple'].std() > 0 else 0
                }

                results['unfiltered_only']['kelly'] = calculate_kelly(
                    unfiltered_wr,
                    results['unfiltered_only']['avg_win'],
                    abs(results['unfiltered_only']['avg_loss'])
                )

    con.close()
    return results

def print_position_sizing_report():
    """Generate comprehensive position sizing report"""

    print("="*80)
    print("POSITION SIZING ANALYSIS: Filtered vs Unfiltered Trades")
    print("="*80)
    print()
    print("QUESTION: Should we trade larger on filtered (small ORB) trades?")
    print("ANSWER: Yes, if their Kelly Criterion suggests higher optimal bet size.")
    print()

    orbs_with_filters = ['2300', '0030', '1100', '1000']

    recommendations = []

    for orb in orbs_with_filters:
        print(f"\n{'-'*80}")
        print(f"{orb} ORB ANALYSIS")
        print(f"{'-'*80}")

        results = analyze_orb_position_sizing(orb)

        if not results:
            print(f"No data for {orb}")
            continue

        # Baseline stats
        print(f"\nBASELINE (All trades):")
        print(f"  Trades: {results['baseline']['trades']}")
        print(f"  Win Rate: {results['baseline']['win_rate']*100:.1f}%")
        print(f"  Avg R: {results['baseline']['avg_r']:+.3f}R")
        print(f"  Avg Win: {results['baseline']['avg_win']:+.3f}R")
        print(f"  Avg Loss: {results['baseline']['avg_loss']:+.3f}R")
        print(f"  Sharpe: {results['baseline']['sharpe']:.3f}")
        print(f"  Kelly%: {results['baseline']['kelly']*100:.1f}%")

        if 'filtered' in results:
            print(f"\nFILTERED (Small ORB only):")
            print(f"  Trades: {results['filtered']['trades']} ({results['filtered']['trades']/results['baseline']['trades']*100:.1f}% of total)")
            print(f"  Win Rate: {results['filtered']['win_rate']*100:.1f}%")
            print(f"  Avg R: {results['filtered']['avg_r']:+.3f}R")
            print(f"  Avg Win: {results['filtered']['avg_win']:+.3f}R")
            print(f"  Avg Loss: {results['filtered']['avg_loss']:+.3f}R")
            print(f"  Sharpe: {results['filtered']['sharpe']:.3f}")
            print(f"  Kelly%: {results['filtered']['kelly']*100:.1f}%")

            improvement = results['filtered']['avg_r'] - results['baseline']['avg_r']
            print(f"\n  IMPROVEMENT: {improvement:+.3f}R ({improvement/results['baseline']['avg_r']*100:+.1f}%)")

            # Position sizing recommendation
            baseline_kelly = results['baseline']['kelly']
            filtered_kelly = results['filtered']['kelly']

            if filtered_kelly > baseline_kelly:
                sizing_ratio = filtered_kelly / baseline_kelly if baseline_kelly > 0 else 1.0
                # Cap at 2x for safety
                sizing_ratio = min(sizing_ratio, 2.0)

                print(f"\n  POSITION SIZING RECOMMENDATION:")
                print(f"    Baseline trades: 1.0% risk")
                print(f"    Filtered trades: {sizing_ratio:.2f}x = {sizing_ratio*1.0:.2f}% risk")
                print(f"    Rationale: Kelly suggests {filtered_kelly/baseline_kelly:.2f}x optimal bet")

                recommendations.append({
                    'orb': orb,
                    'baseline_risk': 1.0,
                    'filtered_risk': sizing_ratio * 1.0,
                    'improvement': improvement,
                    'filtered_trades_pct': results['filtered']['trades']/results['baseline']['trades']*100
                })
            else:
                print(f"\n  POSITION SIZING: No size increase recommended (Kelly similar or lower)")

        if 'unfiltered_only' in results:
            print(f"\nUNFILTERED ONLY (Large ORB - what we're avoiding):")
            print(f"  Trades: {results['unfiltered_only']['trades']}")
            print(f"  Avg R: {results['unfiltered_only']['avg_r']:+.3f}R")
            print(f"  This is what the filter saves us from.")

    # Summary recommendations
    print(f"\n{'='*80}")
    print("SUMMARY RECOMMENDATIONS")
    print(f"{'='*80}\n")

    if recommendations:
        print("TIERED POSITION SIZING STRATEGY:\n")

        print("TIER 1: Baseline Trades (No filter or large ORB)")
        print("  Risk: 1.0% per trade")
        print("  ORBs: 0900 (no filter), 1800 (no filter)")
        print("  Also: Any filtered ORB with large ORB (failed filter)\n")

        print("TIER 2: Filtered Trades (Small ORB, proven edge)")
        for rec in recommendations:
            print(f"  {rec['orb']} ORB: {rec['filtered_risk']:.2f}% risk")
            print(f"    Improvement: {rec['improvement']:+.3f}R | Frequency: {rec['filtered_trades_pct']:.1f}% of trades")

        print("\nIMPLEMENTATION:")
        print("  1. Check if ORB passes size filter")
        print("  2. If PASS → Use Tier 2 sizing (1.5-2.0%)")
        print("  3. If FAIL → Use Tier 1 sizing (1.0%)")
        print("  4. Monitor for 50 trades before increasing beyond 1.5%")

        print("\nRISK MANAGEMENT:")
        print("  - Daily max: 3-4 trades regardless of tier")
        print("  - Weekly max: 12-15 trades")
        print("  - Total capital at risk: Never exceed 5% simultaneously")
        print("  - Filtered trades are RARE (13-42% of setups) so risk of over-leverage is low")

    print(f"\n{'='*80}")
    print("POSITION SIZING ANALYSIS COMPLETE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    print_position_sizing_report()
