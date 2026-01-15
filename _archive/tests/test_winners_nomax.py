"""
Test Winners Without MAX_STOP and ASIA_TP_CAP Filters

Uses the EXACT SAME LOGIC as original scripts.
Only changes: MAX_STOP_TICKS and ASIA_TP_CAP_TICKS set to 999999

Tests 5 winning configs:
1. 10:00 - 5m exec, RR 3.0, confirm 2
2. 18:00 - 5m half-SL, RR 2.0, confirm 1, buffer 0
3. 11:00 - 5m half-SL, RR 3.0, confirm 1, buffer 0
4. 00:30 - 5m half-SL, RR 1.5, confirm 2, buffer 0
5. 09:00 - 5m exec, RR 3.0, confirm 2

Results written to: orb_trades_5m_exec_nomax
Original results in: orb_trades_5m_exec
"""

import subprocess
import sys

print("="*80)
print("TESTING WINNERS WITHOUT MAX_STOP AND ASIA_TP_CAP FILTERS")
print("="*80)
print("Using EXACT same logic as original scripts")
print("Only difference: MAX_STOP=999999, ASIA_TP_CAP=999999")
print()
print("Testing 5 winning configs (~10-15 minutes)...")
print("="*80)
print()

configs = [
    # (script, rr, confirm, sl_mode, buffer, name)
    ("backtest_orb_exec_5m_nomax.py", 3.0, 2, None, None, "10:00 ORB (5m exec)"),
    ("backtest_orb_exec_5m_nomax.py", 3.0, 2, None, None, "09:00 ORB (5m exec)"),
    ("backtest_orb_exec_5mhalfsl_nomax.py", 2.0, 1, "half", 0, "18:00 ORB (half-SL)"),
    ("backtest_orb_exec_5mhalfsl_nomax.py", 3.0, 1, "half", 0, "11:00 ORB (half-SL)"),
    ("backtest_orb_exec_5mhalfsl_nomax.py", 1.5, 2, "half", 0, "00:30 ORB (half-SL)"),
]

for i, (script, rr, confirm, sl_mode, buffer, name) in enumerate(configs, 1):
    print(f"[{i}/5] {name}")
    print("-"*80)

    cmd = f"python {script} --rr {rr} --confirm {confirm}"
    if sl_mode:
        cmd += f" --sl {sl_mode} --buffer-ticks {buffer}"

    print(f"Command: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        # Show last few lines of output
        lines = result.stdout.strip().split('\n')
        for line in lines[-5:]:
            print(f"  {line}")
        print("  [SUCCESS]")
    else:
        print(f"  [FAILED]")
        print(result.stderr[:500])

    print()

print("="*80)
print("TEST COMPLETE")
print("="*80)
print()
print("Next step: python compare_filtered_vs_nomax.py")
print()
