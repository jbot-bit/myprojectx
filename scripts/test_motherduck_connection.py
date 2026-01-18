#!/usr/bin/env python3
"""
Test MotherDuck connection and create prod database.
"""

import os
import sys
import duckdb
from dotenv import load_dotenv

load_dotenv()


def test_motherduck_connection():
    """Test connection to MotherDuck and create prod database."""

    # Get token
    token = os.getenv('MOTHERDUCK_TOKEN')

    if not token:
        print("ERROR: MOTHERDUCK_TOKEN not found in environment!")
        print("\nTo get your MotherDuck token:")
        print("1. Go to https://motherduck.com/")
        print("2. Sign up or log in")
        print("3. Go to Settings > Access Tokens")
        print("4. Create a new token")
        print("5. Add to your .env file:")
        print("   MOTHERDUCK_TOKEN=your_token_here")
        return False

    print("=" * 70)
    print("TESTING MOTHERDUCK CONNECTION")
    print("=" * 70)

    try:
        # Test connection
        print("\n1. Connecting to MotherDuck...")
        conn = duckdb.connect(f'md:?motherduck_token={token}')
        print("   [OK] Connected successfully!")

        # Check version
        version = conn.execute("SELECT version()").fetchone()[0]
        print(f"   [OK] DuckDB version: {version}")

        # List existing databases
        print("\n2. Listing existing databases...")
        dbs = conn.execute("SHOW DATABASES").fetchall()
        print(f"   Found {len(dbs)} database(s):")
        for db in dbs:
            print(f"      - {db[0]}")

        # Check if projectx_prod exists
        db_names = [db[0] for db in dbs]

        if 'projectx_prod' in db_names:
            print("\n   [WARN] Database 'projectx_prod' already exists")
            response = input("   Do you want to drop and recreate it? (yes/no): ")
            if response.lower() == 'yes':
                print("   Dropping existing database...")
                conn.execute("DROP DATABASE IF EXISTS projectx_prod")
                print("   [OK] Dropped")
            else:
                print("   [OK] Will use existing database")

        # Create or use projectx_prod
        print("\n3. Creating/using database 'projectx_prod'...")
        conn.execute("CREATE DATABASE IF NOT EXISTS projectx_prod")
        conn.execute("USE projectx_prod")
        print("   [OK] Database ready!")

        # Test write access
        print("\n4. Testing write access...")
        conn.execute("CREATE TABLE IF NOT EXISTS _test (id INTEGER, ts TIMESTAMP)")
        conn.execute("INSERT INTO _test VALUES (1, CURRENT_TIMESTAMP)")
        result = conn.execute("SELECT COUNT(*) FROM _test").fetchone()[0]
        conn.execute("DROP TABLE _test")
        print(f"   [OK] Write test passed (inserted {result} row)")

        # Show connection string
        print("\n5. Connection string for scripts:")
        print(f"   md:projectx_prod?motherduck_token={token[:20]}...")

        conn.close()

        print("\n" + "=" * 70)
        print("SUCCESS: MotherDuck connection working!")
        print("Database 'projectx_prod' is ready for migration.")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your token is valid")
        print("2. Ensure you have internet connection")
        print("3. Verify MotherDuck service status")
        return False


if __name__ == "__main__":
    success = test_motherduck_connection()
    sys.exit(0 if success else 1)
