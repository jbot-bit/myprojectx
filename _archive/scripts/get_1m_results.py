import duckdb
import pandas as pd

con = duckdb.connect('gold.db', read_only=True)
optimal = pd.read_csv('worst_case_parameters.csv', dtype={'orb': str})

results = []
for _, row in optimal.iterrows():
    r = con.execute("""
        SELECT orb, rr, COUNT(*) as trades,
               AVG(r_multiple) as avg_r,
               SUM(r_multiple) as total_r,
               SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as wr
        FROM orb_trades_1m_exec_nofilters
        WHERE close_confirmations = 1
          AND orb = ?
          AND rr = ?
        GROUP BY orb, rr
    """, [row['orb'], row['optimal_rr']]).fetchone()

    if r:
        results.append({
            'orb': r[0],
            'rr': r[1],
            'trades': r[2],
            'avg_r': r[3],
            'total_r': r[4],
            'wr': r[5]
        })

df = pd.DataFrame(results)
print(df.to_string(index=False))
print(f"\n\nSYSTEM TOTALS:")
print(f"Total trades: {df['trades'].sum()}")
print(f"System-wide avg R: {df['avg_r'].mean():.4f}")
print(f"Weighted avg R: {(df['avg_r'] * df['trades']).sum() / df['trades'].sum():.4f}")
print(f"Total R: {df['total_r'].sum():.1f}R")

con.close()
