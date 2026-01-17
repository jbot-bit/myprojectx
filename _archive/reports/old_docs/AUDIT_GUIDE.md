# Complete Data Accuracy & Calculation Audit Guide

## What This Audit Does

This comprehensive audit script validates **every calculation and data point** in your trading system:

### 10 Audit Categories

1. **Database Schema & Integrity**
   - Verifies all required tables exist (bars_1m, bars_5m, daily_features, validated_setups)
   - Checks all required columns are present
   - Validates data types and constraints

2. **Config vs Database Synchronization**
   - Compares `trading_app/config.py` filters with `validated_setups` database
   - Ensures MGC/NQ/MPL filters match exactly
   - Catches dangerous mismatches that could cause trading errors

3. **ORB Calculation Accuracy**
   - Verifies ORB size = high - low for all 6 ORBs (0900, 1000, 1100, 1800, 2300, 0030)
   - Checks calculations on recent 5 days of data
   - Identifies any mathematical errors in ORB computations

4. **Session Statistics Calculations**
   - Validates Asia/London/NY session highs and lows
   - Ensures high >= low (no inverted values)
   - Checks for data consistency

5. **Trade Level Calculations**
   - Tests entry/stop/target formulas with known correct answers
   - Verifies LONG and SHORT trade math
   - Tests FULL and HALF stop modes
   - Validates multiple RR ratios (1.0, 1.5, 2.0, 3.0, 8.0)

6. **Filter Logic Correctness**
   - Tests size filter comparisons (>= threshold)
   - Verifies None/NULL filters always pass
   - Ensures filter logic matches strategy rules

7. **Data Completeness & Gaps**
   - Checks date range of bars_1m and daily_features
   - Identifies data gaps or missing days
   - Verifies recent data is present (not stale)

8. **Timezone Handling**
   - Validates timezone configuration (Australia/Brisbane)
   - Checks UTC offset is correct
   - Ensures no DST issues

9. **Validated Setups Completeness**
   - Counts setups for MGC, NQ, MPL
   - Verifies all required fields exist
   - Checks for missing or incomplete setup data

10. **Risk/Reward Mathematics**
    - Validates RR ratios are positive
    - Checks avg_r values are reasonable (-10R to +10R)
    - Ensures no extreme or invalid values

## How to Run

### Method 1: Command Prompt (Recommended)

```cmd
cd C:\Users\sydne\OneDrive\myprojectx
python audit_complete_accuracy.py
```

### Method 2: With Full Path

```cmd
python C:\Users\sydne\OneDrive\myprojectx\audit_complete_accuracy.py
```

## What to Look For

### ✓ PASS (Green)
- Calculation is correct
- Data is valid
- Configuration matches

### ⚠ WARN (Yellow)
- Review recommended but not critical
- May indicate unusual data
- Could be normal (e.g., no data on weekends)

### ✗ FAIL (Red)
- **CRITICAL ERROR**
- Calculation is incorrect
- Data is invalid
- Config mismatch detected
- **DO NOT TRADE until fixed**

## Expected Output

```
================================================================================
COMPLETE DATA ACCURACY & CALCULATION AUDIT
================================================================================

================================================================================
AUDIT 1: Database Schema & Integrity
================================================================================

✓ PASS: Table 'bars_1m' exists
✓ PASS: Table 'bars_5m' exists
✓ PASS: Table 'daily_features' exists
✓ PASS: Table 'validated_setups' exists
...

================================================================================
AUDIT SUMMARY
================================================================================

PASSES:   127
WARNINGS:   3
ERRORS:     0
────────────────────
TOTAL:    130

================================================================================
✓✓✓ ALL AUDITS PASSED - DATA IS ACCURATE AND CALCULATIONS ARE CORRECT ✓✓✓
================================================================================
```

## When to Run This Audit

**Run this audit IMMEDIATELY if:**
- You update `validated_setups` database
- You modify `trading_app/config.py`
- You change ORB filters or RR values
- You backfill new data
- You rebuild daily_features
- Before going live with real money
- After any code changes to calculations

**Run this audit REGULARLY:**
- Once per week as maintenance
- After any system updates
- Before important trading sessions

## What If It Fails?

### Critical Errors (Red)

1. **Config Mismatch**
   - **Fix**: Run `python test_app_sync.py` to see exact mismatch
   - **Action**: Update `trading_app/config.py` to match database
   - **Retest**: Run audit again after fix

2. **Calculation Errors**
   - **Example**: ORB size ≠ (high - low)
   - **Action**: Rebuild daily_features with `python build_daily_features.py`
   - **Retest**: Run audit again

3. **Missing Data**
   - **Action**: Run backfill scripts to populate database
   - **Retest**: Verify data completeness

### Warnings (Yellow)

- Usually informational (e.g., "No data on weekends")
- Review but may not require action
- Document if warnings are expected

## Audit Log

Keep a record of audit runs:

```
Date: 2026-01-16
Result: PASSED (127 passes, 0 errors, 3 warnings)
Notes: Warnings for weekend data gaps (expected)

Date: 2026-01-17
Result: FAILED (Config mismatch - MGC 1000 ORB)
Action: Updated config.py, reran audit
Retest: PASSED
```

## Integration with Test Suite

This audit complements:
- `test_app_sync.py` - Config synchronization verification
- `verify_app_integration.py` - Component integration checks
- `validate_data.py` - Basic data validation

**Recommended order:**
1. Run `audit_complete_accuracy.py` (this script) - FIRST
2. If passed, run `test_app_sync.py` - SECOND
3. If both pass, run `verify_app_integration.py` - THIRD

## Safety Protocol

**NEVER skip this audit when:**
- Making strategy changes
- Updating filters or RR values
- After database modifications
- Before live trading

**This audit is your safety net against:**
- Incorrect calculations
- Config mismatches
- Data corruption
- Logic errors
- Mathematical mistakes

## Color Output

The script uses color coding:
- 🟢 **Green (PASS)**: Correct
- 🟡 **Yellow (WARN)**: Review
- 🔴 **Red (FAIL)**: Fix immediately

## Questions?

If audit fails and you're unsure how to fix:
1. Read the error message carefully
2. Check which audit section failed
3. Review the specific data/calculation mentioned
4. Fix the root cause (config, data, code)
5. Rerun audit to verify fix
6. Document what was fixed

## Automation

You can automate this audit:

```cmd
python audit_complete_accuracy.py > audit_log_2026-01-16.txt
```

This saves the output to a file for later review.

---

**Remember: This audit is your guarantee that calculations are correct and data is accurate. Always run it after changes!**
