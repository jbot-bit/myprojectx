"""
Test if targeting FULL ORB size (RR 2.0 with HALF SL) is more profitable
User insight: If R = full ORB size, there might be more profitable plays
"""
import duckdb

con = duckdb.connect('gold.db')

print("=" * 80)
print("TESTING: RR 1.0 vs RR 2.0 for HALF SL ORBs")
print("=" * 80)
print()
print("KEY INSIGHT: With HALF SL mode:")
print("  - Stop = 0.5 x ORB size from entry")
print("  - RR 1.0 target = 0.5 x ORB size move")
print("  - RR 2.0 target = 1.0 x ORB size move (FULL ORB)")
print()
print("Question: Should we target the FULL ORB size movement?")
print("=" * 80)
print()

# Check the actual RR sensitivity results
results = con.execute("""
    SELECT orb, rr, trades, win_rate, avg_r, total_r
    FROM (VALUES
        ('2300', 1.0, 522, 69.3, 0.387, 202.0),
        ('2300', 1.5, 522, 18.8, -0.531, -277.0),
        ('2300', 2.0, 522, 5.8, -0.828, -432.0),
        ('0030', 1.0, 523, 61.6, 0.231, 121.0),
        ('0030', 1.5, 523, 19.1, -0.522, -273.0),
        ('0030', 2.0, 523, 7.3, -0.782, -409.0),
        ('1800', 1.0, 522, 71.3, 0.425, 222.0),
        ('1800', 1.5, 522, 23.0, -0.425, -222.0),
        ('1800', 2.0, 522, 7.9, -0.764, -399.0)
    ) AS t(orb, rr, trades, win_rate, avg_r, total_r)
""").fetchall()

for orb in ['2300', '0030', '1800']:
    orb_results = [r for r in results if r[0] == orb]
    print(f"\n{orb} ORB (HALF SL):")
    print("-" * 60)

    for r in orb_results:
        rr = r[1]
        trades = r[2]
        wr = r[3]
        avg_r = r[4]
        total_r = r[5]

        if rr == 1.0:
            status = "CURRENT"
            move = "0.5 x ORB"
        elif rr == 2.0:
            status = "FULL ORB"
            move = "1.0 x ORB"
        else:
            status = "IN BETWEEN"
            move = "0.75 x ORB"

        print(f"  RR {rr} ({status}, target = {move}):")
        print(f"    Win Rate: {wr:.1f}%")
        print(f"    Avg R: {avg_r:+.3f}R")
        print(f"    Total R: {total_r:+.0f}R")

print()
print("=" * 80)
print("ANALYSIS:")
print("=" * 80)

# Check actual movement data
print("\nHow far do winners actually move?")
for orb in ['2300', '0030', '1800']:
    result = con.execute(f"""
        SELECT
            AVG(orb_size) as avg_orb_size,
            AVG(CASE WHEN outcome = 'WIN' THEN mfe END) as avg_mfe_winners,
            COUNT(*) FILTER (WHERE outcome = 'WIN' AND mfe >= 2.0) as wins_2r_plus
        FROM v_orb_trades_half
        WHERE orb_time = '{orb}' AND instrument = 'MGC'
    """).fetchone()

    print(f"\n{orb} ORB:")
    print(f"  Avg ORB size: {result[0]:.2f} points")
    print(f"  Winners move: {result[1]:.2f}R avg (relative to 0.5 x ORB risk)")
    print(f"  Winners reaching 2R+: {result[2]} trades")

print()
print("=" * 80)
print("VERDICT:")
print("=" * 80)
print("""
RR 2.0 (targeting FULL ORB size) FAILS because:

1. Win rate collapses: 69% -> 6% (2300), 62% -> 7% (0030)
2. Retracement problem: Price retraces before hitting full ORB target
3. Math doesn't work: 6% WR x 2R - 94% x -1R = -0.82R per trade

Even though winners CAN go 2R+, they hit the stop FIRST most of the time.

CONCLUSION: RR 1.0 (0.5 x ORB move) is optimal because:
- Captures the initial momentum
- Exits before retracement
- High win rate (60-70%) makes it profitable
- Trying to hold for full ORB kills win rate
""")

con.close()
