"""
ORB Variants Overnight Runner

Systematically tests all backtest variants:
1. 1m midstop (RR × confirm grid)
2. 5m exec (RR × confirm grid)
3. 5m half-SL (RR × confirm × buffer grid)

Saves progress, handles failures, generates comprehensive report.
"""

import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
import argparse

# ============================================================================
# CONFIGURATION
# ============================================================================

# 1m midstop variants
RR_GRID_1M = [1.5, 2.0, 2.5, 3.0]
CONFIRM_GRID_1M = [1, 2, 3]

# 5m exec variants
RR_GRID_5M = [1.5, 2.0, 2.5, 3.0]
CONFIRM_GRID_5M = [1, 2, 3]

# 5m half-SL variants
RR_GRID_5M_HALF = [1.5, 2.0, 2.5, 3.0]
CONFIRM_GRID_5M_HALF = [1, 2]
SL_MODES = ["full", "half"]
BUFFER_GRID = [0, 5, 10, 15, 20]  # Buffer ticks

# Progress tracking
PROGRESS_FILE = "overnight_progress.json"
LOG_FILE = "overnight_runner.log"

# ============================================================================
# VARIANT BUILDER
# ============================================================================

def build_variants() -> List[Dict]:
    """Build all variant configurations"""
    variants = []

    # 1. 1m midstop variants
    print("Building 1m midstop variants...")
    for rr in RR_GRID_1M:
        for confirm in CONFIRM_GRID_1M:
            variants.append({
                'id': f"1m_rr{rr}_c{confirm}",
                'type': '1m_midstop',
                'script': 'backtest_orb_exec_1m.py',
                'rr': rr,
                'confirm': confirm,
                'command': f"python backtest_orb_exec_1m.py --rr {rr} --confirm {confirm}"
            })

    # 2. 5m exec variants
    print("Building 5m exec variants...")
    for rr in RR_GRID_5M:
        for confirm in CONFIRM_GRID_5M:
            variants.append({
                'id': f"5m_rr{rr}_c{confirm}",
                'type': '5m_exec',
                'script': 'backtest_orb_exec_5m.py',
                'rr': rr,
                'confirm': confirm,
                'command': f"python backtest_orb_exec_5m.py --rr {rr} --confirm {confirm}"
            })

    # 3. 5m half-SL variants (most comprehensive)
    print("Building 5m half-SL variants...")
    for sl_mode in SL_MODES:
        for rr in RR_GRID_5M_HALF:
            for confirm in CONFIRM_GRID_5M_HALF:
                for buffer in BUFFER_GRID:
                    variants.append({
                        'id': f"5m_{sl_mode}_rr{rr}_c{confirm}_b{buffer}",
                        'type': '5m_half_sl',
                        'script': 'backtest_orb_exec_5mhalfsl.py',
                        'rr': rr,
                        'confirm': confirm,
                        'sl_mode': sl_mode,
                        'buffer': buffer,
                        'command': f"python backtest_orb_exec_5mhalfsl.py --rr {rr} --confirm {confirm} --sl {sl_mode} --buffer-ticks {buffer}"
                    })

    return variants

# ============================================================================
# PROGRESS MANAGEMENT
# ============================================================================

def load_progress() -> Dict:
    """Load progress from file"""
    if Path(PROGRESS_FILE).exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'started_at': None,
        'completed': [],
        'failed': [],
        'current': None,
        'total_variants': 0
    }

def save_progress(progress: Dict):
    """Save progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def log(message: str):
    """Log message to file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')

# ============================================================================
# BACKTEST RUNNER
# ============================================================================

def run_variant(variant: Dict) -> Tuple[bool, str]:
    """Run a single variant, return (success, error_message)"""
    log(f"Starting: {variant['id']}")
    log(f"Command: {variant['command']}")

    start_time = time.time()

    try:
        result = subprocess.run(
            variant['command'],
            shell=True,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per variant
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            log(f">> SUCCESS: {variant['id']} ({elapsed:.0f}s)")
            return True, ""
        else:
            error = result.stderr[:200] if result.stderr else "Unknown error"
            log(f"✗ FAILED: {variant['id']} - {error}")
            return False, error

    except subprocess.TimeoutExpired:
        log(f"✗ TIMEOUT: {variant['id']} (>1 hour)")
        return False, "Timeout after 1 hour"
    except Exception as e:
        log(f"✗ ERROR: {variant['id']} - {str(e)}")
        return False, str(e)

# ============================================================================
# MAIN RUNNER
# ============================================================================

def run_overnight(resume: bool = False, retry_failed: bool = False):
    """Main overnight runner"""

    log("="*80)
    log("ORB VARIANTS OVERNIGHT RUNNER - STARTED")
    log("="*80)

    # Build all variants
    variants = build_variants()
    total = len(variants)

    log(f"Total variants to test: {total}")
    log(f"  - 1m midstop: {len([v for v in variants if v['type'] == '1m_midstop'])}")
    log(f"  - 5m exec: {len([v for v in variants if v['type'] == '5m_exec'])}")
    log(f"  - 5m half-SL: {len([v for v in variants if v['type'] == '5m_half_sl'])}")

    # Load progress
    progress = load_progress()

    if not resume and not retry_failed:
        # Fresh start
        progress = {
            'started_at': datetime.now().isoformat(),
            'completed': [],
            'failed': [],
            'current': None,
            'total_variants': total
        }
        log("Starting fresh run")
    elif resume:
        log(f"Resuming from previous run ({len(progress['completed'])} completed)")
    elif retry_failed:
        log(f"Retrying {len(progress['failed'])} failed variants")
        variants = [v for v in variants if v['id'] in [f['id'] for f in progress['failed']]]
        progress['failed'] = []

    # Filter out completed variants (unless retrying failed)
    if not retry_failed:
        completed_ids = set(progress['completed'])
        variants = [v for v in variants if v['id'] not in completed_ids]

    if len(variants) == 0:
        log("No variants to run!")
        return

    log(f"Running {len(variants)} variants...")
    log("")

    # Run each variant
    for i, variant in enumerate(variants, 1):
        progress['current'] = variant['id']
        save_progress(progress)

        log(f"[{i}/{len(variants)}] Running: {variant['id']}")

        success, error = run_variant(variant)

        if success:
            progress['completed'].append(variant['id'])
        else:
            progress['failed'].append({
                'id': variant['id'],
                'error': error,
                'timestamp': datetime.now().isoformat()
            })

        progress['current'] = None
        save_progress(progress)

        # Brief pause between variants
        time.sleep(2)

    # Final report
    log("")
    log("="*80)
    log("OVERNIGHT RUNNER - COMPLETED")
    log("="*80)
    log(f"Total variants: {total}")
    log(f"Completed: {len(progress['completed'])}")
    log(f"Failed: {len(progress['failed'])}")

    if progress['failed']:
        log("")
        log("Failed variants:")
        for failed in progress['failed']:
            log(f"  - {failed['id']}: {failed['error']}")
        log("")
        log("To retry failed variants:")
        log("  python orb_variants_overnight.py --retry-failed")
    else:
        log("")
        log(">> ALL VARIANTS COMPLETED SUCCESSFULLY!")

    log("")
    log("Next steps:")
    log("  1. Analyze results: python analyze_all_variants.py")
    log("  2. View dashboard: streamlit run app_trading_hub.py")
    log("  3. Compare variants: python compare_variants.py")

# ============================================================================
# RESULTS ANALYZER
# ============================================================================

def create_analysis_script():
    """Create a script to analyze all variant results"""

    analysis_script = '''"""
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
'''

    with open("analyze_all_variants.py", 'w', encoding='utf-8') as f:
        f.write(analysis_script)

    log("Created analyze_all_variants.py")

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="ORB Variants Overnight Runner")
    parser.add_argument('--resume', action='store_true', help="Resume from previous run")
    parser.add_argument('--retry-failed', action='store_true', help="Retry only failed variants")
    args = parser.parse_args()

    # Create analysis script
    create_analysis_script()

    # Run overnight testing
    try:
        run_overnight(resume=args.resume, retry_failed=args.retry_failed)
    except KeyboardInterrupt:
        log("")
        log("Interrupted by user. Progress saved.")
        log("To resume: python orb_variants_overnight.py --resume")
    except Exception as e:
        log(f"FATAL ERROR: {str(e)}")
        raise

if __name__ == "__main__":
    main()
