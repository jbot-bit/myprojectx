"""Compare schema between local and cloud"""
import os
from pathlib import Path
from dotenv import load_dotenv
import duckdb

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

MOTHERDUCK_TOKEN = os.getenv('MOTHERDUCK_TOKEN')

print("\n=== CLOUD SCHEMA (MotherDuck) ===\n")
cloud_conn = duckdb.connect(f"md:projectx_prod?motherduck_token={MOTHERDUCK_TOKEN}")
cloud_schema = cloud_conn.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'daily_features_v2'
    AND column_name IN ('atr_20', 'orb_1000_high', 'orb_1000_low')
    ORDER BY column_name
""").fetchall()
for col, dtype in cloud_schema:
    print(f"  {col:20s}: {dtype}")
cloud_conn.close()

print("\n=== LOCAL SCHEMA (gold.db) ===\n")
local_conn = duckdb.connect('gold.db', read_only=True)
local_schema = local_conn.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'daily_features_v2'
    AND column_name IN ('atr_20', 'orb_1000_high', 'orb_1000_low')
    ORDER BY column_name
""").fetchall()
for col, dtype in local_schema:
    print(f"  {col:20s}: {dtype}")
local_conn.close()

print("\n=== ISSUE ===")
print("If columns show as VARCHAR in cloud but DOUBLE in local,")
print("we need to recreate the MotherDuck database with correct types.")
