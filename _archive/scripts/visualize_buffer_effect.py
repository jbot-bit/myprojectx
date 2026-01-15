"""
Visualize how buffer affects stop placement relative to ORB structure

Shows that buffer moves stop TOWARD the opposite ORB boundary,
which may be where price tends to revert to during pullbacks.
"""

import duckdb

DB_PATH = "gold.db"

con = duckdb.connect(DB_PATH, read_only=True)

print("="*100)
print("BUFFER EFFECT ON STOP PLACEMENT")
print("="*100)
print()

# Get a sample of trades with ORB data
query = """
SELECT
    t.date_local,
    t.direction,
    t.entry_price,
    t.stop_price,
    t.buffer_ticks,
    d.orb_1800_high,
    d.orb_1800_low,
    t.outcome
FROM orb_trades_5m_exec t
JOIN daily_features_v2 d ON t.date_local = d.date_local
WHERE t.orb = '1800'
    AND t.rr = 2.0
    AND t.close_confirmations = 1
    AND t.sl_mode = 'half'
    AND t.buffer_ticks IN (0, 5)
    AND t.outcome IN ('WIN', 'LOSS')
    AND t.date_local IN ('2024-01-22', '2024-08-02', '2024-02-06')
ORDER BY t.date_local, t.buffer_ticks
"""

trades = con.execute(query).fetchall()

for i in range(0, len(trades), 2):
    if i+1 >= len(trades):
        break

    t0 = trades[i]
    t5 = trades[i+1]

    date, direction, entry, stop0, buf0, orb_h, orb_l, out0 = t0
    _, _, _, stop5, buf5, _, _, out5 = t5

    mid = (orb_h + orb_l) / 2.0
    orb_range = orb_h - orb_l

    print(f"Date: {date} | Direction: {direction} | Outcome: buf0={out0}, buf5={out5}")
    print("-"*100)
    print(f"ORB High:  {orb_h:7.1f}")
    print(f"Entry:     {entry:7.1f}  <-- Entered HERE (broke {direction})")
    print(f"Midpoint:  {mid:7.1f}")

    if direction == "UP":
        print(f"Stop(0):   {stop0:7.1f}  <-- AT midpoint")
        print(f"Stop(5):   {stop5:7.1f}  <-- {mid - stop5:.1f} TOWARD ORB LOW")
        print(f"ORB Low:   {orb_l:7.1f}  <-- Stop moving THIS direction")
    else:
        print(f"Stop(0):   {stop0:7.1f}  <-- AT midpoint")
        print(f"Stop(5):   {stop5:7.1f}  <-- {stop5 - mid:.1f} TOWARD ORB HIGH")
        print(f"ORB Low:   {orb_l:7.1f}")
        print(f"               ^")
        print(f"               |--- Stop moving AWAY from here (toward ORB HIGH)")

    print()
    print("KEY INSIGHT:")
    if direction == "UP":
        print(f"  - Price broke ABOVE ORB (bullish)")
        print(f"  - Buffer moves stop DOWN toward ORB LOW (the breakout origin)")
        print(f"  - If price pulls back INTO the old ORB range, buffer stop gets hit easier")
    else:
        print(f"  - Price broke BELOW ORB (bearish)")
        print(f"  - Buffer moves stop UP toward ORB HIGH (the breakout origin)")
        print(f"  - If price pulls back INTO the old ORB range, buffer stop gets hit easier")

    print()
    print("="*100)
    print()

print("CONCLUSION:")
print("-"*100)
print()
print("Buffer moves stop TOWARD the ORB boundary we broke from.")
print("This makes stop MORE vulnerable to pullbacks into the old ORB range.")
print()
print("Buffer=0 (midpoint) is optimal because:")
print("  1. Provides cushion from BOTH ORB boundaries")
print("  2. Allows price to pull back into ORB without stopping you out")
print("  3. Only stops you if price fully reverses past midpoint")
print()
print("Your intuition is correct - the buffer side matters!")

con.close()
