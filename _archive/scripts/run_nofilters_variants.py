"""
Run No-Filters Variants

Tests the same variant grid but WITHOUT:
- MAX_STOP_TICKS filter (was 100)
- ASIA_TP_CAP filter (was 150)

This allows comparison to see if the filters are helping or hurting performance.
Results written to separate _nofilters tables for side-by-side comparison.
"""

import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
import argparse

# Same grids as original, but using nofilters scripts
RR_GRID_1M = [1.5, 2.0, 2.5, 3.0]
CONFIRM_GRID_1M = [1, 2, 3]

RR_GRID_5M = [1.5, 2.0, 2.5, 3.0]
CONFIRM_GRID_5M = [1, 2, 3]

RR_GRID_5M_HALF = [1.5, 2.0, 2.5, 3.0]
CONFIRM_GRID_5M_HALF = [1, 2]
SL_MODES = ["full", "half"]
BUFFER_GRID = [0, 5, 10, 15, 20]

PROGRESS_FILE = "nofilters_progress.json"
LOG_FILE = "nofilters_runner.log"

def build_variants():
    """Build all no-filter variant configurations"""
    variants = []

    # 1. 1m midstop nofilters
    for rr in RR_GRID_1M:
        for confirm in CONFIRM_GRID_1M:
            variants.append({
                'id': f"1m_nofilters_rr{rr}_c{confirm}",
                'type': '1m_nofilters',
                'script': 'backtest_orb_exec_1m_nofilters.py',
                'rr': rr,
                'confirm': confirm,
                'command': f"python backtest_orb_exec_1m_nofilters.py --rr {rr} --confirm {confirm}"
            })

    # 2. 5m exec nofilters
    for rr in RR_GRID_5M:
        for confirm in CONFIRM_GRID_5M:
            variants.append({
                'id': f"5m_nofilters_rr{rr}_c{confirm}",
                'type': '5m_nofilters',
                'script': 'backtest_orb_exec_5m_nofilters.py',
                'rr': rr,
                'confirm': confirm,
                'command': f"python backtest_orb_exec_5m_nofilters.py --rr {rr} --confirm {confirm}"
            })

    # 3. 5m half-SL nofilters
    for sl_mode in SL_MODES:
        for rr in RR_GRID_5M_HALF:
            for confirm in CONFIRM_GRID_5M_HALF:
                for buffer in BUFFER_GRID:
                    variants.append({
                        'id': f"5m_nofilters_{sl_mode}_rr{rr}_c{confirm}_b{buffer}",
                        'type': '5m_half_sl_nofilters',
                        'script': 'backtest_orb_exec_5mhalfsl_nofilters.py',
                        'rr': rr,
                        'confirm': confirm,
                        'sl_mode': sl_mode,
                        'buffer': buffer,
                        'command': f"python backtest_orb_exec_5mhalfsl_nofilters.py --rr {rr} --confirm {confirm} --sl {sl_mode} --buffer-ticks {buffer}"
                    })

    return variants

def load_progress():
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

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')

def run_variant(variant):
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
            timeout=3600
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

def run_nofilters(resume=False):
    """Main runner for no-filters variants"""

    log("="*80)
    log("NO-FILTERS VARIANT RUNNER - STARTED")
    log("="*80)
    log("Testing WITHOUT max_stop and asia_tp_cap filters")
    log("")

    variants = build_variants()
    total = len(variants)

    log(f"Total variants to test: {total}")
    log(f"  - 1m nofilters: {len([v for v in variants if v['type'] == '1m_nofilters'])}")
    log(f"  - 5m nofilters: {len([v for v in variants if v['type'] == '5m_nofilters'])}")
    log(f"  - 5m half-SL nofilters: {len([v for v in variants if v['type'] == '5m_half_sl_nofilters'])}")

    progress = load_progress()

    if not resume:
        progress = {
            'started_at': datetime.now().isoformat(),
            'completed': [],
            'failed': [],
            'current': None,
            'total_variants': total
        }
        log("Starting fresh run")
    else:
        log(f"Resuming from previous run ({len(progress['completed'])} completed)")

    completed_ids = set(progress['completed'])
    variants = [v for v in variants if v['id'] not in completed_ids]

    if len(variants) == 0:
        log("No variants to run!")
        return

    log(f"Running {len(variants)} variants...")
    log("")

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
        time.sleep(2)

    log("")
    log("="*80)
    log("NO-FILTERS RUNNER - COMPLETED")
    log("="*80)
    log(f"Total variants: {total}")
    log(f"Completed: {len(progress['completed'])}")
    log(f"Failed: {len(progress['failed'])}")

    if progress['failed']:
        log("")
        log("Failed variants:")
        for failed in progress['failed']:
            log(f"  - {failed['id']}: {failed['error']}")
    else:
        log("")
        log(">> ALL NO-FILTERS VARIANTS COMPLETED SUCCESSFULLY!")

    log("")
    log("Next steps:")
    log("  1. Compare results: python compare_filtered_vs_nofilters.py")
    log("  2. Session analysis: python analyze_by_session.py --nofilters")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="No-Filters Variant Runner")
    parser.add_argument('--resume', action='store_true', help="Resume from previous run")
    args = parser.parse_args()

    try:
        run_nofilters(resume=args.resume)
    except KeyboardInterrupt:
        log("")
        log("Interrupted by user. Progress saved.")
        log("To resume: python run_nofilters_variants.py --resume")
    except Exception as e:
        log(f"FATAL ERROR: {str(e)}")
        raise
