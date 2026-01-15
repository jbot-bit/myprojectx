"""Quick check for current 0030 ORB setup"""
import duckdb
from datetime import datetime

con = duckdb.connect('gold.db')

# Get latest 3 days
result = con.execute("""
    SELECT
        date_local,
        orb_2300_high, orb_2300_low, orb_2300_size,
        orb_0030_high, orb_0030_low, orb_0030_size, orb_0030_break_dir,
        asia_high, asia_low,
        london_high, london_low
    FROM daily_features
    WHERE instrument = 'MGC'
    ORDER BY date_local DESC
    LIMIT 3
""").fetchall()

print('='*80)
print('LATEST MGC DATA IN DATABASE')
print('='*80)

for row in result:
    print(f"\nDate: {row[0]}")
    print(f"  2300 ORB: {row[1]:.2f} / {row[2]:.2f} (Size: {row[3]:.2f})")
    print(f"  0030 ORB: {row[4]:.2f} / {row[5]:.2f} (Size: {row[6]:.2f}) Break: {row[7]}")
    print(f"  Asia:   {row[8]:.2f} - {row[9]:.2f} (Range: {row[8]-row[9]:.2f})")
    print(f"  London: {row[10]:.2f} - {row[11]:.2f} (Range: {row[10]-row[11]:.2f})")

if result:
    print(f"\n{'='*80}")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data gap: {(datetime.now().date() - result[0][0]).days} days old")
    print(f"{'='*80}")

    if (datetime.now().date() - result[0][0]).days > 0:
        print("\n⚠️  WARNING: Data is not current!")
        print("   For tonight's trading, use: python app_trading_hub.py")
        print("   Or wait for Databento to update (usually 1-2 day delay)")

# Check 0030 ORB performance
print(f"\n{'='*80}")
print("0030 ORB PERFORMANCE (Database Stats)")
print('='*80)

perf = con.execute("""
    SELECT
        COUNT(*) as total_days,
        COUNT(*) FILTER (WHERE outcome IN ('WIN', 'LOSS')) as trades,
        ROUND(100.0 * COUNT(*) FILTER (WHERE outcome IN ('WIN', 'LOSS')) / COUNT(*), 1) as breakout_freq,
        ROUND(100.0 * COUNT(*) FILTER (WHERE outcome = 'WIN') /
              COUNT(*) FILTER (WHERE outcome IN ('WIN', 'LOSS')), 1) as win_rate,
        ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple END), 3) as avg_r,
        ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple END), 1) as total_r
    FROM v_orb_trades_half
    WHERE orb_time = '0030' AND instrument = 'MGC'
""").fetchone()

print(f"Total Days: {perf[0]}")
print(f"Trades (breakouts): {perf[1]} ({perf[2]}% of days)")
print(f"Win Rate: {perf[3]}%")
print(f"Avg R: {perf[4]:+.3f}R per trade")
print(f"Total R: {perf[5]:+.1f}R")
print(f"Annual: ~{perf[5] / 2:.0f}R/year (2 years data)")

# Size filter check
print(f"\n{'='*80}")
print("SIZE FILTER STATUS")
print('='*80)
print("0030 ORB: Skip if size > 0.112 × ATR(20)")
print("Status: IMPLEMENTED in trading_app/strategy_engine.py")
print("Note: Database trades do NOT have filter applied (baseline)")

con.close()
