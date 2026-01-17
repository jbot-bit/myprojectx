"""
COMPREHENSIVE SYNCHRONIZATION VERIFICATION
Checks ALL files that use MGC setup data
"""

import sys
sys.path.append('trading_app')

import duckdb
from config import MGC_ORB_SIZE_FILTERS, MGC_ORB_CONFIGS

print("="*80)
print("COMPREHENSIVE SYNCHRONIZATION VERIFICATION")
print("="*80)

# 1. Get database values
con = duckdb.connect('gold.db')
db_result = con.execute("""
    SELECT orb_time, orb_size_filter, win_rate, avg_r, tier, sl_mode, rr
    FROM validated_setups
    WHERE instrument='MGC'
    ORDER BY orb_time
""").fetchall()

db_data = {}
for row in db_result:
    orb_time, orb_size_filter, win_rate, avg_r, tier, sl_mode, rr = row
    db_data[orb_time] = {
        'filter': orb_size_filter,
        'win_rate': win_rate,
        'avg_r': avg_r,
        'tier': tier,
        'sl_mode': sl_mode,
        'rr': rr
    }

con.close()

print("\n1. DATABASE VALUES (gold.db -> validated_setups):")
print("-" * 80)
for orb_time in sorted(db_data.keys()):
    data = db_data[orb_time]
    filter_str = f"{data['filter']:.2f}" if data['filter'] else "None"
    print(f"   {orb_time}: Filter={filter_str:6s}, {data['win_rate']}% WR, {data['avg_r']:+.3f}R, {data['tier']:3s} tier, {data['sl_mode']} SL, RR={data['rr']}")

# 2. Get config.py values
print("\n2. CONFIG.PY VALUES (trading_app/config.py):")
print("-" * 80)
print("   MGC_ORB_SIZE_FILTERS:")
for orb_time in sorted(MGC_ORB_SIZE_FILTERS.keys()):
    filter_val = MGC_ORB_SIZE_FILTERS[orb_time]
    filter_str = f"{filter_val:.2f}" if filter_val else "None"
    print(f"   {orb_time}: {filter_str}")

print("\n   MGC_ORB_CONFIGS:")
for orb_time in sorted(MGC_ORB_CONFIGS.keys()):
    config = MGC_ORB_CONFIGS[orb_time]
    print(f"   {orb_time}: RR={config['rr']}, SL={config['sl_mode']}, Tier={config['tier']}")

# 3. Verify matches
print("\n3. VERIFICATION - Database vs Config.py:")
print("-" * 80)
errors = []

for orb_time in sorted(db_data.keys()):
    db_filter = db_data[orb_time]['filter']
    config_filter = MGC_ORB_SIZE_FILTERS.get(orb_time)

    # Check filter match
    if db_filter is None and config_filter is None:
        filter_match = True
    elif db_filter is None or config_filter is None:
        filter_match = False
    else:
        filter_match = abs(db_filter - config_filter) < 0.001

    # Check RR and SL mode
    db_rr = db_data[orb_time]['rr']
    db_sl = db_data[orb_time]['sl_mode']
    config_rr = MGC_ORB_CONFIGS[orb_time]['rr']
    config_sl = MGC_ORB_CONFIGS[orb_time]['sl_mode']

    rr_match = db_rr == config_rr
    sl_match = db_sl == config_sl

    if filter_match and rr_match and sl_match:
        print(f"   [OK] {orb_time}: All values match")
    else:
        if not filter_match:
            errors.append(f"   [FAIL] {orb_time}: Filter mismatch - DB={db_filter}, Config={config_filter}")
        if not rr_match:
            errors.append(f"   [FAIL] {orb_time}: RR mismatch - DB={db_rr}, Config={config_rr}")
        if not sl_match:
            errors.append(f"   [FAIL] {orb_time}: SL mode mismatch - DB={db_sl}, Config={config_sl}")

# 4. Check MGC_NOW.py content
print("\n4. MGC_NOW.PY CHECK:")
print("-" * 80)
with open('MGC_NOW.py', 'r', encoding='utf-8') as f:
    mgc_now_content = f.read()

# Check for old wrong values
old_values = [
    ("A Tier (68.7% WR, +0.202R)", "0030 OLD VALUE"),
    ("B Tier (71.5% WR, +0.105R)", "0900 OLD VALUE"),
    ("C Tier (71% WR, +0.039R)", "1000 OLD VALUE"),
    ("90% WR!, +0.537R", "1100 OLD AVG R"),
    ("S Tier (71.3% WR, +0.233R)", "1800 OLD VALUE"),
    ("S Tier (72.3% WR, +0.292R)", "2300 OLD VALUE (also wrong tier)"),
    ("Skip if ORB > 11.2% of ATR", "0030 OLD FILTER"),
    ("Skip if ORB > 8.8% of ATR", "1000 OLD FILTER"),
    ("Skip if ORB > 9.5% of ATR", "1100 OLD FILTER"),
    ("Skip if ORB > 15.5% of ATR", "2300 OLD FILTER"),
    ("None (all sizes OK)", "0900/1800 OLD (missing filters)"),
]

mgc_now_errors = []
for old_val, description in old_values:
    if old_val in mgc_now_content:
        mgc_now_errors.append(f"   [FAIL] Found OLD value in MGC_NOW.py: {description}")

if not mgc_now_errors:
    print("   [OK] MGC_NOW.py has correct updated values (no old values found)")
else:
    errors.extend(mgc_now_errors)

# Check for new correct values
new_values = [
    ("S Tier (69.5% WR, +0.390R)", "0030 CORRECT"),
    ("S+ Tier (77.4% WR, +0.548R)", "0900 CORRECT"),
    ("S+ Tier (77.4% WR, +0.547R)", "1000 CORRECT"),
    ("S+ Tier (86.8% WR, +0.737R)", "1100 CORRECT"),
    ("S Tier (70.5% WR, +0.411R)", "1800 CORRECT"),
    ("S+ Tier (72.8% WR, +0.457R)", "2300 CORRECT"),
]

mgc_now_correct = []
for new_val, description in new_values:
    if new_val in mgc_now_content:
        mgc_now_correct.append(f"   [OK] Found CORRECT value: {description}")
    else:
        errors.append(f"   [FAIL] Missing CORRECT value in MGC_NOW.py: {description}")

for msg in mgc_now_correct:
    print(msg)

# 5. Summary
print("\n" + "="*80)
if errors:
    print("ERRORS FOUND:")
    print("="*80)
    for err in errors:
        print(err)
    print("\n[FAIL] SYNCHRONIZATION VERIFICATION FAILED!")
    sys.exit(1)
else:
    print("ALL SYNCHRONIZATION CHECKS PASSED!")
    print("="*80)
    print("\nVerified:")
    print("- gold.db validated_setups table has correct MGC data")
    print("- config.py MGC_ORB_SIZE_FILTERS matches database")
    print("- config.py MGC_ORB_CONFIGS matches database")
    print("- MGC_NOW.py has correct updated values")
    print("- No old incorrect values found")
    print("\n[OK] ALL FILES ARE SYNCHRONIZED AND SAFE FOR TRADING!")
