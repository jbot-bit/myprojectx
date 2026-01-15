"""
Verify half-SL risk calculation methodology

CRITICAL: Check if backtest uses ORB-anchored R or entry-anchored R
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"
SYMBOL = "MGC"

con = duckdb.connect(DB_PATH, read_only=True)

print("="*80)
print("HALF-SL RISK CALCULATION VERIFICATION")
print("="*80)
print()

# Sample 0900 trades with half-SL from daily_features_v2_half
print("Checking daily_features_v2_half methodology:")
print()

# Get a few sample trades
sample = con.execute("""
    SELECT
        date_local,
        orb_0900_high,
        orb_0900_low,
        orb_0900_size,
        orb_0900_break_dir,
        orb_0900_stop_price,
        orb_0900_risk_ticks,
        orb_0900_outcome,
        orb_0900_r_multiple
    FROM daily_features_v2_half
    WHERE orb_0900_break_dir IN ('UP', 'DOWN')
        AND orb_0900_outcome IN ('WIN', 'LOSS')
    LIMIT 10
""").df()

print("Sample trades from daily_features_v2_half:")
print(sample.to_string())
print()

# Now get actual 1m bars to see real entry prices
print("="*80)
print("CHECKING REAL ENTRY PRICES FROM 1M BARS")
print("="*80)
print()

for idx, row in sample.head(3).iterrows():
    date_local = row['date_local']
    orb_high = row['orb_0900_high']
    orb_low = row['orb_0900_low']
    orb_size = row['orb_0900_size']
    orb_mid = (orb_high + orb_low) / 2.0
    break_dir = row['orb_0900_break_dir']
    stop_price = row['orb_0900_stop_price']
    risk_ticks = row['orb_0900_risk_ticks']
    outcome = row['orb_0900_outcome']
    r_multiple = row['orb_0900_r_multiple']

    print(f"Date: {date_local}")
    print(f"  ORB: {orb_low:.2f} - {orb_high:.2f} (size={orb_size:.2f}, mid={orb_mid:.2f})")
    print(f"  Break: {break_dir}")
    print(f"  Stop: {stop_price:.2f}")
    print(f"  Backtest risk: {risk_ticks:.1f} ticks")
    print()

    # Get actual 1m bars after 09:05 to find entry
    bars = con.execute("""
        SELECT
            (ts_utc AT TIME ZONE 'Australia/Brisbane') as ts_local,
            high, low, close
        FROM bars_1m
        WHERE symbol = ?
            AND (ts_utc AT TIME ZONE 'Australia/Brisbane') > CAST(? || ' 09:05:00' AS TIMESTAMP)
            AND (ts_utc AT TIME ZONE 'Australia/Brisbane') <= CAST(? || ' 09:30:00' AS TIMESTAMP)
        ORDER BY ts_local
        LIMIT 10
    """, [SYMBOL, date_local, date_local]).fetchall()

    if not bars:
        print("  [NO BARS FOUND]")
        print()
        continue

    # Find first close outside ORB
    entry_price = None
    entry_ts = None

    for ts, h, l, c in bars:
        if break_dir == 'UP' and c > orb_high:
            entry_price = c
            entry_ts = ts
            break
        elif break_dir == 'DOWN' and c < orb_low:
            entry_price = c
            entry_ts = ts
            break

    if entry_price is None:
        print("  [NO ENTRY FOUND]")
        print()
        continue

    print(f"  REAL ENTRY: {entry_price:.2f} at {entry_ts}")

    # Calculate real risk
    real_risk = abs(entry_price - stop_price)
    real_risk_ticks = real_risk / 0.1

    print(f"  REAL RISK: {real_risk:.2f} ({real_risk_ticks:.1f} ticks)")
    print()

    # Calculate backtest risk
    orb_edge = orb_high if break_dir == 'UP' else orb_low
    backtest_risk = abs(orb_edge - stop_price)
    backtest_risk_ticks = backtest_risk / 0.1

    print(f"  BACKTEST RISK: {backtest_risk:.2f} ({backtest_risk_ticks:.1f} ticks)")
    print(f"    [Calculated from ORB edge ({orb_edge:.2f}) to stop ({stop_price:.2f})]")
    print()

    # Entry slippage
    if break_dir == 'UP':
        slippage = entry_price - orb_high
    else:
        slippage = orb_low - entry_price

    slippage_ticks = slippage / 0.1

    print(f"  ENTRY SLIPPAGE: {slippage:.2f} ({slippage_ticks:.1f} ticks) outside ORB")
    print()

    # Risk ratio
    risk_ratio = real_risk_ticks / backtest_risk_ticks if backtest_risk_ticks > 0 else 0

    print(f"  RISK INFLATION: Real risk is {risk_ratio:.2f}x backtest risk")
    print()

    # Calculate target
    r_orb = backtest_risk
    if break_dir == 'UP':
        target = orb_edge + 1.0 * r_orb
    else:
        target = orb_edge - 1.0 * r_orb

    print(f"  TARGET: {target:.2f}")

    # Real reward
    real_reward = abs(target - entry_price)
    real_reward_ticks = real_reward / 0.1

    print(f"  REAL REWARD (if win): {real_reward:.2f} ({real_reward_ticks:.1f} ticks)")
    print(f"  REAL R:R: {real_reward_ticks:.1f} / {real_risk_ticks:.1f} = {real_reward_ticks/real_risk_ticks:.2f}:1")
    print()

    # Outcome conversion
    print(f"  BACKTEST RESULT: {outcome} ({r_multiple:+.2f}R)")

    if outcome == 'WIN':
        real_r = real_reward_ticks / real_risk_ticks
        print(f"  REAL R (if using real risk): +{real_r:.2f}R")
    elif outcome == 'LOSS':
        print(f"  REAL R (if using real risk): -1.00R (by definition)")

    print()
    print("-"*80)
    print()

con.close()

print("="*80)
print("CONCLUSION:")
print("="*80)
print()
print("If 'RISK INFLATION' is > 1.0, the backtest UNDERSTATES real risk.")
print("This means:")
print("  - Wins are OVERSTATED in R terms (same tick profit / larger risk)")
print("  - Losses are UNDERSTATED in R terms (backtest shows -1.0R but real risk is larger)")
print()
print("For tiny ORBs (like 0900 with 1.7 tick median), inflation can be 2-3x,")
print("making the backtest results unrealistic for real trading.")
print()
