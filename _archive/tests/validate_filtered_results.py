"""
Phase 1: Validate Filtered Results

Confirms the 263K trades in orb_trades_5m_exec are trustworthy before proceeding.

Checks:
1. Filters working correctly (MAX_STOP ≤ 100, ASIA_TP_CAP ≤ 150)
2. No duplicate primary keys (data integrity)
3. Correct outcome labels (WIN/LOSS/NO_TRADE, not OPEN)
"""

import duckdb

DB_PATH = "gold.db"

def validate():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*80)
    print("PHASE 1: VALIDATE FILTERED RESULTS")
    print("="*80)
    print()

    # Check 1: Filters working correctly
    print("CHECK 1: Filter Enforcement")
    print("-"*80)

    result = con.execute("""
        SELECT
            MAX(stop_ticks) as max_stop,
            MAX(CASE WHEN orb IN ('0900','1000','1100')
                     THEN ABS(target_price - entry_price) / 0.1
                     END) as max_asia_tp,
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as total_trades
        FROM orb_trades_5m_exec
        WHERE outcome IN ('WIN','LOSS')
    """).fetchone()

    max_stop, max_asia_tp, total_trades = result

    print(f"Total trades: {total_trades}")
    print(f"Max stop: {max_stop:.1f} ticks (should be <=100)")
    print(f"Max Asia TP: {max_asia_tp:.1f} ticks (should be <=150)")

    if max_stop <= 100:
        print("[PASS] MAX_STOP filter working correctly")
    else:
        print(f"[FAIL] FAILED: MAX_STOP filter not working (found {max_stop:.1f} > 100)")

    if max_asia_tp <= 150:
        print("[PASS] ASIA_TP_CAP filter working correctly")
    else:
        print(f"[FAIL] FAILED: ASIA_TP_CAP filter not working (found {max_asia_tp:.1f} > 150)")

    print()

    # Check 2: No duplicate primary keys
    print("CHECK 2: Data Integrity (No Duplicates)")
    print("-"*80)

    dupes = con.execute("""
        SELECT COUNT(*) FROM (
            SELECT date_local, orb, close_confirmations, rr, sl_mode, buffer_ticks, COUNT(*)
            FROM orb_trades_5m_exec
            GROUP BY date_local, orb, close_confirmations, rr, sl_mode, buffer_ticks
            HAVING COUNT(*) > 1
        )
    """).fetchone()[0]

    print(f"Duplicate primary keys: {dupes} (should be 0)")

    if dupes == 0:
        print("[PASS] No duplicate keys found - data integrity confirmed")
    else:
        print(f"[FAIL] FAILED: Found {dupes} duplicate keys")

    print()

    # Check 3: Outcome distribution
    print("CHECK 3: Correct Outcome Labels")
    print("-"*80)

    outcomes = con.execute("""
        SELECT outcome, COUNT(*) as count
        FROM orb_trades_5m_exec
        GROUP BY outcome
        ORDER BY count DESC
    """).fetchdf()

    print(outcomes.to_string(index=False))
    print()

    has_open = 'OPEN' in outcomes['outcome'].values
    has_correct = all(o in ['WIN', 'LOSS', 'NO_TRADE'] for o in outcomes['outcome'].values)

    if has_correct and not has_open:
        print("[PASS] Correct outcome labels (WIN/LOSS/NO_TRADE)")
    else:
        print("[FAIL] FAILED: Found incorrect outcome labels")
        if has_open:
            print("  ERROR: Found 'OPEN' label (should be 'NO_TRADE')")

    print()

    # Summary
    print("="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    all_passed = (max_stop <= 100 and max_asia_tp <= 150 and dupes == 0 and has_correct and not has_open)

    if all_passed:
        print("[PASS] ALL CHECKS PASSED")
        print()
        print("Your filtered results are TRUSTWORTHY.")
        print("Ready to proceed to Phase 2: Rebuild no-filter test with correct logic")
    else:
        print("[FAIL] VALIDATION FAILED")
        print()
        print("Issues found - need to investigate filtered backtest before proceeding")

    print()
    print("="*80)

    con.close()

if __name__ == "__main__":
    validate()
