# ORB FILTER DEPLOYMENT CHECKLIST

**Date Created**: 2026-01-13
**System**: ORB Size Filters + Kelly Position Sizing
**Status**: PRE-DEPLOYMENT TESTING

---

## PHASE 1: PRE-DEPLOYMENT VERIFICATION

### Code Review
- [ ] Review all filter thresholds in `config.py`
  - [ ] 2300: 0.155
  - [ ] 0030: 0.112
  - [ ] 1100: 0.095
  - [ ] 1000: 0.088
  - [ ] 0900: None (correct)
  - [ ] 1800: None (correct)

- [ ] Verify `ENABLE_ORB_SIZE_FILTERS = True` in config.py

- [ ] Review Kelly multipliers in `data_loader.py`
  - [ ] 2300: 1.15x
  - [ ] 0030: 1.61x
  - [ ] 1100: 1.78x
  - [ ] 1000: 1.23x

- [ ] Confirm filter logic in `strategy_engine.py`
  - [ ] Filter rejection returns INVALID state
  - [ ] STAND_DOWN action on rejection
  - [ ] Clear rejection reasons displayed
  - [ ] Position sizing uses multiplier on PASS

- [ ] Verify BOTH LONG and SHORT breakouts have filter logic

### Database Validation
- [ ] Check ATR(20) data availability in `daily_features_v2_half`
  ```bash
  python -c "import duckdb; con = duckdb.connect('gold.db', read_only=True); print(con.execute('SELECT COUNT(*) FROM daily_features_v2_half WHERE atr_20 IS NOT NULL AND instrument = \"MGC\"').fetchone()[0], 'rows with ATR')"
  ```

- [ ] Expected: 700+ rows with ATR data

- [ ] Verify today's ATR is available (or yesterday's as fallback)
  ```bash
  python -c "from trading_app.data_loader import DataLoader; dl = DataLoader(); print('ATR:', dl.get_today_atr())"
  ```

### Unit Testing
- [ ] Test `get_today_atr()` method
  - [ ] Returns valid float when data exists
  - [ ] Falls back to yesterday if today unavailable
  - [ ] Returns None if no data (graceful degradation)

- [ ] Test `check_orb_size_filter()` method
  - [ ] Test PASS case (small ORB)
  - [ ] Test REJECT case (large ORB)
  - [ ] Test with no filter (0900, 1800)
  - [ ] Test with ATR unavailable (should default to PASS)

- [ ] Test `get_position_size_multiplier()` method
  - [ ] Returns correct multiplier for filtered ORBs
  - [ ] Returns 1.0 for non-filtered ORBs
  - [ ] Returns 1.0 when filter not passed

---

## PHASE 2: INTEGRATION TESTING

### End-to-End App Test

**Setup**:
```bash
python app_trading_hub.py
```

**Test Scenarios**:

#### Scenario 1: Small ORB (Should PASS)
- [ ] Wait for ORB formation at 23:00, 00:30, 10:00, or 11:00
- [ ] Verify ORB forms and size is calculated
- [ ] Expected: Filter PASSES (size < threshold)
- [ ] Expected: Position size shows multiplier (e.g., "1.78x size")
- [ ] Expected: Strategy shows READY state on breakout
- [ ] Expected: Entry signal generated with adjusted risk%

#### Scenario 2: Large ORB (Should REJECT)
- [ ] Wait for large ORB formation
- [ ] Expected: Filter REJECTS
- [ ] Expected: Strategy state = INVALID
- [ ] Expected: Action = STAND_DOWN
- [ ] Expected: Reasons include:
  - "ORB SIZE FILTER REJECTED"
  - "ORB size X.Xpts (XX% of ATR) > threshold XX%"
  - "Large ORB = exhaustion pattern"
- [ ] Expected: No entry signal generated

#### Scenario 3: No Filter ORB (0900, 1800)
- [ ] Test 0900 ORB formation
- [ ] Expected: No filter check performed
- [ ] Expected: Normal breakout logic
- [ ] Expected: Position size = 1.0x (baseline)

#### Scenario 4: ATR Unavailable
- [ ] Test with missing ATR data (simulate by temporarily renaming daily_features table)
- [ ] Expected: Filter defaults to PASS
- [ ] Expected: Warning logged
- [ ] Expected: Position size = 1.0x (baseline)
- [ ] Restore table after test

### Logging Validation
- [ ] Check logs for filter decisions
  - [ ] Filter PASS logged with size and threshold
  - [ ] Filter REJECT logged with reason
  - [ ] Kelly multiplier logged when applied
  - [ ] ATR fallback logged if used

- [ ] No errors or exceptions during filter checks

---

## PHASE 3: PAPER TRADING (1 WEEK)

### Daily Monitoring

**Day 1-7**: Run app with `ENABLE_ORB_SIZE_FILTERS = True`, paper trading only

#### Daily Checklist:
- [ ] **Day 1**: Track all ORB formations and filter decisions
  - [ ] Count PASS vs REJECT for each ORB
  - [ ] Verify rejection rates roughly match expected:
    - 2300: 64% rejected (36% kept)
    - 0030: 87% rejected (13% kept)
    - 1100: 89% rejected (11% kept)
    - 1000: 58% rejected (42% kept)

- [ ] **Day 2**: Monitor position sizing
  - [ ] Verify filtered trades show increased risk%
  - [ ] Verify multipliers applied correctly (1.15x-1.78x)
  - [ ] Check total capital at risk < 5%

- [ ] **Day 3**: Test filter rejection messaging
  - [ ] Verify rejection messages are clear
  - [ ] Check user can see threshold and actual ORB size
  - [ ] Confirm "exhaustion pattern" explanation shows

- [ ] **Day 4**: ATR data validation
  - [ ] Verify ATR available for all trading days
  - [ ] Check fallback to yesterday working if needed
  - [ ] Log any days with missing ATR

- [ ] **Day 5**: Performance tracking
  - [ ] Compare filtered trades vs baseline expectation
  - [ ] Check win rate on PASS trades
  - [ ] Track any REJECT trades that would have won (false negatives)

- [ ] **Day 6**: Edge cases
  - [ ] Test behavior on weekend (no ORBs expected)
  - [ ] Test behavior on holiday (partial data)
  - [ ] Verify no crashes or hangs

- [ ] **Day 7**: Weekly summary
  - [ ] Total ORBs formed: ___
  - [ ] Filter PASS: ___
  - [ ] Filter REJECT: ___
  - [ ] Rejection rates vs expected: Within 20%? [ ]
  - [ ] Any unexpected behaviors: ___

### Paper Trading Results Form

```
WEEK 1 PAPER TRADING RESULTS
============================

ORB: 2300
  Total setups: ___
  Filtered trades: ___ (___%)
  Expected: 36%
  Deviation: ___% [ ] < 20% deviation (OK)

ORB: 0030
  Total setups: ___
  Filtered trades: ___ (___%)
  Expected: 13%
  Deviation: ___% [ ] < 20% deviation (OK)

ORB: 1100
  Total setups: ___
  Filtered trades: ___ (___%)
  Expected: 11%
  Deviation: ___% [ ] < 20% deviation (OK)

ORB: 1000
  Total setups: ___
  Filtered trades: ___ (___%)
  Expected: 42%
  Deviation: ___% [ ] < 20% deviation (OK)

Position Sizing:
  Average multiplier applied: ___x
  Max risk in single trade: ___%
  Max simultaneous risk: ___% [ ] < 5% (OK)

Errors/Issues:
  [ ] None
  [ ] List any issues: ___

Overall Assessment:
  [ ] PASS - Ready for live trading
  [ ] NEEDS ADJUSTMENT - List items: ___
  [ ] FAIL - Do not deploy yet
```

---

## PHASE 4: LIVE DEPLOYMENT (FIRST WEEK)

### Pre-Go-Live Final Checks
- [ ] All Phase 1-3 items completed
- [ ] Paper trading results reviewed and acceptable
- [ ] Backup of current config saved
- [ ] Risk limits verified in config.py
- [ ] Emergency stop procedure documented

### Day-by-Day Live Monitoring

#### Day 1 (First Live Day)
- [ ] **Morning**: Enable live trading with `ENABLE_ORB_SIZE_FILTERS = True`
- [ ] **First ORB**: Watch entire cycle (form -> filter -> breakout)
- [ ] **First Trade**: Verify position size calculated correctly
- [ ] **End of Day**: Review all filter decisions
- [ ] **Check**: Any unexpected rejections or passes?
- [ ] **Risk**: Total exposure stayed < 5%? [ ]

#### Day 2-3 (Build Confidence)
- [ ] Monitor filter decisions each day
- [ ] Track win rate on filtered trades
- [ ] Verify Kelly multipliers working as expected
- [ ] Check: No over-leverage events [ ]

#### Day 4-5 (Performance Check)
- [ ] Compare actual vs expected improvements
- [ ] Are filtered trades outperforming baseline? [ ]
- [ ] Any false negatives (great trades rejected)? Count: ___
- [ ] Any false positives (bad trades passed)? Count: ___

#### Day 6-7 (First Week Summary)
- [ ] Calculate first week performance
  - Filtered trades avg R: ___
  - Baseline expectation: +0.510R
  - Deviation: ___% [ ] < 30% deviation (acceptable for small sample)

- [ ] Review all rejection decisions
  - Were they correct? ___/___
  - Any pattern changes? [ ] No

- [ ] Position sizing working correctly
  - Max single trade risk: ___%
  - Max simultaneous risk: ___%
  - Any Kelly calculations incorrect? [ ] None

### Go/No-Go Decision After Week 1

**CRITERIA FOR CONTINUING**:
- [ ] No critical errors or crashes
- [ ] Filter rejection rates within 20% of expected
- [ ] Position sizing calculations correct
- [ ] No over-leverage events
- [ ] Filtered trades performing reasonably (allow 30% deviation in week 1)

**IF ANY FAILS**: Revert to `ENABLE_ORB_SIZE_FILTERS = False`, investigate, fix, re-test

---

## PHASE 5: ONGOING MONITORING (FIRST MONTH)

### Weekly Reviews (Weeks 2-4)

**Each Week**:
- [ ] **Performance**: Calculate filtered vs baseline performance
  - Week 2: Filtered avg R = ___
  - Week 3: Filtered avg R = ___
  - Week 4: Filtered avg R = ___
  - Target: > +0.40R (allow variance)

- [ ] **Rejection Rates**: Check still stable
  - 2300: ___% kept (target 36%)
  - 0030: ___% kept (target 13%)
  - 1100: ___% kept (target 11%)
  - 1000: ___% kept (target 42%)

- [ ] **Position Sizing**: Verify no over-leverage
  - Max simultaneous risk: ___% [ ] < 5%
  - Kelly multipliers applied correctly: [ ] Yes

- [ ] **Regime Check**: Any market changes?
  - Volatility shift? [ ] No
  - Filter effectiveness changing? [ ] No
  - Need threshold adjustment? [ ] No

### Monthly Review (End of Month 1)

**Calculate Month 1 Statistics**:
- Total trades: ___
- Filtered trades: ___ (___%)
- Avg R per trade: ___
- Baseline expectation: +0.510R
- Improvement vs baseline (no filter): ___% [ ] > +20%

**Filter Accuracy**:
- PASS trades win rate: ___%
- REJECT trades win rate (if tracked): ___%
- False negative rate: ___%
- False positive rate: ___%

**Position Sizing Review**:
- Average Kelly multiplier: ___x
- Largest position taken: ___%
- Any over-leverage events: [ ] None
- Risk management working: [ ] Yes

**Decision**:
- [ ] **CONTINUE** - System working as expected
- [ ] **ADJUST** - Minor tweaks needed (list: ___)
- [ ] **INVESTIGATE** - Performance below expectations
- [ ] **DISABLE** - System not working, revert and analyze

---

## EMERGENCY PROCEDURES

### If System Behaves Unexpectedly

**Immediate Actions**:
1. [ ] Set `ENABLE_ORB_SIZE_FILTERS = False` in config.py
2. [ ] Restart trading app
3. [ ] Document the unexpected behavior
4. [ ] Review recent filter decisions in logs
5. [ ] Check for data issues (missing ATR, corrupt features)

### If Over-Leverage Detected

**Immediate Actions**:
1. [ ] Close any open positions if risk > 5%
2. [ ] Check position size calculations in logs
3. [ ] Verify Kelly multipliers not exceeding 2.0x
4. [ ] Review recent trades for sizing errors
5. [ ] Disable filters if sizing calculation is wrong

### If Performance Significantly Worse

**Definition**: Filtered trades performing > 50% worse than expected for > 2 weeks

**Actions**:
1. [ ] Check for regime change (volatility, market structure)
2. [ ] Analyze recent REJECT decisions (missing good trades?)
3. [ ] Analyze recent PASS decisions (taking bad trades?)
4. [ ] Consider threshold adjustment if regime shifted
5. [ ] Consult backtest with recent data to validate

---

## CONTACT/ESCALATION

**If Issues Arise**:
1. Document the issue clearly (what, when, which ORB, data)
2. Disable filters immediately if critical
3. Review deployment checklist to find relevant test
4. Check logs for error messages or warnings
5. Validate data integrity (ATR, ORB sizes)

---

## COMPLETION SIGN-OFF

### Phase 1: Pre-Deployment Verification
- [ ] Completed by: ___
- [ ] Date: ___
- [ ] Issues found: ___
- [ ] Issues resolved: [ ]

### Phase 2: Integration Testing
- [ ] Completed by: ___
- [ ] Date: ___
- [ ] All scenarios passed: [ ]

### Phase 3: Paper Trading (1 Week)
- [ ] Completed by: ___
- [ ] Start date: ___
- [ ] End date: ___
- [ ] Results: [ ] PASS [ ] FAIL

### Phase 4: Live Deployment (First Week)
- [ ] Go-live date: ___
- [ ] Week 1 results: [ ] CONTINUE [ ] INVESTIGATE [ ] DISABLE

### Phase 5: Ongoing Monitoring (First Month)
- [ ] Month 1 complete: ___
- [ ] Performance vs target: ___% (target > +20%)
- [ ] Decision: [ ] CONTINUE [ ] ADJUST [ ] INVESTIGATE [ ] DISABLE

---

**CHECKLIST COMPLETE**: System validated and ready for production
**DATE**: ___
**SIGNED OFF BY**: ___
