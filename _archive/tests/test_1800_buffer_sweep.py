"""
Test 18:00 ORB with Different Half-SL Buffer Values

Tests the strongest edge (18:00 ORB, RR=2.0, confirm=1, half-SL)
with different buffer tick values to see if it improves results.

Buffer explanation:
- buffer=0: Stop at midpoint of ORB
- buffer=2: Stop 2 ticks (0.2) away from midpoint (tighter stop)
- buffer=5: Stop 5 ticks (0.5) away from midpoint
- buffer=10: Stop 10 ticks (1.0) away from midpoint
- etc.

Tests WITH filters (MAX_STOP=100, ASIA_TP_CAP=150)
"""

import subprocess
import sys

print("="*80)
print("18:00 ORB BUFFER SWEEP TEST")
print("="*80)
print("Config: RR=2.0, confirm=1, half-SL, varying buffer")
print("Baseline: buffer=0 -> +60.0R (504 trades, 37.0% WR)")
print("="*80)
print()

# Test different buffer values (in ticks)
buffer_values = [0, 2, 5, 10, 15, 20]

print(f"Testing {len(buffer_values)} buffer values: {buffer_values}")
print("Estimated time: 3-5 minutes")
print()

for i, buffer in enumerate(buffer_values, 1):
    print(f"[{i}/{len(buffer_values)}] Buffer = {buffer} ticks")
    print("-"*80)

    cmd = f"python backtest_orb_exec_5mhalfsl.py --rr 2.0 --confirm 1 --sl half --buffer-ticks {buffer}"
    print(f"Command: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
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
print("Next step: python analyze_1800_buffer_results.py")
print()
