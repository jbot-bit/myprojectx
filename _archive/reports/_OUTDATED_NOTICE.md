# OUTDATED DOCUMENTATION NOTICE

**Date**: 2026-01-14

## Files Archived

The following files have been archived with `_OUTDATED_` prefix because they contain **incorrect RR 4.0 claims** for 2300/0030 ORBs that were never tested:

### 1. _OUTDATED_NY_ORB_TRADING_GUIDE_JAN14.md
**Reason**: Entire guide based on RR 4.0 configuration that was never backtested
- Claimed: RR 4.0, +1.077R avg for 2300, +1.541R avg for 0030
- Reality: RR 1.0, +0.387R avg for 2300, +0.231R avg for 0030
- Impact: 4× performance inflation

### 2. _OUTDATED_TIERED_PLAYBOOK_COMPLETE_JAN14.md
**Reason**: Contains inflated performance claims for 2300/0030 ORBs
- Same incorrect RR 4.0 claims
- Strategy recommendations based on wrong numbers

## Correct Documentation

Use these verified documents instead:

### Primary References
- **TRADING_PLAYBOOK_COMPLETE.md** (Updated 2026-01-14)
- **TRADING_RULESET_CANONICAL.md** (Verified accurate)
- **CORRECTED_PERFORMANCE_SUMMARY.md** (Database-verified numbers)

### Configuration Files (All Corrected)
- trading_app/config.py
- trading_app/live_trading_dashboard.py
- trading_app/strategy_recommender.py

### Verification Documents
- **COMPREHENSIVE_STRATEGY_AUDIT_2026-01-14.md** (Complete audit)
- **VERIFICATION_COMPLETE_2026-01-14.md** (Fix status report)
- **FINAL_SYSTEM_VERIFICATION.py** (Automated verification)

## What Was Wrong

**The Problem:**
- Documentation claimed 2300/0030 ORBs used "RR 4.0" configuration
- This configuration was NEVER tested or implemented
- Database shows ALL trades use RR 1.0 (r_multiple = +/-1.0)
- Performance claims were inflated by 4×

**The Fix:**
- All config files corrected to RR 1.0
- All documentation updated with accurate database-verified numbers
- System now honest and consistent across all files

## Corrected Performance (Database Verified)

### 2300 ORB (NY Futures Session)
- RR: 1.0 (not 4.0)
- Win Rate: 69.3% (per trade, not per day)
- Avg R: +0.387R per trade
- Annual: ~+100R/year

### 0030 ORB (Asia Transition)
- RR: 1.0 (not 4.0)
- Win Rate: 61.6% (per trade, not per day)
- Avg R: +0.231R per trade
- Annual: ~+60R/year

## System-Wide Performance (All 6 ORBs)

- Data: 740 days (2024-01-02 to 2026-01-10)
- Total Trades: 3,133
- Overall Win Rate: 69.9%
- Total R: +1,183R
- **Annual: ~+585R/year** (honest, database-verified)

**Previous (INFLATED)**: ~+908R/year
**Corrected (HONEST)**: ~+585R/year
**Difference**: -36% (but ACCURATE)

## Audit Trail

All corrections documented in:
1. COMPREHENSIVE_STRATEGY_AUDIT_2026-01-14.md
2. VERIFICATION_COMPLETE_2026-01-14.md
3. CORRECTED_PERFORMANCE_SUMMARY.md

Run verification: `python FINAL_SYSTEM_VERIFICATION.py`

---

**Status**: System verified honest and consistent as of 2026-01-14
