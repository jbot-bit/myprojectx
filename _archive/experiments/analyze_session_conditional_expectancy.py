"""
Session-based conditional expectancy analysis.

Attach prior-session labels to future ORB trades and compute conditional expectancies.

CRITICAL RULES:
1. Labels from Session A → ORB trades in Session B (no lookahead)
2. One condition at a time (no stacking)
3. Test BOTH continuation AND reversal for sweep conditions
4. Report only: sample_size >= 200, delta >= +0.10R
"""

import duckdb
import pandas as pd
from typing import Dict, List, Tuple

conn = duckdb.connect("gold.db")


def get_orb_trades(orb_time: str, table_name: str = "orb_trades_5m_exec") -> pd.DataFrame:
    """
    Get ORB trades for a specific ORB time from specified trade table.
    Returns trades with date_local, direction, r_multiple, outcome.
    """
    query = f"""
    SELECT
        date_local,
        direction,
        r_multiple,
        outcome,
        entry_price,
        stop_price,
        target_price
    FROM {table_name}
    WHERE orb = '{orb_time}'
    AND direction IS NOT NULL
    AND r_multiple IS NOT NULL
    """
    return conn.execute(query).fetchdf()


def attach_prior_session_labels(
    orb_trades: pd.DataFrame,
    label_columns: List[str],
    same_day: bool = True
) -> pd.DataFrame:
    """
    Attach prior-session labels to ORB trades.

    Args:
        orb_trades: DataFrame with date_local and trade data
        label_columns: List of column names from session_labels to attach
        same_day: If True, use same date_local. If False, use previous day (for overnight ORBs)

    Returns:
        DataFrame with ORB trades + labels attached
    """

    # Build column selection
    cols_str = ", ".join([f"sl.{col}" for col in label_columns])

    if same_day:
        # Same day join (e.g., Asia labels -> London ORB on same trading day)
        join_condition = "t.date_local = sl.date_local"
    else:
        # Previous day join (would be needed if labels from Day N-1 -> Day N)
        join_condition = "t.date_local = sl.date_local + INTERVAL '1 day'"

    query = f"""
    SELECT
        t.*,
        {cols_str}
    FROM orb_trades t
    LEFT JOIN session_labels sl ON {join_condition}
    """

    return conn.execute(query).fetchdf()


def compute_baseline_expectancy(trades: pd.DataFrame) -> Dict:
    """
    Compute baseline expectancy (no condition).
    """
    valid_trades = trades[trades['r_multiple'].notna()]

    return {
        'sample_size': len(valid_trades),
        'avg_r': valid_trades['r_multiple'].mean() if len(valid_trades) > 0 else 0.0,
        'win_rate': (valid_trades['outcome'] == 'WIN').sum() / len(valid_trades) if len(valid_trades) > 0 else 0.0,
        'avg_win': valid_trades[valid_trades['outcome'] == 'WIN']['r_multiple'].mean() if len(valid_trades[valid_trades['outcome'] == 'WIN']) > 0 else 0.0,
        'avg_loss': valid_trades[valid_trades['outcome'] == 'LOSS']['r_multiple'].mean() if len(valid_trades[valid_trades['outcome'] == 'LOSS']) > 0 else 0.0,
    }


def compute_conditional_expectancy(
    trades: pd.DataFrame,
    condition_col: str,
    condition_value
) -> Dict:
    """
    Compute expectancy when condition is met.
    """
    filtered = trades[trades[condition_col] == condition_value]
    return compute_baseline_expectancy(filtered)


def compute_directional_conditional_expectancy(
    trades: pd.DataFrame,
    condition_col: str,
    condition_value,
    direction: str
) -> Dict:
    """
    Compute expectancy when condition is met AND direction matches.
    Used for testing continuation vs reversal.
    """
    filtered = trades[
        (trades[condition_col] == condition_value) &
        (trades['direction'] == direction)
    ]
    return compute_baseline_expectancy(filtered)


def analyze_single_condition(
    orb_trades_with_labels: pd.DataFrame,
    label_name: str,
    label_value,
    baseline: Dict,
    min_sample_size: int = 200,
    min_delta: float = 0.10
) -> Dict:
    """
    Analyze a single condition and return results if significant.

    Returns dict with condition analysis, or None if not significant.
    """
    cond_stats = compute_conditional_expectancy(orb_trades_with_labels, label_name, label_value)

    # Check significance thresholds
    if cond_stats['sample_size'] < min_sample_size:
        return None

    delta = cond_stats['avg_r'] - baseline['avg_r']

    if abs(delta) < min_delta:
        return None

    return {
        'label': label_name,
        'value': label_value,
        'sample_size': cond_stats['sample_size'],
        'avg_r': cond_stats['avg_r'],
        'baseline_avg_r': baseline['avg_r'],
        'delta': delta,
        'win_rate': cond_stats['win_rate'],
        'avg_win': cond_stats['avg_win'],
        'avg_loss': cond_stats['avg_loss'],
    }


def analyze_sweep_continuation_vs_reversal(
    orb_trades_with_labels: pd.DataFrame,
    sweep_label: str,
    continuation_direction: str,
    reversal_direction: str,
    baseline: Dict,
    min_sample_size: int = 200,
    min_delta: float = 0.10
) -> List[Dict]:
    """
    For sweep labels, test BOTH continuation and reversal.

    Example:
        sweep_label = 'asia_sweep_high'
        continuation_direction = 'UP' (price swept high, then broke UP)
        reversal_direction = 'DOWN' (price swept high, then broke DOWN)
    """
    results = []

    # Test continuation
    cont_stats = compute_directional_conditional_expectancy(
        orb_trades_with_labels, sweep_label, True, continuation_direction
    )

    if cont_stats['sample_size'] >= min_sample_size:
        delta_cont = cont_stats['avg_r'] - baseline['avg_r']
        if abs(delta_cont) >= min_delta:
            results.append({
                'label': f"{sweep_label} + {continuation_direction}",
                'hypothesis': 'CONTINUATION',
                'sample_size': cont_stats['sample_size'],
                'avg_r': cont_stats['avg_r'],
                'baseline_avg_r': baseline['avg_r'],
                'delta': delta_cont,
                'win_rate': cont_stats['win_rate'],
                'avg_win': cont_stats['avg_win'],
                'avg_loss': cont_stats['avg_loss'],
            })

    # Test reversal
    rev_stats = compute_directional_conditional_expectancy(
        orb_trades_with_labels, sweep_label, True, reversal_direction
    )

    if rev_stats['sample_size'] >= min_sample_size:
        delta_rev = rev_stats['avg_r'] - baseline['avg_r']
        if abs(delta_rev) >= min_delta:
            results.append({
                'label': f"{sweep_label} + {reversal_direction}",
                'hypothesis': 'REVERSAL',
                'sample_size': rev_stats['sample_size'],
                'avg_r': rev_stats['avg_r'],
                'baseline_avg_r': baseline['avg_r'],
                'delta': delta_rev,
                'win_rate': rev_stats['win_rate'],
                'avg_win': rev_stats['avg_win'],
                'avg_loss': rev_stats['avg_loss'],
            })

    return results


def run_full_analysis(
    table_name: str = "orb_trades_5m_exec",
    min_sample_size: int = 200,
    min_delta: float = 0.10
):
    """
    Run full conditional expectancy analysis for all ORB times and conditions.
    """

    print(f"\n{'='*80}")
    print(f"SESSION CONDITIONAL EXPECTANCY ANALYSIS")
    print(f"Trade Table: {table_name}")
    print(f"Min Sample Size: {min_sample_size}")
    print(f"Min Delta: +{min_delta}R")
    print(f"{'='*80}\n")

    all_results = []

    # ============================================
    # LONDON ORB (1800) with ASIA labels
    # ============================================
    print("\n" + "="*80)
    print("LONDON ORB (1800) <- ASIA SESSION LABELS")
    print("="*80)

    london_trades = get_orb_trades('1800', table_name)
    print(f"\nLondon ORB trades: {len(london_trades)}")

    if len(london_trades) == 0:
        print("No London ORB trades found. Skipping.")
    else:
        # Attach Asia labels
        asia_label_cols = ['asia_sweep_high', 'asia_sweep_low', 'asia_range_type',
                          'asia_net_direction', 'asia_failure']

        london_with_asia = attach_prior_session_labels(
            london_trades, asia_label_cols, same_day=True
        )

        baseline_london = compute_baseline_expectancy(london_trades)
        print(f"\nBaseline (London ORB):")
        print(f"  Sample: {baseline_london['sample_size']}")
        print(f"  Avg R: {baseline_london['avg_r']:.3f}R")
        print(f"  Win Rate: {baseline_london['win_rate']:.1%}")

        # Test sweep conditions with continuation/reversal
        print("\n--- SWEEP CONDITIONS (Continuation vs Reversal) ---")

        sweep_results = analyze_sweep_continuation_vs_reversal(
            london_with_asia, 'asia_sweep_high', 'UP', 'DOWN',
            baseline_london, min_sample_size, min_delta
        )
        all_results.extend(sweep_results)
        for r in sweep_results:
            print(f"\n{r['label']} ({r['hypothesis']}):")
            print(f"  N={r['sample_size']}, Avg R={r['avg_r']:.3f}, Delta={r['delta']:+.3f}R, WR={r['win_rate']:.1%}")

        sweep_results = analyze_sweep_continuation_vs_reversal(
            london_with_asia, 'asia_sweep_low', 'DOWN', 'UP',
            baseline_london, min_sample_size, min_delta
        )
        all_results.extend(sweep_results)
        for r in sweep_results:
            print(f"\n{r['label']} ({r['hypothesis']}):")
            print(f"  N={r['sample_size']}, Avg R={r['avg_r']:.3f}, Delta={r['delta']:+.3f}R, WR={r['win_rate']:.1%}")

        # Test categorical conditions
        print("\n--- CATEGORICAL CONDITIONS ---")

        for cat_label in ['asia_range_type', 'asia_net_direction']:
            unique_values = london_with_asia[cat_label].dropna().unique()
            for val in unique_values:
                result = analyze_single_condition(
                    london_with_asia, cat_label, val, baseline_london,
                    min_sample_size, min_delta
                )
                if result:
                    all_results.append(result)
                    print(f"\n{result['label']}={result['value']}:")
                    print(f"  N={result['sample_size']}, Avg R={result['avg_r']:.3f}, Delta={result['delta']:+.3f}R, WR={result['win_rate']:.1%}")

        # Test boolean conditions
        print("\n--- BOOLEAN CONDITIONS ---")

        for bool_label in ['asia_failure']:
            for val in [True, False]:
                result = analyze_single_condition(
                    london_with_asia, bool_label, val, baseline_london,
                    min_sample_size, min_delta
                )
                if result:
                    all_results.append(result)
                    print(f"\n{result['label']}={result['value']}:")
                    print(f"  N={result['sample_size']}, Avg R={result['avg_r']:.3f}, Delta={result['delta']:+.3f}R, WR={result['win_rate']:.1%}")

    # ============================================
    # NY ORB (2300) with ASIA + LONDON labels
    # ============================================
    print("\n\n" + "="*80)
    print("NY ORB (2300) <- ASIA + LONDON SESSION LABELS")
    print("="*80)

    ny_2300_trades = get_orb_trades('2300', table_name)
    print(f"\nNY 2300 ORB trades: {len(ny_2300_trades)}")

    if len(ny_2300_trades) == 0:
        print("No NY 2300 ORB trades found. Skipping.")
    else:
        # Attach Asia + London labels
        all_label_cols = ['asia_sweep_high', 'asia_sweep_low', 'asia_range_type',
                         'asia_net_direction', 'asia_failure',
                         'london_sweep_prior_high', 'london_sweep_prior_low', 'london_orb_outcome']

        ny_2300_with_labels = attach_prior_session_labels(
            ny_2300_trades, all_label_cols, same_day=True
        )

        baseline_ny_2300 = compute_baseline_expectancy(ny_2300_trades)
        print(f"\nBaseline (NY 2300 ORB):")
        print(f"  Sample: {baseline_ny_2300['sample_size']}")
        print(f"  Avg R: {baseline_ny_2300['avg_r']:.3f}R")
        print(f"  Win Rate: {baseline_ny_2300['win_rate']:.1%}")

        # Test Asia sweep conditions
        print("\n--- ASIA SWEEP CONDITIONS ---")

        sweep_results = analyze_sweep_continuation_vs_reversal(
            ny_2300_with_labels, 'asia_sweep_high', 'UP', 'DOWN',
            baseline_ny_2300, min_sample_size, min_delta
        )
        all_results.extend(sweep_results)
        for r in sweep_results:
            print(f"\n{r['label']} ({r['hypothesis']}):")
            print(f"  N={r['sample_size']}, Avg R={r['avg_r']:.3f}, Delta={r['delta']:+.3f}R, WR={r['win_rate']:.1%}")

        sweep_results = analyze_sweep_continuation_vs_reversal(
            ny_2300_with_labels, 'asia_sweep_low', 'DOWN', 'UP',
            baseline_ny_2300, min_sample_size, min_delta
        )
        all_results.extend(sweep_results)
        for r in sweep_results:
            print(f"\n{r['label']} ({r['hypothesis']}):")
            print(f"  N={r['sample_size']}, Avg R={r['avg_r']:.3f}, Delta={r['delta']:+.3f}R, WR={r['win_rate']:.1%}")

        # Test London sweep conditions
        print("\n--- LONDON SWEEP CONDITIONS ---")

        sweep_results = analyze_sweep_continuation_vs_reversal(
            ny_2300_with_labels, 'london_sweep_prior_high', 'UP', 'DOWN',
            baseline_ny_2300, min_sample_size, min_delta
        )
        all_results.extend(sweep_results)
        for r in sweep_results:
            print(f"\n{r['label']} ({r['hypothesis']}):")
            print(f"  N={r['sample_size']}, Avg R={r['avg_r']:.3f}, Delta={r['delta']:+.3f}R, WR={r['win_rate']:.1%}")

        sweep_results = analyze_sweep_continuation_vs_reversal(
            ny_2300_with_labels, 'london_sweep_prior_low', 'DOWN', 'UP',
            baseline_ny_2300, min_sample_size, min_delta
        )
        all_results.extend(sweep_results)
        for r in sweep_results:
            print(f"\n{r['label']} ({r['hypothesis']}):")
            print(f"  N={r['sample_size']}, Avg R={r['avg_r']:.3f}, Delta={r['delta']:+.3f}R, WR={r['win_rate']:.1%}")

        # Test London ORB outcome
        print("\n--- LONDON ORB OUTCOME ---")

        for val in ['hold', 'fail', 'reject']:
            result = analyze_single_condition(
                ny_2300_with_labels, 'london_orb_outcome', val, baseline_ny_2300,
                min_sample_size, min_delta
            )
            if result:
                all_results.append(result)
                print(f"\n{result['label']}={result['value']}:")
                print(f"  N={result['sample_size']}, Avg R={result['avg_r']:.3f}, Delta={result['delta']:+.3f}R, WR={result['win_rate']:.1%}")

    # ============================================
    # NY ORB (0030) with ASIA + LONDON labels
    # ============================================
    print("\n\n" + "="*80)
    print("NY ORB (0030) <- ASIA + LONDON SESSION LABELS")
    print("="*80)

    ny_0030_trades = get_orb_trades('0030', table_name)
    print(f"\nNY 0030 ORB trades: {len(ny_0030_trades)}")

    if len(ny_0030_trades) == 0:
        print("No NY 0030 ORB trades found. Skipping.")
    else:
        # Attach Asia + London labels
        ny_0030_with_labels = attach_prior_session_labels(
            ny_0030_trades, all_label_cols, same_day=True
        )

        baseline_ny_0030 = compute_baseline_expectancy(ny_0030_trades)
        print(f"\nBaseline (NY 0030 ORB):")
        print(f"  Sample: {baseline_ny_0030['sample_size']}")
        print(f"  Avg R: {baseline_ny_0030['avg_r']:.3f}R")
        print(f"  Win Rate: {baseline_ny_0030['win_rate']:.1%}")

        # Test Asia sweep conditions
        print("\n--- ASIA SWEEP CONDITIONS ---")

        sweep_results = analyze_sweep_continuation_vs_reversal(
            ny_0030_with_labels, 'asia_sweep_high', 'UP', 'DOWN',
            baseline_ny_0030, min_sample_size, min_delta
        )
        all_results.extend(sweep_results)
        for r in sweep_results:
            print(f"\n{r['label']} ({r['hypothesis']}):")
            print(f"  N={r['sample_size']}, Avg R={r['avg_r']:.3f}, Delta={r['delta']:+.3f}R, WR={r['win_rate']:.1%}")

        sweep_results = analyze_sweep_continuation_vs_reversal(
            ny_0030_with_labels, 'asia_sweep_low', 'DOWN', 'UP',
            baseline_ny_0030, min_sample_size, min_delta
        )
        all_results.extend(sweep_results)
        for r in sweep_results:
            print(f"\n{r['label']} ({r['hypothesis']}):")
            print(f"  N={r['sample_size']}, Avg R={r['avg_r']:.3f}, Delta={r['delta']:+.3f}R, WR={r['win_rate']:.1%}")

        # Test London sweep conditions
        print("\n--- LONDON SWEEP CONDITIONS ---")

        sweep_results = analyze_sweep_continuation_vs_reversal(
            ny_0030_with_labels, 'london_sweep_prior_high', 'UP', 'DOWN',
            baseline_ny_0030, min_sample_size, min_delta
        )
        all_results.extend(sweep_results)
        for r in sweep_results:
            print(f"\n{r['label']} ({r['hypothesis']}):")
            print(f"  N={r['sample_size']}, Avg R={r['avg_r']:.3f}, Delta={r['delta']:+.3f}R, WR={r['win_rate']:.1%}")

        sweep_results = analyze_sweep_continuation_vs_reversal(
            ny_0030_with_labels, 'london_sweep_prior_low', 'DOWN', 'UP',
            baseline_ny_0030, min_sample_size, min_delta
        )
        all_results.extend(sweep_results)
        for r in sweep_results:
            print(f"\n{r['label']} ({r['hypothesis']}):")
            print(f"  N={r['sample_size']}, Avg R={r['avg_r']:.3f}, Delta={r['delta']:+.3f}R, WR={r['win_rate']:.1%}")

        # Test London ORB outcome
        print("\n--- LONDON ORB OUTCOME ---")

        for val in ['hold', 'fail', 'reject']:
            result = analyze_single_condition(
                ny_0030_with_labels, 'london_orb_outcome', val, baseline_ny_0030,
                min_sample_size, min_delta
            )
            if result:
                all_results.append(result)
                print(f"\n{result['label']}={result['value']}:")
                print(f"  N={result['sample_size']}, Avg R={result['avg_r']:.3f}, Delta={result['delta']:+.3f}R, WR={result['win_rate']:.1%}")

    # ============================================
    # NY ORB (0030) with NY PRE-ORB LABELS
    # ============================================
    print("\n\n" + "="*80)
    print("NY ORB (0030) <- NY PRE-ORB SESSION LABELS (2300-0030)")
    print("="*80)

    ny_0030_trades2 = get_orb_trades('0030', table_name)
    print(f"\nNY 0030 ORB trades: {len(ny_0030_trades2)}")

    if len(ny_0030_trades2) == 0:
        print("No NY 0030 ORB trades found. Skipping.")
    else:
        # Attach NY pre-ORB inventory state labels
        ny_label_cols = ['ny_range_type', 'ny_net_direction', 'ny_exhaustion']

        ny_0030_with_ny_labels = attach_prior_session_labels(
            ny_0030_trades2, ny_label_cols, same_day=True
        )

        baseline_ny_0030_2 = compute_baseline_expectancy(ny_0030_trades2)
        print(f"\nBaseline (NY 0030 ORB):")
        print(f"  Sample: {baseline_ny_0030_2['sample_size']}")
        print(f"  Avg R: {baseline_ny_0030_2['avg_r']:.3f}R")
        print(f"  Win Rate: {baseline_ny_0030_2['win_rate']:.1%}")

        # Test NY inventory state conditions
        print("\n--- NY INVENTORY STATE CONDITIONS ---")

        # Test NY exhaustion (continuation vs reversal)
        print("\n--- NY EXHAUSTION CONDITIONS (Continuation vs Reversal) ---")

        # For exhaustion, test both up and down continuations when exhaustion=True
        for direction in ['UP', 'DOWN']:
            result = analyze_single_condition(
                ny_0030_with_ny_labels[ny_0030_with_ny_labels['direction'] == direction],
                'ny_exhaustion', True, baseline_ny_0030_2,
                min_sample_size, min_delta
            )
            if result:
                result['label'] = f"ny_exhaustion=True + {direction}"
                result['hypothesis'] = f"EXHAUSTION + {direction}"
                all_results.append(result)
                print(f"\n{result['label']}:")
                print(f"  N={result['sample_size']}, Avg R={result['avg_r']:.3f}, Delta={result['delta']:+.3f}R, WR={result['win_rate']:.1%}")

        # Test categorical conditions
        print("\n--- NY CATEGORICAL CONDITIONS ---")

        for cat_label in ['ny_range_type', 'ny_net_direction']:
            unique_values = ny_0030_with_ny_labels[cat_label].dropna().unique()
            for val in unique_values:
                result = analyze_single_condition(
                    ny_0030_with_ny_labels, cat_label, val, baseline_ny_0030_2,
                    min_sample_size, min_delta
                )
                if result:
                    all_results.append(result)
                    print(f"\n{result['label']}={result['value']}:")
                    print(f"  N={result['sample_size']}, Avg R={result['avg_r']:.3f}, Delta={result['delta']:+.3f}R, WR={result['win_rate']:.1%}")

    # ============================================
    # SUMMARY
    # ============================================
    print("\n\n" + "="*80)
    print("SUMMARY: SIGNIFICANT CONDITIONS")
    print(f"(n >= {min_sample_size}, delta >= +{min_delta}R)")
    print("="*80 + "\n")

    if len(all_results) == 0:
        print("No significant conditions found.")
    else:
        # Sort by absolute delta
        all_results_sorted = sorted(all_results, key=lambda x: abs(x['delta']), reverse=True)

        for r in all_results_sorted:
            label_str = f"{r.get('label', 'N/A')}"
            if 'value' in r:
                label_str += f"={r['value']}"
            if 'hypothesis' in r:
                label_str += f" ({r['hypothesis']})"

            print(f"{label_str}:")
            print(f"  N={r['sample_size']}, Avg R={r['avg_r']:.3f}, Delta={r['delta']:+.3f}R, WR={r['win_rate']:.1%}")
            print()

    print(f"Total significant conditions: {len(all_results)}")


if __name__ == "__main__":
    # Run analysis on default 5m execution table
    run_full_analysis(
        table_name="orb_trades_5m_exec",
        min_sample_size=200,
        min_delta=0.10
    )

    conn.close()
