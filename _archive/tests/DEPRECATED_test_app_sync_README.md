# test_app_sync.py - DEPRECATED (2026-01-16)

## Why This Test Was Deprecated

`test_app_sync.py` was created to validate synchronization between:
- `validated_setups` database table
- `trading_app/config.py` hardcoded dictionaries (MGC_ORB_CONFIGS, MGC_ORB_SIZE_FILTERS)

## The Problem It Solved

Before 2026-01-16, configs were maintained in TWO places:
1. Database: `gold.db` → `validated_setups` table
2. Code: `trading_app/config.py` → hardcoded dictionaries

This required manual synchronization:
1. Update database with new RR/filters
2. Manually copy values to config.py
3. Run test_app_sync.py to verify match

**Risk:** Forgetting step 2 or 3 caused mismatches → wrong RR values in live trading → real money losses

## The Solution (Why Test No Longer Needed)

On 2026-01-16, we implemented **auto-generated configs**:
- Created `config_generator.py` to read from database
- Modified `trading_app/config.py` to load dynamically:
  ```python
  MGC_ORB_CONFIGS, MGC_ORB_SIZE_FILTERS = load_instrument_configs('MGC')
  ```

**Result:** Single source of truth (database). Config and database are ALWAYS in sync by design.

## Test Still Passes

The test still passes because config.py now reads from the same database the test queries. But it's redundant - synchronization is automatic now.

## Historical Context

This test prevented a critical bug discovered on 2026-01-16:
- `validated_setups` was updated with CORRECTED MGC values (after scan window bug fix)
- `config.py` still had OLD audit values
- Mismatch: 1000 ORB showed RR=1.0 in app instead of RR=8.0!
- If not caught, would have caused huge losses in live trading

This test saved us once, then we fixed the root cause so it can never happen again.

## Recommendation

Keep this test archived as documentation of the problem we solved. Do not use in production - config_generator.py is the new solution.
