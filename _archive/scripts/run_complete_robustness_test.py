"""
Master Runner: Complete Robustness Test Pipeline

Executes all 5 steps of the robustness testing system:
1. Audit database and identify filtered table
2. Extract candidate configs (trades >= 100, total_r >= 20)
3. Export to candidate_configs.json/csv
4. Run robustness batch test (no-max backtest for all candidates)
5. Generate final comparison report

Run this to execute the complete pipeline from start to finish.
"""

import subprocess
import sys
import os
from datetime import datetime

def run_step(step_num, script_name, description):
    """Run a single step script"""

    print()
    print("="*100)
    print(f"STEP {step_num}: {description}")
    print(f"Script: {script_name}")
    print("="*100)
    print()

    if not os.path.exists(script_name):
        print(f"[FAIL] Script not found: {script_name}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False,
            text=True
        )
        print()
        print(f"[SUCCESS] Step {step_num} complete")
        return True

    except subprocess.CalledProcessError as e:
        print()
        print(f"[FAIL] Step {step_num} failed with exit code {e.returncode}")
        return False

def main():
    """Execute complete robustness test pipeline"""

    start_time = datetime.now()

    print("="*100)
    print("COMPLETE ROBUSTNESS TEST PIPELINE")
    print("="*100)
    print()
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("This will:")
    print("  1. Audit database and identify filtered table")
    print("  2. Extract candidate configs (profitable configs)")
    print("  3. Run no-max backtest for all candidates (NO FILTERS)")
    print("  4. Generate comparison report (filtered vs no-max)")
    print()
    print("[IMPORTANT] This may take several minutes to complete")
    print()

    input("Press ENTER to continue or Ctrl+C to cancel...")

    steps = [
        (1, "audit_robustness_setup.py", "Audit Database & Identify Filtered Table"),
        (2, "extract_candidate_configs.py", "Extract Candidate Configs"),
        (4, "run_robustness_batch.py", "Run Robustness Batch Tests"),
        (5, "generate_robustness_report.py", "Generate Final Comparison Report"),
    ]

    for step_num, script, description in steps:
        success = run_step(step_num, script, description)

        if not success:
            print()
            print("="*100)
            print("PIPELINE FAILED")
            print("="*100)
            print()
            print(f"Failed at Step {step_num}: {description}")
            print(f"Fix the error and re-run: python {script}")
            print()
            sys.exit(1)

    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    print()
    print("="*100)
    print("PIPELINE COMPLETE")
    print("="*100)
    print()
    print(f"Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print()
    print("Output Files:")
    print("  - filtered_table_name.txt")
    print("  - candidate_configs.csv")
    print("  - candidate_configs.json")
    print("  - robustness_comparison.csv")
    print("  - robust_edges.csv (if any found)")
    print("  - ROBUSTNESS_REPORT.md")
    print()
    print("Database Tables Created:")
    print("  - orb_robustness_results (no-max backtest results)")
    print()
    print("[SUCCESS] Complete robustness test pipeline finished")
    print()
    print("Next: Read ROBUSTNESS_REPORT.md for results")
    print()
    print("="*100)

if __name__ == "__main__":
    main()
