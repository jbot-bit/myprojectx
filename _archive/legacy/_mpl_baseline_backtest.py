
import duckdb
import csv
from collections import defaultdict

DB_PATH = "gold.db"
SYMBOL = "MPL"
OUTPUT_FILE = "mpl_baseline_results.csv"

con = duckdb.connect(DB_PATH)

# Query all ORBs
query = '''
SELECT
    date_local,
    'MPL' as instrument,
    '0900' as orb_time, orb_0900_outcome, orb_0900_r_multiple FROM daily_features_v2_mpl WHERE instrument = 'MPL'
UNION ALL SELECT date_local, 'MPL', '1000', orb_1000_outcome, orb_1000_r_multiple FROM daily_features_v2_mpl WHERE instrument = 'MPL'
UNION ALL SELECT date_local, 'MPL', '1100', orb_1100_outcome, orb_1100_r_multiple FROM daily_features_v2_mpl WHERE instrument = 'MPL'
UNION ALL SELECT date_local, 'MPL', '1800', orb_1800_outcome, orb_1800_r_multiple FROM daily_features_v2_mpl WHERE instrument = 'MPL'
UNION ALL SELECT date_local, 'MPL', '2300', orb_2300_outcome, orb_2300_r_multiple FROM daily_features_v2_mpl WHERE instrument = 'MPL'
UNION ALL SELECT date_local, 'MPL', '0030', orb_0030_outcome, orb_0030_r_multiple FROM daily_features_v2_mpl WHERE instrument = 'MPL'
'''

rows = con.execute(query).fetchall()
con.close()

# Aggregate by ORB
results = defaultdict(lambda: {"trades": 0, "wins": 0, "total_r": 0.0, "r_list": []})

for date_local, instrument, orb_time, outcome, r_multiple in rows:
    if outcome == "WIN" or outcome == "LOSS":
        results[orb_time]["trades"] += 1
        if outcome == "WIN":
            results[orb_time]["wins"] += 1
        if r_multiple is not None:
            results[orb_time]["total_r"] += r_multiple
            results[orb_time]["r_list"].append(r_multiple)

# Calculate stats
with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["orb_time", "trades", "wins", "losses", "win_rate", "avg_r", "total_r", "expectancy"])

    for orb_time in ["0900", "1000", "1100", "1800", "2300", "0030"]:
        data = results[orb_time]
        trades = data["trades"]
        wins = data["wins"]
        losses = trades - wins
        win_rate = (wins / trades * 100) if trades > 0 else 0
        avg_r = (data["total_r"] / trades) if trades > 0 else 0
        total_r = data["total_r"]

        # Expectancy = avg win size * win rate - avg loss size * loss rate
        # For RR=1.0: avg win = +1.0, avg loss = -1.0
        expectancy = (win_rate / 100) * 1.0 - ((100 - win_rate) / 100) * 1.0

        writer.writerow([orb_time, trades, wins, losses, f"{win_rate:.1f}", f"{avg_r:.3f}", f"{total_r:.1f}", f"{expectancy:.3f}"])

print(f"Baseline results saved to {OUTPUT_FILE}")

# Print summary
print("\nBASELINE RESULTS (RR=1.0, FULL SL):")
print("-" * 80)
for orb_time in ["0900", "1000", "1100", "1800", "2300", "0030"]:
    data = results[orb_time]
    trades = data["trades"]
    wins = data["wins"]
    win_rate = (wins / trades * 100) if trades > 0 else 0
    avg_r = (data["total_r"] / trades) if trades > 0 else 0
    print(f"{orb_time}: {trades:3d} trades, {win_rate:5.1f}% WR, {avg_r:+.3f}R avg")
