"""
Create v_orb_trades_half view - unpivoted view of all ORB trades from daily_features_v2_half
"""

import duckdb

con = duckdb.connect("gold.db")

# Drop existing view if it exists
con.execute("DROP VIEW IF EXISTS v_orb_trades_half")

# Create unpivoted view
con.execute("""
    CREATE VIEW v_orb_trades_half AS
    SELECT date_local, 'MGC' as instrument, '0900' as orb_time,
           orb_0900_high as orb_high, orb_0900_low as orb_low, orb_0900_size as orb_size,
           orb_0900_break_dir as break_dir, orb_0900_outcome as outcome,
           orb_0900_r_multiple as r_multiple,
           orb_0900_mae as mae, orb_0900_mfe as mfe,
           orb_0900_stop_price as stop_price, orb_0900_risk_ticks as risk_ticks
    FROM daily_features_v2_half
    UNION ALL
    SELECT date_local, 'MGC', '1000',
           orb_1000_high, orb_1000_low, orb_1000_size,
           orb_1000_break_dir, orb_1000_outcome, orb_1000_r_multiple,
           orb_1000_mae, orb_1000_mfe,
           orb_1000_stop_price, orb_1000_risk_ticks
    FROM daily_features_v2_half
    UNION ALL
    SELECT date_local, 'MGC', '1100',
           orb_1100_high, orb_1100_low, orb_1100_size,
           orb_1100_break_dir, orb_1100_outcome, orb_1100_r_multiple,
           orb_1100_mae, orb_1100_mfe,
           orb_1100_stop_price, orb_1100_risk_ticks
    FROM daily_features_v2_half
    UNION ALL
    SELECT date_local, 'MGC', '1800',
           orb_1800_high, orb_1800_low, orb_1800_size,
           orb_1800_break_dir, orb_1800_outcome, orb_1800_r_multiple,
           orb_1800_mae, orb_1800_mfe,
           orb_1800_stop_price, orb_1800_risk_ticks
    FROM daily_features_v2_half
    UNION ALL
    SELECT date_local, 'MGC', '2300',
           orb_2300_high, orb_2300_low, orb_2300_size,
           orb_2300_break_dir, orb_2300_outcome, orb_2300_r_multiple,
           orb_2300_mae, orb_2300_mfe,
           orb_2300_stop_price, orb_2300_risk_ticks
    FROM daily_features_v2_half
    UNION ALL
    SELECT date_local, 'MGC', '0030',
           orb_0030_high, orb_0030_low, orb_0030_size,
           orb_0030_break_dir, orb_0030_outcome, orb_0030_r_multiple,
           orb_0030_mae, orb_0030_mfe,
           orb_0030_stop_price, orb_0030_risk_ticks
    FROM daily_features_v2_half
""")

con.commit()
con.close()

print("View v_orb_trades_half created successfully")
