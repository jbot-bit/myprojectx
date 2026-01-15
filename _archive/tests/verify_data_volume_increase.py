"""
Verify that the 110 extra session_labels rows produce actual NY 0030 trades.
"""
import duckdb

conn = duckdb.connect('gold.db')

print("="*80)
print("DATA VOLUME INCREASE VERIFICATION")
print("="*80)

# How many NY 0030 trades exist?
total_trades = conn.execute("""
    SELECT COUNT(*)
    FROM orb_trades_5m_exec
    WHERE orb = '0030'
    AND direction IS NOT NULL
    AND r_multiple IS NOT NULL
""").fetchone()[0]

# How many can join to session_labels?
joined_trades = conn.execute("""
    SELECT COUNT(*)
    FROM orb_trades_5m_exec t
    INNER JOIN session_labels sl ON t.date_local = sl.date_local
    WHERE t.orb = '0030'
    AND t.direction IS NOT NULL
    AND t.r_multiple IS NOT NULL
""").fetchone()[0]

print(f"\nTotal NY 0030 trades: {total_trades:,}")
print(f"Trades with labels: {joined_trades:,}")
print(f"Missing labels: {total_trades - joined_trades:,}")

# Check neutral samples specifically
neutral_trades = conn.execute("""
    SELECT COUNT(*)
    FROM orb_trades_5m_exec t
    INNER JOIN session_labels sl ON t.date_local = sl.date_local
    WHERE t.orb = '0030'
    AND t.direction IS NOT NULL
    AND t.r_multiple IS NOT NULL
    AND sl.ny_net_direction = 'neutral'
""").fetchone()[0]

print(f"\nTrades with ny_net_direction=neutral: {neutral_trades:,}")

# Compare to old filter (london_high IS NOT NULL)
old_filter_trades = conn.execute("""
    SELECT COUNT(*)
    FROM orb_trades_5m_exec t
    INNER JOIN session_labels sl ON t.date_local = sl.date_local
    INNER JOIN daily_features df ON t.date_local = df.date_local
    WHERE t.orb = '0030'
    AND t.direction IS NOT NULL
    AND t.r_multiple IS NOT NULL
    AND df.london_high IS NOT NULL
    AND sl.ny_net_direction = 'neutral'
""").fetchone()[0]

print(f"\nWith old London filter (london_high IS NOT NULL):")
print(f"  Neutral trades: {old_filter_trades:,}")
print(f"\nNew neutral trades from removed filter: {neutral_trades - old_filter_trades:,}")

# Sample 5 of the new neutral days
print("\n" + "="*80)
print("SAMPLE 5 NEW NEUTRAL DAYS (missing London data)")
print("="*80)

sample = conn.execute("""
    SELECT
        sl.date_local,
        COUNT(t.direction) as num_trades,
        AVG(t.r_multiple) as avg_r,
        df.london_high,
        df.asia_high,
        sl.ny_net_direction
    FROM session_labels sl
    LEFT JOIN orb_trades_5m_exec t ON sl.date_local = t.date_local AND t.orb = '0030'
    LEFT JOIN daily_features df ON sl.date_local = df.date_local
    WHERE sl.ny_net_direction = 'neutral'
    AND df.london_high IS NULL
    GROUP BY sl.date_local, df.london_high, df.asia_high, sl.ny_net_direction
    ORDER BY RANDOM()
    LIMIT 5
""").fetchdf()

print(sample.to_string(index=False))

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)

conn.close()
