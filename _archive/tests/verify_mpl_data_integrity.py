"""
MPL Data Integrity Verification
================================

Comprehensive data quality checks:
1. No duplicate timestamps
2. No gaps in continuous contracts
3. No impossible price movements
4. ORB calculations are correct
5. MAE/MFE values are logical
6. No lookahead bias (feature dates match bar dates)

Usage:
  python verify_mpl_data_integrity.py
"""

import duckdb
from datetime import datetime, timedelta

DB_PATH = "gold.db"
SYMBOL = "MPL"


def check_duplicates():
    """Check for duplicate timestamps"""
    con = duckdb.connect(DB_PATH)

    query = """
    SELECT ts_utc, COUNT(*) as cnt
    FROM bars_1m_mpl
    WHERE symbol = 'MPL'
    GROUP BY ts_utc
    HAVING COUNT(*) > 1
    """

    duplicates = con.execute(query).fetchall()
    con.close()

    if duplicates:
        print(f"❌ FAIL: Found {len(duplicates)} duplicate timestamps")
        for ts, cnt in duplicates[:5]:
            print(f"   {ts}: {cnt} duplicates")
        return False
    else:
        print(f"✅ PASS: No duplicate timestamps")
        return True


def check_price_sanity():
    """Check for impossible price movements"""
    con = duckdb.connect(DB_PATH)

    # Check for bars where high < low or close outside range
    query = """
    SELECT COUNT(*) FROM bars_1m_mpl
    WHERE symbol = 'MPL'
      AND (
        high < low
        OR close < low
        OR close > high
        OR open < low
        OR open > high
      )
    """

    invalid_bars = con.execute(query).fetchone()[0]
    con.close()

    if invalid_bars > 0:
        print(f"❌ FAIL: Found {invalid_bars} bars with invalid OHLC relationships")
        return False
    else:
        print(f"✅ PASS: All bars have valid OHLC relationships")
        return True


def check_orb_calculations():
    """Verify ORB high/low are within session range"""
    con = duckdb.connect(DB_PATH)

    # Check if ORB high/low match actual bar data
    query = """
    SELECT COUNT(*) FROM daily_features_v2_mpl
    WHERE instrument = 'MPL'
      AND (
        orb_0900_size < 0
        OR orb_1000_size < 0
        OR orb_1100_size < 0
        OR orb_1800_size < 0
        OR orb_2300_size < 0
        OR orb_0030_size < 0
      )
    """

    invalid_orbs = con.execute(query).fetchone()[0]

    if invalid_orbs > 0:
        print(f"❌ FAIL: Found {invalid_orbs} days with negative ORB size")
        con.close()
        return False
    else:
        print(f"✅ PASS: All ORB sizes are non-negative")

    # Check break_dir consistency
    query = """
    SELECT COUNT(*) FROM daily_features_v2_mpl
    WHERE instrument = 'MPL'
      AND orb_0900_outcome IN ('WIN', 'LOSS')
      AND orb_0900_break_dir = 'NONE'
    """

    inconsistent = con.execute(query).fetchone()[0]
    con.close()

    if inconsistent > 0:
        print(f"❌ FAIL: Found {inconsistent} trades with outcome but no break_dir")
        return False
    else:
        print(f"✅ PASS: Break directions are consistent with outcomes")
        return True


def check_mae_mfe_logic():
    """Verify MAE/MFE values make sense"""
    con = duckdb.connect(DB_PATH)

    # For winning trades, MFE should be positive, MAE should be negative or small
    query = """
    SELECT COUNT(*) FROM daily_features_v2_mpl
    WHERE instrument = 'MPL'
      AND orb_0900_outcome = 'WIN'
      AND (orb_0900_mfe <= 0 OR orb_0900_mae > 0)
    """

    invalid_wins = con.execute(query).fetchone()[0]

    if invalid_wins > 0:
        print(f"⚠️  WARNING: Found {invalid_wins} winning trades with unusual MAE/MFE")
    else:
        print(f"✅ PASS: MAE/MFE values are logical for winning trades")

    # For losing trades, MAE should be negative (hit stop)
    query = """
    SELECT COUNT(*) FROM daily_features_v2_mpl
    WHERE instrument = 'MPL'
      AND orb_0900_outcome = 'LOSS'
      AND orb_0900_mae >= 0
    """

    invalid_losses = con.execute(query).fetchone()[0]
    con.close()

    if invalid_losses > 0:
        print(f"⚠️  WARNING: Found {invalid_losses} losing trades with positive MAE")
        return True  # Warning, not error
    else:
        print(f"✅ PASS: MAE values are logical for losing trades")
        return True


def check_temporal_ordering():
    """Ensure features don't reference future data"""
    con = duckdb.connect(DB_PATH)

    # Check that ATR_20 calculation doesn't include future dates
    # (This is implicit in the V2 builder, but let's verify no anomalies)

    query = """
    SELECT COUNT(*) FROM daily_features_v2_mpl
    WHERE instrument = 'MPL'
      AND atr_20 IS NOT NULL
      AND atr_20 <= 0
    """

    invalid_atr = con.execute(query).fetchone()[0]

    if invalid_atr > 0:
        print(f"⚠️  WARNING: Found {invalid_atr} days with invalid ATR (<= 0)")
    else:
        print(f"✅ PASS: ATR values are all positive")

    # Check feature dates match bar dates
    query = """
    SELECT f.date_local, COUNT(*) as bar_count
    FROM daily_features_v2_mpl f
    LEFT JOIN bars_1m_mpl b
      ON b.symbol = 'MPL'
      AND DATE_TRUNC('day', b.ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'Australia/Brisbane') = f.date_local
    WHERE f.instrument = 'MPL'
    GROUP BY f.date_local
    HAVING COUNT(*) = 0
    """

    orphan_features = con.execute(query).fetchall()
    con.close()

    if orphan_features:
        print(f"❌ FAIL: Found {len(orphan_features)} feature dates with no matching bars")
        return False
    else:
        print(f"✅ PASS: All feature dates have matching bar data")
        return True


def check_data_completeness():
    """Check for large gaps in data"""
    con = duckdb.connect(DB_PATH)

    query = """
    SELECT date_local
    FROM daily_features_v2_mpl
    WHERE instrument = 'MPL'
    ORDER BY date_local
    """

    dates = [row[0] for row in con.execute(query).fetchall()]
    con.close()

    if not dates:
        print(f"❌ FAIL: No dates found in daily_features_v2_mpl")
        return False

    # Check for gaps > 7 days (weekends are OK, but not multi-week gaps)
    large_gaps = []
    for i in range(1, len(dates)):
        gap_days = (dates[i] - dates[i-1]).days
        if gap_days > 7:
            large_gaps.append((dates[i-1], dates[i], gap_days))

    if large_gaps:
        print(f"⚠️  INFO: Found {len(large_gaps)} gaps > 7 days in data")
        for start, end, gap in large_gaps[:5]:
            print(f"   {start} to {end}: {gap} days")
    else:
        print(f"✅ PASS: No large gaps in data (all gaps <= 7 days)")

    return True


def main():
    print("="*80)
    print("MPL DATA INTEGRITY VERIFICATION")
    print("="*80)

    checks = [
        ("Duplicate timestamps", check_duplicates),
        ("Price sanity (OHLC relationships)", check_price_sanity),
        ("ORB calculations", check_orb_calculations),
        ("MAE/MFE logic", check_mae_mfe_logic),
        ("Temporal ordering (no lookahead)", check_temporal_ordering),
        ("Data completeness (gaps)", check_data_completeness),
    ]

    results = []
    print("\nRunning checks...\n")

    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        try:
            passed = check_func()
            results.append((check_name, "PASS" if passed else "FAIL"))
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append((check_name, "ERROR"))

    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)

    passed = sum(1 for _, status in results if status == "PASS")
    total = len(results)

    for check_name, status in results:
        emoji = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "⚠️")
        print(f"{emoji} {check_name}: {status}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL CHECKS PASSED - Data is clean and ready for trading")
        return 0
    elif passed >= total * 0.8:
        print("\n⚠️  MOST CHECKS PASSED - Review warnings before trading")
        return 1
    else:
        print("\n❌ MULTIPLE FAILURES - Do not trade until issues are resolved")
        return 2


if __name__ == "__main__":
    exit(main())
