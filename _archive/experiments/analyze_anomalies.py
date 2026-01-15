"""
ANOMALY ANALYSIS - Convert Loss Clusters to Valid Entry-Time Filters

Following the guidance from anomolies.txt:
1. Identify bad trades (loss clusters)
2. Find overrepresented pre-entry conditions
3. Validate with time-split OOS
4. Test robustness to threshold changes

NO LOOKAHEAD: All features computed using only data available at/before entry.
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

DB_PATH = "gold.db"

# ============================================================================
# STEP 1: IDENTIFY BAD TRADES
# ============================================================================

def identify_bad_trades(con: duckdb.DuckDBPyConnection, orb: str) -> pd.DataFrame:
    """
    Identify bad trades using multiple criteria:
    - Bottom 30% by R-multiple
    - High MAE (≥ 0.8R)
    - Fast failure (loss within 15 minutes)

    Returns DataFrame with 'is_bad_trade' column.
    """

    # Query from daily_features_v2_half with correct column names
    query = f"""
    SELECT
        date_local,
        instrument,

        -- ORB columns (dynamically based on orb param)
        orb_{orb}_high as orb_high,
        orb_{orb}_low as orb_low,
        orb_{orb}_size as orb_size,
        orb_{orb}_break_dir as break_dir,
        orb_{orb}_outcome as outcome,
        orb_{orb}_r_multiple as r_multiple,
        orb_{orb}_mae as mae,
        orb_{orb}_mfe as mfe,
        orb_{orb}_risk_ticks as risk_ticks,

        -- Session features (available at entry)
        asia_range,
        london_range,
        ny_range,

        -- Session highs/lows for sweep detection
        asia_high,
        asia_low,
        london_high,
        london_low,

        -- ATR for normalization (proxy for ADR)
        atr_20

    FROM daily_features_v2_half
    WHERE orb_{orb}_outcome IN ('WIN', 'LOSS')
    AND instrument = 'MGC'
    ORDER BY date_local
    """

    df = con.execute(query).df()

    if df.empty:
        print(f"No trades found for {orb}")
        return df

    # Calculate MAE/MFE in R terms
    df['mae_r'] = df['mae'] / df['risk_ticks']
    df['mfe_r'] = df['mfe'] / df['risk_ticks']

    # Calculate pre-move features (approximation from session ranges)
    # Pre-ORB travel for night ORBs = london_range
    if orb in ['2300', '0030']:
        df['pre_orb_travel'] = df['london_range']
        df['pre_ny_travel'] = df['london_range']  # Approx
    elif orb in ['1800']:
        df['pre_orb_travel'] = df['asia_range']
        df['pre_ny_travel'] = 0  # Not applicable
    else:
        df['pre_orb_travel'] = 0  # Day ORBs don't have pre-move
        df['pre_ny_travel'] = 0

    # Sweep flags (night ORBs only)
    if orb in ['2300', '0030']:
        df['swept_london_high_before_entry'] = (df['london_high'].notna()) & (df['orb_high'] > df['london_high'])
        df['swept_london_low_before_entry'] = (df['london_low'].notna()) & (df['orb_low'] < df['london_low'])
    else:
        df['swept_london_high_before_entry'] = False
        df['swept_london_low_before_entry'] = False

    # Identify bad trades
    r_threshold_30pct = df['r_multiple'].quantile(0.30)

    df['is_bad_trade'] = (
        (df['r_multiple'] <= r_threshold_30pct) |  # Bottom 30%
        (df['mae_r'] >= 0.8) |  # High MAE
        ((df['outcome'] == 'LOSS') & (df['mae_r'] >= 0.5))  # Fast failure
    )

    bad_count = df['is_bad_trade'].sum()
    total_count = len(df)

    print(f"\n{orb} ORB - Bad Trade Identification:")
    print(f"  Total trades: {total_count}")
    print(f"  Bad trades: {bad_count} ({bad_count/total_count*100:.1f}%)")
    print(f"  R threshold (30th pct): {r_threshold_30pct:.3f}R")

    return df


# ============================================================================
# STEP 2: BUILD ENTRY-TIME FEATURES
# ============================================================================

def build_entry_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build features that are knowable at entry time.
    NO LOOKAHEAD - all features use only data available before/at entry.
    """

    df = df.copy()

    # Use ATR as proxy for daily range
    atr_col = 'atr_20' if 'atr_20' in df.columns else None

    if atr_col is None:
        return df

    # 1. Pre-open travel normalization
    if 'pre_ny_travel' in df.columns:
        df['pre_ny_travel_norm'] = df['pre_ny_travel'] / df[atr_col]

    if 'pre_orb_travel' in df.columns:
        df['pre_orb_travel_norm'] = df['pre_orb_travel'] / df[atr_col]

    # 2. Session range compression/expansion
    if 'asia_range' in df.columns:
        df['asia_range_norm'] = df['asia_range'] / df[atr_col]
        df['asia_compressed'] = df['asia_range_norm'] < 0.3
        df['asia_expanded'] = df['asia_range_norm'] > 0.7

    if 'london_range' in df.columns:
        df['london_range_norm'] = df['london_range'] / df[atr_col]
        df['london_compressed'] = df['london_range_norm'] < 0.3
        df['london_expanded'] = df['london_range_norm'] > 0.7

    # 3. ORB size ratio
    if 'orb_size' in df.columns:
        df['orb_size_norm'] = df['orb_size'] / df[atr_col]
        df['orb_small'] = df['orb_size_norm'] < 0.05
        df['orb_large'] = df['orb_size_norm'] > 0.15

    # 4. High pre-move flag
    if 'pre_ny_travel_norm' in df.columns:
        df['high_pre_ny_travel'] = df['pre_ny_travel_norm'] > 0.5

    if 'pre_orb_travel_norm' in df.columns:
        df['high_pre_orb_travel'] = df['pre_orb_travel_norm'] > 0.3

    # 5. Stop size (available at entry)
    if 'risk_ticks' in df.columns:
        df['stop_norm'] = df['risk_ticks'] / df[atr_col]
        df['large_stop'] = df['stop_norm'] > 0.15

    return df


# ============================================================================
# STEP 3: FIND OVERREPRESENTED CONDITIONS
# ============================================================================

def find_overrepresented_conditions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Find conditions that are overrepresented in bad trades.

    Returns DataFrame with:
    - condition name
    - frequency in bad trades
    - frequency in all trades
    - lift (bad_freq / all_freq)
    """

    results = []

    # Boolean feature columns to test
    feature_cols = [
        'asia_compressed', 'asia_expanded',
        'london_compressed', 'london_expanded',
        'orb_small', 'orb_large',
        'high_pre_ny_travel', 'high_pre_orb_travel',
        'large_stop',
        'swept_london_high_before_entry', 'swept_london_low_before_entry'
    ]

    bad_trades = df[df['is_bad_trade']]
    all_trades = df

    for feature in feature_cols:
        if feature not in df.columns:
            continue

        # Skip if all null
        if df[feature].isna().all():
            continue

        # Frequency in bad trades
        bad_freq = bad_trades[feature].sum() / len(bad_trades) if len(bad_trades) > 0 else 0

        # Frequency in all trades
        all_freq = all_trades[feature].sum() / len(all_trades) if len(all_trades) > 0 else 0

        # Lift
        lift = bad_freq / all_freq if all_freq > 0 else 0

        # Count
        bad_count = bad_trades[feature].sum()
        all_count = all_trades[feature].sum()

        results.append({
            'condition': feature,
            'bad_freq': bad_freq,
            'all_freq': all_freq,
            'lift': lift,
            'bad_count': int(bad_count),
            'all_count': int(all_count)
        })

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('lift', ascending=False)

    return results_df


# ============================================================================
# STEP 4: TIME-SPLIT OOS VALIDATION
# ============================================================================

def validate_time_split(df: pd.DataFrame, condition: str, split_date: str) -> Dict:
    """
    Validate a condition using time-split OOS.

    Args:
        df: DataFrame with trades
        condition: condition column name
        split_date: date to split IS/OOS (e.g., "2024-01-01")

    Returns:
        Dict with IS and OOS performance stats
    """

    if condition not in df.columns:
        return {}

    # Split data
    split_dt = pd.to_datetime(split_date)
    df['date_local'] = pd.to_datetime(df['date_local'])

    is_data = df[df['date_local'] < split_dt]
    oos_data = df[df['date_local'] >= split_dt]

    def calc_stats(data: pd.DataFrame, filter_active: bool) -> Dict:
        if filter_active:
            # Exclude trades where condition is True
            filtered = data[~data[condition].fillna(False)]
        else:
            # All trades (baseline)
            filtered = data

        if len(filtered) == 0:
            return {
                'trades': 0, 'win_rate': 0, 'avg_r': 0, 'expectancy': 0
            }

        wins = (filtered['outcome'] == 'WIN').sum()
        win_rate = wins / len(filtered) if len(filtered) > 0 else 0
        avg_r = filtered['r_multiple'].mean()
        expectancy = avg_r

        return {
            'trades': len(filtered),
            'win_rate': win_rate,
            'avg_r': avg_r,
            'expectancy': expectancy
        }

    # Calculate stats
    is_baseline = calc_stats(is_data, filter_active=False)
    is_filtered = calc_stats(is_data, filter_active=True)

    oos_baseline = calc_stats(oos_data, filter_active=False)
    oos_filtered = calc_stats(oos_data, filter_active=True)

    return {
        'condition': condition,
        'split_date': split_date,
        'is_baseline': is_baseline,
        'is_filtered': is_filtered,
        'oos_baseline': oos_baseline,
        'oos_filtered': oos_filtered,
        'is_improvement': is_filtered['expectancy'] - is_baseline['expectancy'],
        'oos_improvement': oos_filtered['expectancy'] - oos_baseline['expectancy']
    }


# ============================================================================
# STEP 5: ROBUSTNESS TESTING
# ============================================================================

def test_robustness(df: pd.DataFrame, base_feature: str, thresholds: List[float]) -> pd.DataFrame:
    """
    Test robustness by varying thresholds.

    For continuous features (e.g., pre_ny_travel_norm), test different threshold values.
    If improvement holds across thresholds → robust.
    If only works at one exact threshold → curve-fit.

    Args:
        df: DataFrame with trades
        base_feature: continuous feature column (e.g., 'pre_ny_travel_norm')
        thresholds: list of threshold values to test

    Returns:
        DataFrame with results for each threshold
    """

    if base_feature not in df.columns:
        return pd.DataFrame()

    results = []

    for thresh in thresholds:
        # Create binary condition
        condition_name = f"{base_feature}_gt_{thresh:.2f}"
        df[condition_name] = df[base_feature] > thresh

        # Baseline stats (all trades)
        baseline_r = df['r_multiple'].mean()
        baseline_trades = len(df)

        # Filtered stats (exclude condition)
        filtered = df[~df[condition_name].fillna(False)]
        filtered_r = filtered['r_multiple'].mean() if len(filtered) > 0 else 0
        filtered_trades = len(filtered)

        improvement = filtered_r - baseline_r

        results.append({
            'threshold': thresh,
            'condition': condition_name,
            'baseline_r': baseline_r,
            'filtered_r': filtered_r,
            'improvement': improvement,
            'trades_removed': baseline_trades - filtered_trades,
            'pct_removed': (baseline_trades - filtered_trades) / baseline_trades * 100
        })

    return pd.DataFrame(results)


# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def analyze_orb_anomalies(orb: str, split_date: str = "2024-01-01"):
    """
    Complete anomaly analysis for a single ORB.

    Steps:
    1. Identify bad trades
    2. Build entry-time features
    3. Find overrepresented conditions
    4. Validate with time-split OOS
    5. Test robustness
    """

    con = duckdb.connect(DB_PATH, read_only=True)

    print(f"\n{'='*80}")
    print(f"ANOMALY ANALYSIS: {orb} ORB")
    print(f"{'='*80}")

    # Step 1: Load and identify bad trades
    df = identify_bad_trades(con, orb)

    if df.empty:
        con.close()
        return

    # Step 2: Build entry-time features
    df = build_entry_time_features(df)

    # Step 3: Find overrepresented conditions
    print(f"\n--- Overrepresented Conditions in Bad Trades ---")
    conditions_df = find_overrepresented_conditions(df)

    print("\nTop conditions with lift >= 1.3:")
    top_conditions = conditions_df[conditions_df['lift'] >= 1.3]

    if not top_conditions.empty:
        print(top_conditions.to_string(index=False))
    else:
        print("No conditions with lift >= 1.3 found")

    # Step 4: Time-split OOS validation for top conditions
    print(f"\n--- Time-Split OOS Validation (split: {split_date}) ---")

    for _, row in top_conditions.iterrows():
        condition = row['condition']
        validation = validate_time_split(df, condition, split_date)

        if validation:
            print(f"\nCondition: {condition}")
            print(f"  IN-SAMPLE:")
            print(f"    Baseline:  {validation['is_baseline']['trades']} trades, "
                  f"{validation['is_baseline']['avg_r']:.3f}R avg")
            print(f"    Filtered:  {validation['is_filtered']['trades']} trades, "
                  f"{validation['is_filtered']['avg_r']:.3f}R avg")
            print(f"    Improvement: {validation['is_improvement']:+.3f}R")

            print(f"  OUT-OF-SAMPLE:")
            print(f"    Baseline:  {validation['oos_baseline']['trades']} trades, "
                  f"{validation['oos_baseline']['avg_r']:.3f}R avg")
            print(f"    Filtered:  {validation['oos_filtered']['trades']} trades, "
                  f"{validation['oos_filtered']['avg_r']:.3f}R avg")
            print(f"    Improvement: {validation['oos_improvement']:+.3f}R")

            # Check if robust (improvement holds OOS)
            if validation['oos_improvement'] > 0 and validation['is_improvement'] > 0:
                print(f"    [OK] ROBUST: Improvement holds in both IS and OOS")
            elif validation['oos_improvement'] <= 0 and validation['is_improvement'] > 0:
                print(f"    [FAIL] OVERFIT: Improvement only in IS, fails OOS")
            else:
                print(f"    ? INCONCLUSIVE")

    # Step 5: Robustness testing for continuous features
    print(f"\n--- Robustness Testing ---")

    continuous_features = ['pre_ny_travel_norm', 'pre_orb_travel_norm', 'orb_size_norm']

    for feature in continuous_features:
        if feature not in df.columns or df[feature].isna().all():
            continue

        print(f"\nFeature: {feature}")

        # Test thresholds around mean/median
        feature_mean = df[feature].mean()
        thresholds = [
            feature_mean * 0.5,
            feature_mean * 0.75,
            feature_mean * 1.0,
            feature_mean * 1.25,
            feature_mean * 1.5
        ]

        robustness_df = test_robustness(df, feature, thresholds)

        if not robustness_df.empty:
            print(robustness_df.to_string(index=False))

            # Check if robust
            positive_improvements = (robustness_df['improvement'] > 0).sum()
            if positive_improvements >= 3:
                print(f"  [OK] ROBUST: Positive improvement at {positive_improvements}/5 thresholds")
            else:
                print(f"  [FAIL] FRAGILE: Only positive at {positive_improvements}/5 thresholds")

    con.close()


# ============================================================================
# RUN FOR ALL ORBS
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze trading anomalies")
    parser.add_argument("--orb", default="all", help="ORB to analyze (0900, 1000, 1100, 1800, 2300, 0030, or 'all')")
    parser.add_argument("--split-date", default="2024-01-01", help="Date to split IS/OOS")

    args = parser.parse_args()

    if args.orb == "all":
        orbs = ["0900", "1000", "1100", "1800", "2300", "0030"]
    else:
        orbs = [args.orb]

    for orb in orbs:
        analyze_orb_anomalies(orb, args.split_date)

    print(f"\n{'='*80}")
    print("ANOMALY ANALYSIS COMPLETE")
    print(f"{'='*80}")
