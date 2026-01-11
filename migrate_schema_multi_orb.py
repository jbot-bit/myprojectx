"""
Schema migration: Add all 6 ORB column sets to daily_features
Run this ONCE to migrate your existing database.
"""

import duckdb
from pathlib import Path

DB_PATH = Path("gold.db")

def main():
    con = duckdb.connect(str(DB_PATH))

    print("Current schema:")
    current = con.execute("DESCRIBE daily_features").fetchall()
    for row in current:
        print(f"  {row[0]}: {row[1]}")

    print("\nAdding instrument column if missing...")
    try:
        con.execute("ALTER TABLE daily_features ADD COLUMN instrument TEXT")
        print("  [OK] Added instrument column")
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            print("  [OK] instrument column already exists")
        else:
            raise

    print("\nAdding asia_range if missing...")
    try:
        con.execute("ALTER TABLE daily_features ADD COLUMN asia_range DOUBLE")
        print("  [OK] Added asia_range column")
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            print("  [OK] asia_range column already exists")
        else:
            raise

    # Rename existing orb_* columns to orb_0030_* (since current code computes 00:30 ORB)
    print("\nRenaming existing ORB columns to orb_0030_* ...")
    renames = [
        ("orb_high", "orb_0030_high"),
        ("orb_low", "orb_0030_low"),
        ("orb_first5m", "orb_0030_size"),
        ("orb_break_dir", "orb_0030_break_dir"),
    ]

    for old_name, new_name in renames:
        try:
            con.execute(f"ALTER TABLE daily_features RENAME COLUMN {old_name} TO {new_name}")
            print(f"  [OK] Renamed {old_name} -> {new_name}")
        except Exception as e:
            err_msg = str(e).lower()
            if "does not have a column" in err_msg or "does not exist" in err_msg:
                print(f"  [SKIP] {old_name} doesn't exist (already renamed or doesn't exist)")
            elif "already exists" in err_msg or "duplicate" in err_msg:
                print(f"  [OK] {new_name} already exists")
            else:
                print(f"  [ERROR] {e}")
                # Continue anyway
                pass

    # Add all 6 ORB column sets
    print("\nAdding all ORB column sets...")
    orb_times = ["0900", "1000", "1100", "1800", "2300", "0030"]

    for orb_time in orb_times:
        print(f"  Adding ORB {orb_time} columns...")
        columns = [
            (f"orb_{orb_time}_high", "DOUBLE"),
            (f"orb_{orb_time}_low", "DOUBLE"),
            (f"orb_{orb_time}_size", "DOUBLE"),
            (f"orb_{orb_time}_break_dir", "TEXT"),
        ]

        for col_name, col_type in columns:
            try:
                con.execute(f"ALTER TABLE daily_features ADD COLUMN {col_name} {col_type}")
                print(f"    [OK] Added {col_name}")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"    [OK] {col_name} already exists")
                else:
                    raise

    # Update default instrument value for existing rows
    print("\nSetting instrument='MGC' for existing rows...")
    result = con.execute("UPDATE daily_features SET instrument = 'MGC' WHERE instrument IS NULL").fetchall()
    print(f"  [OK] Updated rows")

    # Recreate PK with (date_local, instrument)
    print("\nRecreating primary key as (date_local, instrument)...")
    try:
        # DuckDB doesn't support ALTER TABLE for PK changes, need to recreate table
        # But since we want to preserve data, we'll just add a unique constraint
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_features_pk ON daily_features(date_local, instrument)")
        print("  [OK] Added unique index on (date_local, instrument)")
    except Exception as e:
        print(f"  [WARN] {e}")

    print("\nNew schema:")
    new_schema = con.execute("DESCRIBE daily_features").fetchall()
    for row in new_schema:
        print(f"  {row[0]}: {row[1]}")

    con.close()
    print("\n[SUCCESS] Migration complete!")
    print("\nNext steps:")
    print("1. Run: python build_daily_features.py <some-date> to test new logic")
    print("2. Wipe and rebuild all features: python wipe_mgc.py && python backfill_databento_continuous.py <start> <end>")

if __name__ == "__main__":
    main()
