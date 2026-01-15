"""
Analyze All Variant Results

Compares all backtested variants to find the best configurations.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def analyze_variants():
    con = duckdb.connect(DB_PATH)

    print("="*80)
    print("VARIANT ANALYSIS - BEST CONFIGURATIONS")
    print("="*80)
    print()

    # 1. Analyze 1m midstop variants
    print("1. 1m Midstop Variants (orb_trades_1m_exec)")
    print("-"*80)

    df_1m = con.execute("""
        SELECT
            rr,
            close_confirmations as confirm,
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            AVG(CASE WHEN outcome='WIN' THEN 1 ELSE 0 END) as win_rate,
            AVG(r_multiple) as avg_r,
            SUM(r_multiple) as total_r,
            AVG(mae_r) as avg_mae,
            AVG(mfe_r) as avg_mfe
        FROM orb_trades_1m_exec
        GROUP BY rr, close_confirmations
        ORDER BY total_r DESC
    """).fetchdf()

    print(df_1m.to_string(index=False))
    print()

    # Best 1m config
    best_1m = df_1m.iloc[0]
    print(f">> BEST 1m: RR={best_1m['rr']}, Confirm={best_1m['confirm']}, Win Rate={best_1m['win_rate']:.1%}, Total R={best_1m['total_r']:+.0f}")
    print()

    # 2. Analyze 5m exec variants
    print("2. 5m Exec Variants (orb_trades_5m_exec - no sl_mode/buffer)")
    print("-"*80)

    df_5m = con.execute("""
        SELECT
            rr,
            close_confirmations as confirm,
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            AVG(CASE WHEN outcome='WIN' THEN 1 ELSE 0 END) as win_rate,
            AVG(r_multiple) as avg_r,
            SUM(r_multiple) as total_r
        FROM orb_trades_5m_exec
        WHERE sl_mode IS NULL OR sl_mode = ''
        GROUP BY rr, close_confirmations
        ORDER BY total_r DESC
    """).fetchdf()

    if len(df_5m) > 0:
        print(df_5m.to_string(index=False))
        print()

        best_5m = df_5m.iloc[0]
        print(f">> BEST 5m: RR={best_5m['rr']}, Confirm={best_5m['confirm']}, Win Rate={best_5m['win_rate']:.1%}, Total R={best_5m['total_r']:+.0f}")
    else:
        print("No 5m exec results found")
    print()

    # 3. Analyze 5m half-SL variants (most comprehensive)
    print("3. 5m Half-SL Variants (with sl_mode and buffer)")
    print("-"*80)

    df_5m_half = con.execute("""
        SELECT
            sl_mode,
            buffer_ticks,
            rr,
            close_confirmations as confirm,
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            AVG(CASE WHEN outcome='WIN' THEN 1 ELSE 0 END) as win_rate,
            AVG(r_multiple) as avg_r,
            SUM(r_multiple) as total_r
        FROM orb_trades_5m_exec
        WHERE sl_mode IS NOT NULL AND sl_mode != ''
        GROUP BY sl_mode, buffer_ticks, rr, close_confirmations
        ORDER BY total_r DESC
        LIMIT 20
    """).fetchdf()

    if len(df_5m_half) > 0:
        print(df_5m_half.to_string(index=False))
        print()

        best_5m_half = df_5m_half.iloc[0]
        print(f">> BEST 5m Half-SL: SL={best_5m_half['sl_mode']}, Buffer={best_5m_half['buffer_ticks']}, RR={best_5m_half['rr']}, Confirm={best_5m_half['confirm']}, Win Rate={best_5m_half['win_rate']:.1%}, Total R={best_5m_half['total_r']:+.0f}")
    else:
        print("No 5m half-SL results found")
    print()

    # 4. Overall winner
    print("="*80)
    print("OVERALL BEST CONFIGURATION")
    print("="*80)

    all_configs = []

    if len(df_1m) > 0:
        all_configs.append(('1m midstop', best_1m['total_r'], f"RR={best_1m['rr']}, Confirm={best_1m['confirm']}"))

    if len(df_5m) > 0:
        all_configs.append(('5m exec', best_5m['total_r'], f"RR={best_5m['rr']}, Confirm={best_5m['confirm']}"))

    if len(df_5m_half) > 0:
        all_configs.append(('5m half-SL', best_5m_half['total_r'], f"SL={best_5m_half['sl_mode']}, Buffer={best_5m_half['buffer_ticks']}, RR={best_5m_half['rr']}, Confirm={best_5m_half['confirm']}"))

    all_configs.sort(key=lambda x: x[1], reverse=True)

    if all_configs:
        winner = all_configs[0]
        print(f">>>>>> WINNER: {winner[0]} with Total R = {winner[1]:+.0f}")
        print(f"    Config: {winner[2]}")

    con.close()

if __name__ == "__main__":
    analyze_variants()
