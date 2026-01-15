"""
Add stop_price and risk_ticks columns to daily_features_v2
"""
import duckdb

con = duckdb.connect("gold.db")

orbs = ["0900", "1000", "1100", "1800", "2300", "0030"]

for orb in orbs:
    stop_col = f"orb_{orb}_stop_price"
    risk_col = f"orb_{orb}_risk_ticks"

    # Add stop_price column
    try:
        con.execute(f"ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS {stop_col} DOUBLE")
        print(f"Added {stop_col}")
    except Exception as e:
        print(f"Error adding {stop_col}: {e}")

    # Add risk_ticks column
    try:
        con.execute(f"ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS {risk_col} DOUBLE")
        print(f"Added {risk_col}")
    except Exception as e:
        print(f"Error adding {risk_col}: {e}")

con.commit()
con.close()
print("\nDone!")
