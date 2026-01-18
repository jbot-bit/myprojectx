"""
Check what data exists in MotherDuck projectx_prod database
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import duckdb

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

MOTHERDUCK_TOKEN = os.getenv('MOTHERDUCK_TOKEN')

if not MOTHERDUCK_TOKEN:
    print("[ERROR] MOTHERDUCK_TOKEN not found in .env file")
    sys.exit(1)

def check_motherduck_data():
    """Check existing data in MotherDuck"""
    conn_str = f"md:projectx_prod?motherduck_token={MOTHERDUCK_TOKEN}"

    print("\n" + "="*60)
    print("CHECKING MOTHERDUCK DATABASE: projectx_prod")
    print("="*60 + "\n")

    try:
        conn = duckdb.connect(conn_str)

        # Get list of tables
        print("1. Listing tables...")
        tables = conn.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
        """).fetchall()

        if not tables:
            print("   [INFO] Database is EMPTY - no tables found")
            print("\n" + "="*60)
            print("RECOMMENDATION: Run migration to populate database")
            print("="*60)
            conn.close()
            return

        print(f"   Found {len(tables)} table(s):")
        for table in tables:
            print(f"      - {table[0]}")

        print("\n2. Checking row counts...")

        # Expected tables
        expected_tables = ['bars_1m', 'bars_5m', 'daily_features', 'validated_setups']

        results = {}
        for table_name in expected_tables:
            if (table_name,) in tables:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    results[table_name] = count
                    print(f"   {table_name:20s}: {count:,} rows")

                    # Show instruments if bars table
                    if 'bars' in table_name:
                        instruments = conn.execute(f"""
                            SELECT symbol, COUNT(*) as cnt
                            FROM {table_name}
                            GROUP BY symbol
                            ORDER BY symbol
                        """).fetchall()
                        for symbol, cnt in instruments:
                            print(f"      └─ {symbol}: {cnt:,} rows")
                except Exception as e:
                    print(f"   {table_name:20s}: ERROR - {e}")
            else:
                print(f"   {table_name:20s}: MISSING")

        # Compare with local gold.db
        print("\n3. Comparing with local gold.db...")
        local_db = Path(__file__).parent.parent / 'gold.db'
        if local_db.exists():
            local_conn = duckdb.connect(str(local_db), read_only=True)

            print("\n   Local gold.db:")
            for table_name in expected_tables:
                try:
                    count = local_conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    cloud_count = results.get(table_name, 0)
                    diff = count - cloud_count
                    status = "✅ MATCH" if diff == 0 else f"⚠️  DIFF: {diff:+,}"
                    print(f"   {table_name:20s}: {count:,} rows | {status}")
                except:
                    print(f"   {table_name:20s}: TABLE NOT FOUND")

            local_conn.close()

        # Recommendation
        print("\n" + "="*60)
        print("RECOMMENDATION:")
        print("="*60)

        all_match = all(
            results.get(t, 0) > 0 for t in expected_tables
        )

        if all_match:
            print("✅ MotherDuck database looks complete!")
            print("   You can set CLOUD_MODE=1 in .env to use it")
            print("\n   To verify data integrity, run:")
            print("   python audit_master.py")
        else:
            print("⚠️  MotherDuck database is incomplete or outdated")
            print("   Options:")
            print("   1. Drop and recreate: python scripts/test_motherduck_connection.py")
            print("      (Say 'yes' when prompted)")
            print("   2. Run migration: python scripts/migrate_to_motherduck.py")
            print("      (This will sync data from local to cloud)")

        print("="*60)

        conn.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_motherduck_data()
