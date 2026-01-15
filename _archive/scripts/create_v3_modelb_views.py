"""
Create convenience views for Model B tables
"""

import duckdb

DB_PATH = "gold.db"

con = duckdb.connect(DB_PATH)

print("Creating convenience views for Model B tables...")
print()

# Full-SL view
print("Creating v_orb_trades_v3_modelb...")
con.execute("""
    DROP VIEW IF EXISTS v_orb_trades_v3_modelb
""")

con.execute("""
    CREATE VIEW v_orb_trades_v3_modelb AS
    SELECT date_local, 'MGC' as instrument, '0900' as orb_time,
           orb_0900_high as orb_high, orb_0900_low as orb_low, orb_0900_size as orb_size,
           orb_0900_break_dir as break_dir, orb_0900_outcome as outcome, orb_0900_r_multiple as r_multiple,
           orb_0900_entry_price as entry_price, orb_0900_stop_price as stop_price, orb_0900_target_price as target_price,
           orb_0900_risk_ticks as risk_ticks, orb_0900_reward_ticks as reward_ticks
    FROM daily_features_v3_modelb
    UNION ALL
    SELECT date_local, 'MGC' as instrument, '1000' as orb_time,
           orb_1000_high, orb_1000_low, orb_1000_size,
           orb_1000_break_dir, orb_1000_outcome, orb_1000_r_multiple,
           orb_1000_entry_price, orb_1000_stop_price, orb_1000_target_price,
           orb_1000_risk_ticks, orb_1000_reward_ticks
    FROM daily_features_v3_modelb
    UNION ALL
    SELECT date_local, 'MGC' as instrument, '1100' as orb_time,
           orb_1100_high, orb_1100_low, orb_1100_size,
           orb_1100_break_dir, orb_1100_outcome, orb_1100_r_multiple,
           orb_1100_entry_price, orb_1100_stop_price, orb_1100_target_price,
           orb_1100_risk_ticks, orb_1100_reward_ticks
    FROM daily_features_v3_modelb
    UNION ALL
    SELECT date_local, 'MGC' as instrument, '1800' as orb_time,
           orb_1800_high, orb_1800_low, orb_1800_size,
           orb_1800_break_dir, orb_1800_outcome, orb_1800_r_multiple,
           orb_1800_entry_price, orb_1800_stop_price, orb_1800_target_price,
           orb_1800_risk_ticks, orb_1800_reward_ticks
    FROM daily_features_v3_modelb
    UNION ALL
    SELECT date_local, 'MGC' as instrument, '2300' as orb_time,
           orb_2300_high, orb_2300_low, orb_2300_size,
           orb_2300_break_dir, orb_2300_outcome, orb_2300_r_multiple,
           orb_2300_entry_price, orb_2300_stop_price, orb_2300_target_price,
           orb_2300_risk_ticks, orb_2300_reward_ticks
    FROM daily_features_v3_modelb
    UNION ALL
    SELECT date_local, 'MGC' as instrument, '0030' as orb_time,
           orb_0030_high, orb_0030_low, orb_0030_size,
           orb_0030_break_dir, orb_0030_outcome, orb_0030_r_multiple,
           orb_0030_entry_price, orb_0030_stop_price, orb_0030_target_price,
           orb_0030_risk_ticks, orb_0030_reward_ticks
    FROM daily_features_v3_modelb
""")
print("  [OK] v_orb_trades_v3_modelb")

# Half-SL view
print("Creating v_orb_trades_v3_modelb_half...")
con.execute("""
    DROP VIEW IF EXISTS v_orb_trades_v3_modelb_half
""")

con.execute("""
    CREATE VIEW v_orb_trades_v3_modelb_half AS
    SELECT date_local, 'MGC' as instrument, '0900' as orb_time,
           orb_0900_high as orb_high, orb_0900_low as orb_low, orb_0900_size as orb_size,
           orb_0900_break_dir as break_dir, orb_0900_outcome as outcome, orb_0900_r_multiple as r_multiple,
           orb_0900_entry_price as entry_price, orb_0900_stop_price as stop_price, orb_0900_target_price as target_price,
           orb_0900_risk_ticks as risk_ticks, orb_0900_reward_ticks as reward_ticks
    FROM daily_features_v3_modelb_half
    UNION ALL
    SELECT date_local, 'MGC' as instrument, '1000' as orb_time,
           orb_1000_high, orb_1000_low, orb_1000_size,
           orb_1000_break_dir, orb_1000_outcome, orb_1000_r_multiple,
           orb_1000_entry_price, orb_1000_stop_price, orb_1000_target_price,
           orb_1000_risk_ticks, orb_1000_reward_ticks
    FROM daily_features_v3_modelb_half
    UNION ALL
    SELECT date_local, 'MGC' as instrument, '1100' as orb_time,
           orb_1100_high, orb_1100_low, orb_1100_size,
           orb_1100_break_dir, orb_1100_outcome, orb_1100_r_multiple,
           orb_1100_entry_price, orb_1100_stop_price, orb_1100_target_price,
           orb_1100_risk_ticks, orb_1100_reward_ticks
    FROM daily_features_v3_modelb_half
    UNION ALL
    SELECT date_local, 'MGC' as instrument, '1800' as orb_time,
           orb_1800_high, orb_1800_low, orb_1800_size,
           orb_1800_break_dir, orb_1800_outcome, orb_1800_r_multiple,
           orb_1800_entry_price, orb_1800_stop_price, orb_1800_target_price,
           orb_1800_risk_ticks, orb_1800_reward_ticks
    FROM daily_features_v3_modelb_half
    UNION ALL
    SELECT date_local, 'MGC' as instrument, '2300' as orb_time,
           orb_2300_high, orb_2300_low, orb_2300_size,
           orb_2300_break_dir, orb_2300_outcome, orb_2300_r_multiple,
           orb_2300_entry_price, orb_2300_stop_price, orb_2300_target_price,
           orb_2300_risk_ticks, orb_2300_reward_ticks
    FROM daily_features_v3_modelb_half
    UNION ALL
    SELECT date_local, 'MGC' as instrument, '0030' as orb_time,
           orb_0030_high, orb_0030_low, orb_0030_size,
           orb_0030_break_dir, orb_0030_outcome, orb_0030_r_multiple,
           orb_0030_entry_price, orb_0030_stop_price, orb_0030_target_price,
           orb_0030_risk_ticks, orb_0030_reward_ticks
    FROM daily_features_v3_modelb_half
""")
print("  [OK] v_orb_trades_v3_modelb_half")

con.close()
print()
print("Views created successfully!")
