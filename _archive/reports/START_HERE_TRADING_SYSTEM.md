# START HERE - Complete Trading System
**Gold (MGC) Liquidity-Based Trading**
**Date**: 2026-01-13

---

## You Asked For

1. ✅ **All strategies in a playbook**
2. ✅ **When/how trades show up**
3. ✅ **Positive outcomes with zero lookahead bias**
4. ✅ **Best ORB strategies included**
5. ✅ **ALL validated strategies now documented** (Updated 2026-01-14)

**This document guides you to the right files for each purpose.**

⚠️ **UPDATED 2026-01-14**: Playbook now includes 17 strategies (8 automated, 9 validated manual/advanced)

---

## Quick Start: What To Read First

### 1. Strategy Overview (5 minutes)
**Read**: `STRATEGY_HIERARCHY_FINAL.md`
- See all 8 strategies ranked by performance
- Understand PRIMARY (cascades) vs SECONDARY (ORBs) vs BACKUP (single liquidity)
- Get daily decision flow (what to check when)

### 2. Complete Playbook (60 minutes) ⭐ READ THIS FIRST
**Read**: `TRADING_PLAYBOOK_COMPLETE.md` ⚠️ UPDATED JAN 14
- **Strategy 1**: ORB Breakouts (6 MGC ORBs - CANONICAL configs) ✅ In App
- **Strategy 2**: Single Liquidity Reactions (backup strategy) ✅ In Playbook
- **Strategy 3**: Multi-Liquidity Cascades (PRIMARY - strongest edge) ✅ In Playbook
- **Strategy 4**: NQ ORB Breakouts (5 NQ ORBs - alternative instrument) ⚠️ TIER 4
- **Strategy 5**: London Advanced Filters (3 tiers) ⚠️ TIER 3 - Manual Only
- **Strategy 6**: Session-Based Enhancements (Engine A) ⚠️ TIER 3 - Manual Only
- **Strategy 7**: Outcome Momentum (Engine B) ⚠️ TIER 3 - Manual Only
- **Strategy 8**: Positioning & Filters (3 types) ⚠️ TIER 3 - Manual Only
- **Total**: 17 strategies documented (8 automated, 9 manual/validated)
- Complete entry/exit rules for all strategies
- When trades show up and how to recognize them

**Read**: `TRADING_RULESET_CANONICAL.md`
- Technical reference for ORB parameters only
- Detailed performance metrics and filters

**Read**: `CORRECTED_PERFORMANCE_SUMMARY.md`
- Database-verified performance for all 6 ORBs
- Honest performance numbers (updated 2026-01-14)

### 3. Desk Reference (Print This!)
**Print**: `CASCADE_QUICK_REFERENCE.md`
- One-page checklist for 23:00 trading window
- Pre-entry checklist
- Position size calculator
- Mental checks
- Keep visible at your desk during 22:55-23:30

---

## Deep Dive: Understanding the Edge

### Cascade Mechanics (20 minutes)
**Read**: `CASCADE_PATTERN_RECOGNITION.md`
- Complete pattern breakdown
- Why cascades work (forced liquidation mechanics)
- What destroys edge (tested failures)
- All 10 validation tests
- Session integrity requirements
- Gap size multiplier proof

### Lookahead Verification (15 minutes)
**Read**: `LOOKAHEAD_BIAS_VERIFICATION.md`
- Proves zero lookahead bias in all strategies
- Timeline analysis (when data becomes available)
- Code verification
- Reproduction instructions
- Backtesting vs live trading comparison

---

## Implementation: Tools & Scripts

### Daily Monitoring

**During Trading** (Real-Time):
```bash
python monitor_cascade_live.py              # Today's cascade monitoring
python monitor_cascade_live.py 2026-01-13  # Specific date
```

**After Trade** (Analysis):
```bash
python track_cascade_exits.py --entry 2711.5 --stop 2713.0 --direction SHORT --date 2025-01-10
```

### Backtesting & Verification

**Reproduce Cascade Results**:
```bash
python test_cascade_minimal.py
# Expected: 69 setups, +1.95R avg, large gap +5.36R
```

**Reproduce ORB Results**:
```bash
python backtest_all_orbs_complete.py 2024-01-01 2026-01-10
# Expected: All 6 ORBs positive, 00:30 best (+1.54R), 23:00 strong (+1.08R)
```

**Reproduce Single Liquidity Results**:
```bash
python test_liquidity_reaction_minimal.py
# Expected: 120 setups, +1.44R avg
```

### Analysis Scripts

**Cascade Timing**:
```bash
python analyze_cascade_timing.py
# Shows: 70% enter at 23:00, median peak 3-5min, must hold 90min
```

**Bidirectional Validation**:
```bash
python test_cascade_bidirectional.py
# Shows: Both SHORT (+1.95R) and LONG (+1.00R) work
```

**Pattern Tests** (what we learned):
- `test_ny_to_asia_cascade.py` - FAILED (partial sessions don't work)
- `test_london_to_next_asia.py` - FAILED (overnight gaps break chain)
- `test_asia_london_early_exit.py` - FAILED (early exit destroys edge)
- `test_structure_only_no_second_sweep.py` - WEAKENS EDGE (failure is mandatory)

---

## File Directory

### Core Playbooks
| File | Purpose | Read When |
|------|---------|-----------|
| `STRATEGY_HIERARCHY_FINAL.md` | Strategy ranking & decision tree | **START HERE** |
| `TRADING_PLAYBOOK_COMPLETE.md` | Complete 3-strategy playbook (updated 2026-01-14) | **READ FIRST** |
| `TRADING_RULESET_CANONICAL.md` | ORB parameters reference | Before trading |
| `CORRECTED_PERFORMANCE_SUMMARY.md` | Database-verified performance | Before trading |
| `CASCADE_QUICK_REFERENCE.md` | One-page desk reference | **PRINT & KEEP AT DESK** |

### Deep Understanding
| File | Purpose | Read When |
|------|---------|-----------|
| `CASCADE_PATTERN_RECOGNITION.md` | Full cascade mechanics | To understand why it works |
| `LOOKAHEAD_BIAS_VERIFICATION.md` | Proves reproducibility | To trust the results |

### Monitoring Tools
| File | Purpose | Use When |
|------|---------|----------|
| `monitor_cascade_live.py` | Real-time cascade monitoring | 09:00, 17:00, 23:00 |
| `track_cascade_exits.py` | Exit tracking & analysis | After trade completion |

### Backtest Scripts
| File | Purpose | Expected Result |
|------|---------|-----------------|
| `test_cascade_minimal.py` | Cascade validation | 69 setups, +1.95R |
| `backtest_all_orbs_complete.py` | All ORBs | 00:30 +1.54R, 23:00 +1.08R |
| `test_liquidity_reaction_minimal.py` | Single liquidity | 120 setups, +1.44R |

### Analysis Results
| File | Contains |
|------|----------|
| `canonical_session_parameters.csv` | Optimal ORB configs (locked) |
| `complete_orb_sweep_results.csv` | All 252 ORB configs tested |

### Database & Data
| File | Purpose |
|------|---------|
| `gold.db` | Main database (bars_1m, daily_features) |
| `build_daily_features_v2.py` | Feature builder |
| `backfill_databento_continuous.py` | Data backfiller |

---

## Strategy Performance Summary

### MGC (Gold) - Tested: 741 days (2024-01-02 to 2026-01-10)

#### TIER 1-2: AUTOMATED (In App)
| Strategy | Avg R | Frequency | Win Rate | Priority | Risk/Trade |
|----------|-------|-----------|----------|----------|------------|
| **Cascades** | **+1.95R** | 9.3% (2-3/mo) | 19-27% | PRIMARY | 0.10-0.25% |
| **00:30 ORB** | **+1.54R** | 56% days | 50.8% | PRIMARY | 0.25-0.50% |
| Single Liquidity | +1.44R | 16% days | 33.7% | BACKUP | 0.25-0.50% |
| 23:00 ORB | +1.08R | 63% days | 41.5% | SECONDARY | 0.25-0.50% |
| 18:00 ORB | +0.43R | 64% days | 71.3% | SECONDARY | 0.10-0.25% |
| 10:00 ORB | +0.34R | 64% days | 33.5% | SECONDARY | 0.10-0.25% |
| 11:00 ORB | +0.30R | 66% days | 64.9% | SECONDARY | 0.10-0.25% |
| 09:00 ORB | +0.27R | 66% days | 63.3% | SECONDARY | 0.10-0.25% |

**Expected: +461R/year (TIER 1-2 automated strategies)**

#### TIER 3: ADVANCED (Manual Only - NOT in app yet)
| Strategy | Improvement | Frequency | Status |
|----------|-------------|-----------|--------|
| London Filters Tier 1 | +1.059R avg | ~14/year | ⚠️ Manual tracking required |
| Asia→London Inventory | +0.15R per setup | ~80/year | ⚠️ Manual tracking required |
| Outcome Momentum | +2-5% WR | Asia ORBs | ⚠️ Manual tracking required |
| Positioning | +0.05-0.06R | Asia ORBs | ⚠️ Manual tracking required |
| Lagged Features | +0.15-0.19R | 00:30, 11:00 | ⚠️ Manual tracking required |
| Size Filters | +0.06-0.35R | 4 ORBs | ❓ Check if in app |

**Expected: +80R/year additional (TIER 3 if manually tracked)**

#### TIER 4: NQ (Alternative Instrument)
| Strategy | Avg R | Frequency | Win Rate | Status |
|----------|-------|-----------|----------|--------|
| NQ 00:30 ORB | +0.292R | 100% days | 61.2% | ⚠️ Validated |
| NQ 11:00 ORB | +0.260R | 93% days | 62.7% | ⚠️ Validated |
| NQ 18:00 ORB | +0.257R | 93% days | 62.5% | ⚠️ Validated |
| NQ 10:00 ORB | +0.174R | 89% days | 58.7% | ⚠️ Validated |
| NQ 09:00 ORB | +0.145R | 63% days | 57.3% | ⚠️ Validated |

**Expected: +208R/year (NQ diversification)**

### **TOTAL SYSTEM**
- **Automated (TIER 1-2)**: +461R/year
- **Advanced (TIER 3)**: +80R/year (manual)
- **Alternative (TIER 4)**: +208R/year (NQ)
- **COMBINED**: +461R to +749R/year

**All strategies have positive edge and zero lookahead bias.**

---

## Daily Routine

### Morning (08:00-09:00)
- [ ] Run `monitor_cascade_live.py` for yesterday (if you missed it)
- [ ] Review any overnight cascade results
- [ ] Note Asia session start (09:00)

### Asia Session (09:00-17:00)
- [ ] Track Asia high/low (for cascade later)
- [ ] Optional: Trade day ORBs (09:00, 10:00, 11:00) if interested

### Pre-London (17:00)
- [ ] Note Asia high: ______ Asia low: ______
- [ ] Set alert for London tracking

### London Session (18:00-23:00)
- [ ] Track London high/low
- [ ] Optional: Trade 18:00 ORB if interested
- [ ] **At 22:30**: Calculate cascade gap (London high - Asia high)
  - **If gap >9.5pts → PREPARE FOR CASCADE at 23:00**
  - **If gap <9.5pts → PREPARE FOR ORB at 23:00**

### CRITICAL WINDOW (22:55-23:30)
- [ ] **22:55**: Get ready, review CASCADE_QUICK_REFERENCE.md
- [ ] **23:00-23:05**: PRIMARY CASCADE CHECK (if gap >9.5pts)
  - Watch for second sweep
  - Watch for acceptance failure
  - Entry at London level if confirmed
- [ ] **23:00-23:05**: SECONDARY 23:00 ORB (if no cascade)
  - Track 23:00-23:05 ORB
  - Entry at 23:05+ on breakout
- [ ] **23:30**: Stand down if nothing triggered

### NY Session (00:30-02:00)
- [ ] **00:30**: TERTIARY 00:30 ORB (if no cascade, no 23:00 ORB)
  - Track 00:30-00:35 ORB
  - Entry at 00:35+ on breakout
- [ ] If cascade running: Trail structure, no fixed-time exit

---

## Key Rules (NEVER BREAK)

### Entry Rules
1. ✅ **Cascades ALWAYS PRIORITY** - Check first, always
2. ✅ **Gap >9.5pts MANDATORY** - No large gap = no cascade edge
3. ✅ **Acceptance failure MANDATORY** - No failure = no confirmation
4. ✅ **Entry at level (±0.1pts)** - Precision matters
5. ✅ **ONE STRATEGY PER DAY** - Never cascade + ORB same day

### Exit Rules
1. ✅ **Phase 1**: Move to BE at +1R (within 10min)
2. ✅ **Phase 2**: Trail structure (after 15min)
3. ✅ **Time limit**: 90min max hold
4. ❌ **NEVER fixed-time exit** - Destroys edge (-1.78R vs +1.95R)

### Risk Rules
1. ✅ **Cascades**: 0.10-0.25% (NON-NEGOTIABLE)
2. ✅ **Night ORBs**: 0.25-0.50%
3. ✅ **Day ORBs**: 0.10-0.25%
4. ✅ **Max daily**: 0.50-1.00% across all trades

---

## Psychological Expectations

### Cascades (PRIMARY)
- **Feel like**: Venture capital (most lose, rare huge win)
- **Expect**: 70%+ losing trades
- **Expect**: 5-14 consecutive losses
- **Median R**: -1R (most trades lose)
- **Max R**: +129R (tail events fund system)

### Night ORBs (SECONDARY)
- **Feel like**: Growth stocks (frequent, moderate wins)
- **Expect**: 41-51% win rate
- **Max R**: ~+20R (predictable)

### Day ORBs (TERTIARY)
- **Feel like**: Dividend stocks (grind, high win rate)
- **Expect**: 33-65% win rate
- **Max R**: ~+8-15R (small, consistent)

**Mental Model**: You're building a portfolio of low-correlated edges, not picking one strategy.

---

## Before You Trade Checklist

### Knowledge
- [ ] Read STRATEGY_HIERARCHY_FINAL.md (strategy ranking)
- [ ] Read TRADING_PLAYBOOK_COMPLETE.md (all 3 strategies)
- [ ] Read TRADING_RULESET_CANONICAL.md (ORB parameters)
- [ ] Read NY_ORB_TRADING_GUIDE.md (NY ORBs explained)
- [ ] Print CASCADE_QUICK_REFERENCE.md (desk reference)
- [ ] Read CASCADE_PATTERN_RECOGNITION.md (understand mechanics)
- [ ] Read LOOKAHEAD_BIAS_VERIFICATION.md (trust results)

### Setup
- [ ] Database has data (2020+ recommended)
- [ ] Run backtests to verify results match expected
- [ ] `monitor_cascade_live.py` works
- [ ] `track_cascade_exits.py` works
- [ ] Alerts set for 17:00, 22:30, 23:00, 00:30

### Execution
- [ ] Position size calculator ready
- [ ] Risk limits programmed (0.10-0.25% cascades, etc.)
- [ ] Understand entry rules (all must be true)
- [ ] Understand exit rules (Phase 1 BE, Phase 2 structure trail)
- [ ] Understand priority (Cascades > Night ORBs > Day ORBs)

### Psychology
- [ ] I accept 70%+ cascade trades will lose
- [ ] I accept 5-14 consecutive cascade losses
- [ ] I will NOT increase size after wins
- [ ] I will NOT decrease size after losses
- [ ] I trust the process (edge is proven over 741 days)

**When all checked → START PAPER TRADING FOR 20-40 DAYS**

---

## Next Steps

### Week 1-2: Paper Trading
- [ ] Trade cascades with paper money (0.10% risk)
- [ ] Trade 23:00/00:30 ORBs with paper money (0.25% risk)
- [ ] Log every trade in CASCADE_QUICK_REFERENCE.md format
- [ ] Track: entry timing, gap size, R outcomes, adherence to rules

### Week 3-4: Validation
- [ ] Validate cascade frequency (expect 2-3 setups)
- [ ] Validate gap-size correlation (large > small)
- [ ] Validate 23:00 timing (70% of entries)
- [ ] Validate R distribution (median -1R, occasional huge R)

### Week 5+: Size Validation
- [ ] Increase to 0.25% cascade risk if comfortable
- [ ] Track emotional response to 5+ consecutive losses
- [ ] Confirm you can hold through -1R strings
- [ ] If all good → GO LIVE with full size

### Quarterly: Edge Monitoring
- [ ] Average R >+1.0R? (cascades)
- [ ] Frequency 8-12%? (cascades)
- [ ] Gap correlation holds? (large >> small by 5×+)
- [ ] If YES to all → Edge persists, continue trading
- [ ] If NO to 2+ → STOP, re-analyze for 30 days

---

## Support & Questions

### If Results Don't Match
1. Check database date range (should be 2024-01-02 to 2026-01-10)
2. Check sl_mode ("half" for ORBs, "full" for some)
3. Re-run feature builder: `python build_daily_features_v2.py 2024-01-01 --sl-mode half`
4. Compare your output to expected results in this document

### If You Find Bugs
- All code is auditable and open-source
- Check LOOKAHEAD_BIAS_VERIFICATION.md for verification logic
- Database schema: bars_1m (raw data) + daily_features (derived)

### If Edge Degrades
- Quarterly review: frequency, average R, gap correlation
- If average R drops below +1.0R (cascades) → Re-evaluate
- If frequency increases >15% → Selectivity may be degrading

---

## Final Notes

**You now have**:
1. ✅ **8 strategies ranked** by performance (cascades best, ORBs next)
2. ✅ **Complete playbook** with when/how trades show up
3. ✅ **Zero lookahead bias** (proven and verified)
4. ✅ **Positive outcomes** (all strategies have edge)
5. ✅ **Reproduction** instructions (all results verifiable)
6. ✅ **Monitoring tools** (real-time + post-trade analysis)

**Your job**:
1. **Study** the materials (1-2 days)
2. **Paper trade** (20-40 days)
3. **Validate** edge (frequency, R dist, gap correlation)
4. **Go live** with proper sizing (0.10-0.25% cascades)
5. **Monitor** quarterly for edge decay

**The edge is real. The system is complete. Now execute.**

---

**Good luck, and trust the process.**
