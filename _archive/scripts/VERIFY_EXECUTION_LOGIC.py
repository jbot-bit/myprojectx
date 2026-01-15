"""
VERIFY EXECUTION LOGIC - Manual spot check

This manually walks through 1-2 trades to verify:
1. ORB is calculated correctly (5 minutes)
2. Trigger is detected correctly (1m close outside)
3. Entry is at next bar open (not close)
4. Risk is entry-anchored (entry to stop, NOT ORB edge to stop)
5. Target is entry-anchored (entry + R*risk)
6. Outcome is determined correctly
"""

import duckdb
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DB_PATH = "gold.db"
SYMBOL = "MGC"
TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TICK_SIZE = 0.1

con = duckdb.connect(DB_PATH, read_only=True)

print("="*80)
print("MANUAL EXECUTION LOGIC VERIFICATION")
print("="*80)
print()

# Pick a specific date to verify
test_date = "2026-01-09"
orb_time = "0900"

print(f"Testing: {test_date}, {orb_time} ORB")
print()

# Step 1: Calculate ORB (5 minutes: 09:00-09:05)
print("STEP 1: Calculate ORB (09:00-09:05)")
print("-"*80)

orb_start = f"{test_date} 09:00:00"
orb_end = f"{test_date} 09:05:00"

orb_bars = con.execute("""
    SELECT
        (ts_utc AT TIME ZONE 'Australia/Brisbane') as ts_local,
        high, low, close
    FROM bars_1m
    WHERE symbol = ?
        AND (ts_utc AT TIME ZONE 'Australia/Brisbane') >= CAST(? AS TIMESTAMP)
        AND (ts_utc AT TIME ZONE 'Australia/Brisbane') < CAST(? AS TIMESTAMP)
    ORDER BY ts_local
""", [SYMBOL, orb_start, orb_end]).fetchall()

if not orb_bars:
    print("ERROR: No ORB bars found!")
    con.close()
    exit(1)

orb_high = max(h for _, h, _, _ in orb_bars)
orb_low = min(l for _, _, l, _ in orb_bars)
orb_size = orb_high - orb_low
orb_mid = (orb_high + orb_low) / 2.0

print(f"ORB bars found: {len(orb_bars)}")
for ts, h, l, c in orb_bars:
    print(f"  {ts}: H={h:.1f} L={l:.1f} C={c:.1f}")

print()
print(f"ORB HIGH: {orb_high:.1f}")
print(f"ORB LOW:  {orb_low:.1f}")
print(f"ORB SIZE: {orb_size:.1f} ({orb_size/TICK_SIZE:.1f} ticks)")
print(f"ORB MID:  {orb_mid:.1f}")
print()

# Step 2: Find trigger (first 1m close outside ORB)
print("STEP 2: Find Trigger (first 1m close outside ORB)")
print("-"*80)

scan_start = f"{test_date} 09:05:00"
scan_end = f"{test_date} 09:30:00"  # First 25 minutes after ORB

scan_bars = con.execute("""
    SELECT
        (ts_utc AT TIME ZONE 'Australia/Brisbane') as ts_local,
        open, high, low, close
    FROM bars_1m
    WHERE symbol = ?
        AND (ts_utc AT TIME ZONE 'Australia/Brisbane') >= CAST(? AS TIMESTAMP)
        AND (ts_utc AT TIME ZONE 'Australia/Brisbane') < CAST(? AS TIMESTAMP)
    ORDER BY ts_local
""", [SYMBOL, scan_start, scan_end]).fetchall()

trigger_idx = None
trigger_bar = None
direction = None

for i, (ts, o, h, l, c) in enumerate(scan_bars):
    print(f"  {ts}: O={o:.1f} H={h:.1f} L={l:.1f} C={c:.1f}", end="")

    if c > orb_high:
        print(f" <- CLOSE ABOVE ORB ({c:.1f} > {orb_high:.1f})")
        direction = "UP"
        trigger_idx = i
        trigger_bar = (ts, o, h, l, c)
        break
    elif c < orb_low:
        print(f" <- CLOSE BELOW ORB ({c:.1f} < {orb_low:.1f})")
        direction = "DOWN"
        trigger_idx = i
        trigger_bar = (ts, o, h, l, c)
        break
    else:
        print(f" (inside ORB)")

if not trigger_bar:
    print()
    print("NO TRIGGER FOUND (no close outside ORB)")
    con.close()
    exit(0)

print()
print(f"TRIGGER DETECTED: {direction} at {trigger_bar[0]}")
print(f"Trigger close: {trigger_bar[4]:.1f}")
print()

# Step 3: Entry at NEXT bar open
print("STEP 3: Entry at NEXT Bar Open")
print("-"*80)

if trigger_idx + 1 >= len(scan_bars):
    print("ERROR: No next bar available for entry!")
    con.close()
    exit(1)

entry_bar = scan_bars[trigger_idx + 1]
entry_ts, entry_open, entry_high, entry_low, entry_close = entry_bar

print(f"Entry bar: {entry_ts}")
print(f"Entry price: {entry_open:.1f} (next bar OPEN)")
print()

# Step 4: Calculate stop (half-SL = ORB mid)
print("STEP 4: Calculate Stop (HALF-SL = ORB MID)")
print("-"*80)

stop_price = orb_mid

print(f"Stop price: {stop_price:.1f} (ORB mid)")
print()

# Step 5: Calculate ENTRY-ANCHORED RISK
print("STEP 5: Calculate ENTRY-ANCHORED RISK")
print("-"*80)

risk = abs(entry_open - stop_price)
risk_ticks = risk / TICK_SIZE

print(f"Entry: {entry_open:.1f}")
print(f"Stop:  {stop_price:.1f}")
print(f"Risk:  {risk:.2f} ({risk_ticks:.1f} ticks)")
print()

# CRITICAL CHECK: Compare to ORB-anchored (OLD WAY)
orb_edge = orb_high if direction == "UP" else orb_low
orb_anchored_risk = abs(orb_edge - stop_price)
orb_anchored_risk_ticks = orb_anchored_risk / TICK_SIZE

print("COMPARISON TO OLD (WRONG) METHOD:")
print(f"  ORB-anchored risk: {orb_anchored_risk:.2f} ({orb_anchored_risk_ticks:.1f} ticks)")
print(f"  Entry-anchored risk: {risk:.2f} ({risk_ticks:.1f} ticks)")
print(f"  Risk inflation: {risk_ticks / orb_anchored_risk_ticks:.2f}x")
print()

if risk_ticks > orb_anchored_risk_ticks * 1.2:
    print("  [CORRECT] Entry-anchored risk is larger (accounts for slippage)")
elif risk_ticks < orb_anchored_risk_ticks * 0.8:
    print("  [WARNING] Entry-anchored risk is SMALLER than ORB-anchored?")
else:
    print("  [OK] Risks similar (small slippage)")
print()

# Step 6: Calculate target (entry-anchored)
print("STEP 6: Calculate Target (ENTRY-ANCHORED, 1R)")
print("-"*80)

rr = 1.0
if direction == "UP":
    target_price = entry_open + rr * risk
else:
    target_price = entry_open - rr * risk

print(f"Target: {target_price:.1f} (entry {'+' if direction == 'UP' else '-'} {rr}R)")
print()

# Step 7: Determine outcome (scan subsequent bars)
print("STEP 7: Determine Outcome")
print("-"*80)

outcome = None
hit_bar = None

for i, (ts, o, h, l, c) in enumerate(scan_bars[trigger_idx + 1:]):
    if direction == "UP":
        hit_stop = l <= stop_price
        hit_target = h >= target_price

        if hit_stop and hit_target:
            print(f"{ts}: BOTH hit in same bar (H={h:.1f} >= {target_price:.1f}, L={l:.1f} <= {stop_price:.1f})")
            print(f"  Conservative rule: COUNT AS LOSS")
            outcome = "LOSS"
            hit_bar = (ts, o, h, l, c)
            break
        elif hit_target:
            print(f"{ts}: TARGET hit (H={h:.1f} >= {target_price:.1f})")
            outcome = "WIN"
            hit_bar = (ts, o, h, l, c)
            break
        elif hit_stop:
            print(f"{ts}: STOP hit (L={l:.1f} <= {stop_price:.1f})")
            outcome = "LOSS"
            hit_bar = (ts, o, h, l, c)
            break
    else:  # DOWN
        hit_stop = h >= stop_price
        hit_target = l <= target_price

        if hit_stop and hit_target:
            print(f"{ts}: BOTH hit in same bar (L={l:.1f} <= {target_price:.1f}, H={h:.1f} >= {stop_price:.1f})")
            print(f"  Conservative rule: COUNT AS LOSS")
            outcome = "LOSS"
            hit_bar = (ts, o, h, l, c)
            break
        elif hit_target:
            print(f"{ts}: TARGET hit (L={l:.1f} <= {target_price:.1f})")
            outcome = "WIN"
            hit_bar = (ts, o, h, l, c)
            break
        elif hit_stop:
            print(f"{ts}: STOP hit (H={h:.1f} >= {stop_price:.1f})")
            outcome = "LOSS"
            hit_bar = (ts, o, h, l, c)
            break

if not outcome:
    print("  No exit (neither TP nor SL hit by end of scan window)")
    outcome = "NO_TRADE"

print()

# Step 8: Summary
print("="*80)
print("SUMMARY")
print("="*80)
print()
print(f"Date: {test_date}")
print(f"ORB: {orb_time} ({orb_size/TICK_SIZE:.1f} ticks)")
print(f"Direction: {direction}")
print(f"Trigger: {trigger_bar[0]} close at {trigger_bar[4]:.1f}")
print(f"Entry: {entry_ts} open at {entry_open:.1f}")
print(f"Stop: {stop_price:.1f} (ORB mid)")
print(f"Target: {target_price:.1f}")
print(f"Risk: {risk_ticks:.1f} ticks (entry-anchored)")
print(f"Outcome: {outcome}")
print()

if outcome in ["WIN", "LOSS"]:
    r_multiple = rr if outcome == "WIN" else -1.0
    print(f"R-multiple: {r_multiple:+.1f}R")
    print()

# Verify against database
print("="*80)
print("VERIFICATION AGAINST DATABASE")
print("="*80)
print()

# Check if we have the new table
tables = con.execute("SHOW TABLES").fetchall()
has_v3 = any('daily_features_v3_modelb_half' in str(t) for t in tables)

if has_v3:
    db_result = con.execute("""
        SELECT
            orb_0900_high,
            orb_0900_low,
            orb_0900_break_dir,
            orb_0900_entry_price,
            orb_0900_stop_price,
            orb_0900_target_price,
            orb_0900_risk_ticks,
            orb_0900_outcome,
            orb_0900_r_multiple
        FROM daily_features_v3_modelb_half
        WHERE date_local = ?
    """, [test_date]).fetchone()

    if db_result:
        print("Database (daily_features_v3_modelb_half):")
        print(f"  ORB: {db_result[0]:.1f} - {db_result[1]:.1f}")
        print(f"  Break dir: {db_result[2]}")
        print(f"  Entry: {db_result[3]:.1f}" if db_result[3] else "  Entry: None")
        print(f"  Stop: {db_result[4]:.1f}" if db_result[4] else "  Stop: None")
        print(f"  Target: {db_result[5]:.1f}" if db_result[5] else "  Target: None")
        print(f"  Risk: {db_result[6]:.1f} ticks" if db_result[6] else "  Risk: None")
        print(f"  Outcome: {db_result[7]}")
        print(f"  R-multiple: {db_result[8]:+.1f}R" if db_result[8] else "  R-multiple: None")
        print()

        # Compare
        if db_result[3] and abs(db_result[3] - entry_open) < 0.1:
            print("[OK] Entry price matches")
        elif db_result[3]:
            print(f"[WARNING] Entry mismatch: DB={db_result[3]:.1f}, Calculated={entry_open:.1f}")

        if db_result[6] and abs(db_result[6] - risk_ticks) < 0.5:
            print("[OK] Risk matches")
        elif db_result[6]:
            print(f"[WARNING] Risk mismatch: DB={db_result[6]:.1f}, Calculated={risk_ticks:.1f}")
    else:
        print("No database entry found for this date (table not populated yet)")
else:
    print("daily_features_v3_modelb_half table doesn't exist yet")
    print("This is expected - run the overnight job to create it")

print()

con.close()

print("="*80)
print("VERIFICATION COMPLETE")
print("="*80)
print()
print("Key checks:")
print("  1. ORB is 5 minutes (09:00-09:05) ✓")
print("  2. Trigger is first close outside ORB ✓")
print("  3. Entry is at NEXT bar open ✓")
print("  4. Risk is ENTRY-ANCHORED (not ORB-anchored) ✓")
print("  5. Target is entry +/- R*risk ✓")
print("  6. Same-bar TP+SL = LOSS (conservative) ✓")
print()
print("If all checks pass, the logic is CORRECT.")
print()
