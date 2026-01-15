# COMPLETE STRATEGIES INVENTORY - 2026-01-14

## Summary

**Question**: "what about the strategies that used the different sessions between each other"

**Answer**: YES - Multiple session-to-session strategies exist, documented in separate files outside the main playbook.

---

## ALL STRATEGIES - DEPLOYMENT STATUS

### ✅ **DEPLOYED IN APP** (trading_app/live_trading_dashboard.py)

| Strategy | File | Status | Performance |
|----------|------|--------|-------------|
| **ORB Breakouts** | TRADING_RULESET_CANONICAL.md | ✅ ACTIVE | All 6 ORBs profitable |
| - 09:00 ORB | - | ✅ ACTIVE | +0.266R avg, 63.3% WR |
| - 10:00 ORB | - | ✅ ACTIVE | +0.342R avg, 33.5% WR |
| - 11:00 ORB | - | ✅ ACTIVE | +0.299R avg, 64.9% WR |
| - 18:00 ORB | - | ⚠️ ACTIVE (paper first) | +0.425R avg, 71.3% WR |
| - 23:00 ORB | - | ✅ ACTIVE | +1.077R avg, 41.5% WR |
| - 00:30 ORB | - | ✅ ACTIVE | +1.541R avg, 50.8% WR |

---

### ✅ **DOCUMENTED IN PLAYBOOK** (But Not in App)

| Strategy | File | Status | Performance |
|----------|------|--------|-------------|
| **Multi-Liquidity Cascades** | TRADING_PLAYBOOK_COMPLETE.md | ✅ PRIMARY | +1.95R avg (2-3/month) |
| **Single Liquidity Reactions** | TRADING_PLAYBOOK_COMPLETE.md | ✅ BACKUP | +1.44R avg (16% freq) |

---

### ⚠️ **VALIDATED BUT NOT IN PLAYBOOK** (Session-Based)

#### **Asia → London Inventory Resolution**
| Detail | Value |
|--------|-------|
| **File** | ASIA_LONDON_FRAMEWORK.md |
| **Status** | ✅ VALIDATED (structural edge) |
| **Concept** | London trades result of Asia resolving prior inventory |
| **Rules** | Asia resolved prior HIGH → London LONG only (+0.15R) |
| | Asia resolved prior LOW → London SHORT only (+0.15R) |
| | Asia failed to resolve → London ORB baseline |
| **Sample** | Proven in SESSION_CONDITIONAL_EXPECTANCY_REPORT_FINAL.md |
| **In App?** | ❌ NO - Research only |
| **In Playbook?** | ❌ NO |

---

#### **London Advanced Filters (3 Tiers)**
| Detail | Value |
|--------|-------|
| **File** | LONDON_BEST_SETUPS.md |
| **Status** | ✅ VALIDATED (126 configs tested) |
| **Testing** | 499-521 trades, 5+ years data |
| **In App?** | ❌ NO - Research only |
| **In Playbook?** | ❌ NO |

**TIER 1: Highest Edge**
- Config: ASIA_NORMAL + NY_HIGH + SKIP_NY_LOW
- Performance: **+1.059R avg** (68 trades, 51.5% WR)
- RR: 3.0, SL: FULL
- Rules:
  1. Asia range 100-200 ticks
  2. If Asia resolved prior NY high → Trade UP only
  3. If Asia resolved prior NY low → SKIP London
  4. RR = 3.0, stop at opposite ORB edge

**TIER 2: Balanced**
- Config: ASIA_NORMAL + RR 3.0 FULL SL
- Performance: +0.487R avg (199 trades, 37.2% WR)
- Simpler: No directional filters

**TIER 3: High Volume**
- Config: BASELINE + RR 1.5 FULL SL
- Performance: +0.388R avg (499 trades, 55.5% WR)
- Total R: +193.5R (highest)
- Simplest: No filters at all

---

### ❌ **TESTED AND FAILED** (Do Not Trade)

**File**: UNIFIED_FRAMEWORK_RESULTS.md

| Pattern | Sessions | Status | Result |
|---------|----------|--------|--------|
| Failure-to-Continue | 0900, 1000, 1100, 0030 | ❌ NO EDGE | +0.003R to +0.075R (marginal) |
| Volatility Exhaustion | 0900, 1000, 1100, 0030 | ❌ INSUFFICIENT | Too rare (<20 trades) |
| No-Side-Chosen | 0900, 1000, 1100, 0030 | ❌ NO EDGE | Negative results |

**Exception**: 1800 ORB liquidity reaction validated (+0.687R on 49 trades)

---

## COMPARISON: ORB Baseline vs Advanced Filters

### **18:00 London ORB Performance**

| Config | Performance | Trades | WR | Complexity |
|--------|-------------|--------|-----|------------|
| **CANONICAL Baseline** | +0.425R avg | 522 | 71.3% | None (RR 1.0 HALF SL) |
| **TIER 1 Advanced** | **+1.059R avg** | 68 | 51.5% | Filters: ASIA_NORMAL + NY_HIGH + SKIP_NY_LOW, RR 3.0 FULL SL |
| **TIER 3 Baseline** | +0.388R avg | 499 | 55.5% | RR 1.5 FULL SL |

**Key Insight**: Advanced filters can increase edge from +0.4R to **+1.06R** but reduce frequency 7×

---

## WHY AREN'T THESE IN THE PLAYBOOK?

### **Theory 1: Different Development Timeline**
- TRADING_PLAYBOOK_COMPLETE.md created Jan 13
- ASIA_LONDON_FRAMEWORK.md created Jan 12
- LONDON_BEST_SETUPS.md created Jan 12
- Files developed in parallel, not integrated

### **Theory 2: Different Strategy Types**
- **Playbook**: Time-based setups (ORBs, Cascades)
- **Framework files**: Conditional/filter-based (session state)
- May have been kept separate intentionally

### **Theory 3: Validation Status**
- **Playbook strategies**: Fully validated, ready to trade
- **Framework strategies**: Validated edges but need integration testing
- May be waiting for implementation before adding to playbook

---

## SHOULD THEY BE IN THE PLAYBOOK?

### **Arguments FOR Including**:
1. ✅ **Validated edges** (+0.15R to +1.059R improvements)
2. ✅ **Documented thoroughly** (ASIA_LONDON_FRAMEWORK, LONDON_BEST_SETUPS)
3. ✅ **Non-trivial sample sizes** (68-199 trades depending on tier)
4. ✅ **Session-based logic** fits with overall system philosophy
5. ✅ **User is actively trading** and should know about ALL edges

### **Arguments AGAINST Including**:
1. ⚠️ **Not implemented in app** yet
2. ⚠️ **More complex** than baseline ORBs
3. ⚠️ **Lower frequency** than baseline (68 vs 499 trades for London)
4. ⚠️ **Requires additional tracking** (prior session inventory)
5. ⚠️ **May confuse beginners** with too many options

---

## RECOMMENDED ACTION

### **Option 1: Create Strategy Appendix**
Add section to TRADING_PLAYBOOK_COMPLETE.md:
```
## ADVANCED STRATEGIES (Optional)

### Strategy 4: Asia → London Inventory Resolution
[Details from ASIA_LONDON_FRAMEWORK.md]

### Strategy 5: London Advanced Filters (3 Tiers)
[Details from LONDON_BEST_SETUPS.md]

⚠️ These require manual tracking of session inventory
⚠️ Not yet implemented in trading app
⚠️ Trade only after mastering base strategies
```

### **Option 2: Keep Separate**
Leave as separate reference documents:
- ASIA_LONDON_FRAMEWORK.md (for advanced traders)
- LONDON_BEST_SETUPS.md (for advanced traders)
- TRADING_PLAYBOOK_COMPLETE.md (for core strategies)

Mark them clearly in START_HERE_TRADING_SYSTEM.md as "Advanced" reading

### **Option 3: Implement in App First**
1. Add session inventory tracking to app
2. Add London filter logic
3. Test in paper trading
4. THEN add to playbook once proven in live app

---

## USER QUESTION ANSWERED

**Question**: "what about the strategies that used the different sessions between each other"

**Answer**:

YES - Two major session-based strategies exist but are NOT in the main playbook:

1. **Asia → London Inventory Resolution** (+0.15R edges)
   - File: ASIA_LONDON_FRAMEWORK.md
   - Status: Validated, not in app, not in playbook

2. **London Advanced Filters** (+1.059R for Tier 1)
   - File: LONDON_BEST_SETUPS.md
   - Status: Validated, not in app, not in playbook

**These are separate from**:
- Multi-Liquidity Cascades (in playbook)
- Single Liquidity Reactions (in playbook)
- ORB Breakouts (in app + playbook)

**Recommendation**:
- Read ASIA_LONDON_FRAMEWORK.md and LONDON_BEST_SETUPS.md
- Decide if you want to trade them manually (not in app yet)
- Or wait for app implementation

---

## FILES TO READ (Prioritized)

### **Core Trading (Start Here)**:
1. ✅ TRADING_PLAYBOOK_COMPLETE.md - 3 main strategies
2. ✅ TRADING_RULESET_CANONICAL.md - ORB parameters

### **Advanced Session Strategies (After Mastery)**:
3. ⚠️ ASIA_LONDON_FRAMEWORK.md - Inventory resolution
4. ⚠️ LONDON_BEST_SETUPS.md - Advanced filters
5. ⚠️ SESSION_CONDITIONAL_EXPECTANCY_REPORT_FINAL.md - Research backing

### **Research (Reference Only)**:
6. ℹ️ UNIFIED_FRAMEWORK_RESULTS.md - What didn't work

---

## DEPLOYMENT RECOMMENDATION

**If you want these strategies active**:

1. **Immediate (Manual Trading)**:
   - Read ASIA_LONDON_FRAMEWORK.md
   - Read LONDON_BEST_SETUPS.md
   - Manually track prior session inventory
   - Apply filters before entering London ORB trades

2. **Long-term (App Integration)**:
   - Request app feature: Session inventory tracking
   - Request app feature: London filter dropdown
   - Automated strategy selection based on conditions

**Current State**: Documented, validated, but NOT automated in app.

---

**Created**: 2026-01-14
**Status**: COMPLETE INVENTORY
**Confidence**: HIGH (all files reviewed, deployment status verified)
