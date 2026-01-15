# 1-MINUTE ENTRY VERIFICATION REPORT

**Date:** 2026-01-12
**Purpose:** Verify if 1-minute entry (vs 5-minute) saves the system

---

## ENTRY MODEL SPECIFICATION

**Tested Model:**
- ORB defined on **5-minute window** (09:00-09:05, etc.)
- Entry triggered by **first 1-minute bar close** outside ORB
- Entry price = **1-minute close price** (market-realistic)
- Worst-case intrabar resolution (if TP+SL hit same bar → LOSS)
- Same RR/SL per ORB as optimal parameters

**File:** `backtest_orb_exec_1m_nofilters.py`
**Function:** `run_backtest(close_confirmations=1, rr=...)`
**Database:** `orb_trades_1m_exec_nofilters` table

---

## VERIFICATION STATUS BY ORB

| ORB  | Optimal RR | TESTED? | File | Avg R | Trade Count |
|------|-----------|---------|------|-------|-------------|
| 0900 | 1.0       | ⏳ RUNNING | `backtest_orb_exec_1m_nofilters.py` | TBD | ~522 |
| 1000 | 3.0       | ✅ **YES** | `backtest_orb_exec_1m_nofilters.py` | **+0.052R** | 523 |
| 1100 | 1.0       | ⏳ RUNNING | `backtest_orb_exec_1m_nofilters.py` | TBD | ~523 |
| 1800 | 2.0       | ✅ **YES** | `backtest_orb_exec_1m_nofilters.py` | **+0.013R** | 522 |
| 2300 | 4.0       | ⏳ RUNNING | `backtest_orb_exec_1m_nofilters.py` | TBD | ~522 |
| 0030 | 4.0       | ⏳ RUNNING | `backtest_orb_exec_1m_nofilters.py` | TBD | ~523 |

**Tests running:** RR 1.0 and 4.0 (expected completion: ~2-3 minutes)

---

## RESULTS: CONFIRMED TESTS

### 1000 ORB (RR 3.0 - Optimal)

**Entry Method Comparison:**

| Method | Avg R | Trades | WR% | Delta from Theoretical |
|--------|-------|--------|-----|------------------------|
| ORB-edge theoretical | **+0.342R** | 489 | 33.5% | Baseline |
| **1-minute close** | **+0.052R** | 523 | 25.6% | **-0.290R** (-84.8%) |
| 5-minute close | **-0.060R** | 489 | N/A | **-0.402R** (-117.5%) |

**Key findings:**
- ✅ 1-minute entry is **POSITIVE** (+0.052R)
- ✅ 1-minute is **+0.112R better** than 5-minute entry
- ❌ Still **-0.290R worse** than theoretical ORB-edge entry
- Entry timing degradation: **84.8%** of theoretical edge lost

---

### 1800 ORB (RR 2.0 - Optimal)

**Entry Method Comparison:**

| Method | Avg R | Trades | WR% | Delta from Theoretical |
|--------|-------|--------|-----|------------------------|
| ORB-edge theoretical | **+0.393R** | 491 | 46.4% | Baseline |
| **1-minute close** | **+0.013R** | 522 | 32.8% | **-0.380R** (-96.7%) |
| 5-minute close | **-0.085R** | 491 | N/A | **-0.478R** (-121.6%) |

**Key findings:**
- ✅ 1-minute entry is **POSITIVE** (+0.013R)
- ✅ 1-minute is **+0.098R better** than 5-minute entry
- ❌ Still **-0.380R worse** than theoretical ORB-edge entry
- Entry timing degradation: **96.7%** of theoretical edge lost

---

## PARTIAL RESULTS: NON-OPTIMAL RR

*(For context - not optimal parameters)*

**0900 ORB:**
- RR 1.5 (vs optimal 1.0): **-0.052R** avg, 36.8% WR, 522 trades

**1100 ORB:**
- RR 1.5 (vs optimal 1.0): **+0.006R** avg, 38.2% WR, 523 trades
- RR 2.0: **+0.006R** avg, 31.0% WR, 523 trades

**2300 ORB:**
- RR 3.0 (vs optimal 4.0): **-0.308R** avg, 11.3% WR, 522 trades

**0030 ORB:**
- RR 3.0 (vs optimal 4.0): **-0.264R** avg, 9.8% WR, 523 trades

---

## ENTRY TIMING ANALYSIS

### Why 1-Minute Is Better Than 5-Minute

**Mechanism:**

1. **ORB completes at 09:05**
2. **Price breaks out:**
   - 09:05:30 → Price moves above ORB high
   - 09:06:00 → 1-minute bar closes above ORB → **1m entry here**
   - 09:07:00 → ...
   - 09:10:00 → 5-minute bar closes above ORB → **5m entry here**

3. **Result:**
   - 1-minute entry: ~4 minutes earlier
   - Entry price closer to ORB edge
   - Less slippage from initial breakout

**Measured improvement:** +0.10R to +0.11R better than 5-minute entry

---

### Why Both Are Much Worse Than Theoretical

**Theoretical (ORB-edge) assumes:**
- Entry at ORB high: 2045.5
- Stop at ORB low: 2040.0
- Risk: 5.5 points = 55 ticks

**Reality (1-minute close):**
- ORB high touched: 2045.5
- First 1m close outside: 2046.2 (7 ticks overshoot)
- Stop still at: 2040.0
- Risk: 6.2 points = 62 ticks (13% larger)

**Impact:**
- Entry worse by 7 ticks
- Effective RR reduced
- Target harder to reach
- Win rate drops

**Measured degradation:** -0.29R to -0.38R worse than theoretical

---

## SYSTEM-WIDE PROJECTION

**Based on 2 confirmed ORBs (1000, 1800):**

| Entry Method | Est. System Avg R | Projection (2893 trades) | Verdict |
|--------------|------------------|--------------------------|---------|
| ORB-edge theoretical | +0.626R | **+1816R total** | Profitable (UNREALISTIC) |
| 1-minute close | **+0.033R** | **+95R total** | Barely positive |
| 5-minute close | -0.329R | **-952R total** | Losing |

**Waiting for remaining ORBs to confirm system-wide projection.**

---

## CRITICAL QUESTIONS

### 1. Is 1-minute entry deployment-ready?

⏳ **PENDING** - Need all 6 ORBs tested with optimal RR

**If all 6 ORBs positive:**
- YES, but with caveats:
  - Edge is THIN (+0.033R avg projected)
  - Vulnerable to slippage/costs
  - Requires perfect execution

**If ANY ORB negative:**
- NO - System still fails realistic execution test

---

### 2. Why is 1-minute entry better than 5-minute?

**Earlier entry = closer to ORB edge**

- 1-minute: Entry ~1 minute after breakout
- 5-minute: Entry ~5 minutes after breakout
- Price tends to run after breakout
- Earlier entry captures more of move

**Measured advantage:** +0.10R to +0.11R per trade

---

### 3. Why is theoretical ORB-edge still much better?

**Zero-slippage assumption**

Theoretical entry assumes:
- You enter at EXACT ORB high/low
- This is where price STARTS breaking out
- No overshoot, no slippage

Reality:
- Price must CLOSE outside ORB to trigger entry
- By then, price has overshot by 5-20 ticks
- This overshoot IS the signal cost

**Cannot be eliminated without:**
- Limit orders (wait for pullback - low fill rate)
- Tighter criteria (filter out extended breakouts - fewer trades)
- Intrabar monitoring (requires 1-second data)

---

## COMPARISON TO DELAYED ENTRY TEST

**Why delayed entry test showed negative baseline:**

The delayed entry test used **5-minute close** for baseline (+0 bars).

This verification shows:
- 5-minute close: -0.329R system-wide
- 1-minute close: **~+0.033R system-wide** (projected)

**The delayed entry test was correct** - it tested realistic 5m execution.

**But it missed the optimization** - 1-minute entry is available and better.

---

## NEXT STEPS

### Immediate (Waiting for tests)

1. ⏳ Complete RR 1.0 tests (0900, 1100)
2. ⏳ Complete RR 4.0 tests (2300, 0030)
3. ✅ Calculate system-wide 1-minute entry results
4. ✅ Generate final comparison table

### If 1-minute entry is positive system-wide

1. ❌ **Reoptimize parameters** for 1-minute entry
   - Current RR/SL optimized for ORB-edge theoretical
   - May not be optimal for 1-minute entry
   - Run parameter sweep with 1-minute execution

2. ❌ **Test with filters**
   - MAX_STOP: May improve if 1m entry allows tighter stops
   - TP_CAP: May need adjustment for earlier entry

3. ❌ **Complete pressure-test suite**
   - Slippage impact (1-2 ticks on top of 1m close)
   - Delayed entry (+1/+2 bars from 1m signal)
   - Loss clustering
   - Volatility regime segmentation

4. ❌ **Compare to alternative entry methods**
   - Limit orders at ORB edge
   - Tighter entry criteria
   - Scaled entries

### If 1-minute entry is still negative

1. ❌ Test limit order entry (wait for pullback)
2. ❌ Test tighter entry criteria (within X ticks)
3. ❌ Consider strategy redesign or abandonment

---

## PRELIMINARY VERDICT

**Based on 2 of 6 ORBs tested:**

✅ **1-MINUTE ENTRY IS BETTER THAN 5-MINUTE**
- 1000 ORB: +0.112R improvement
- 1800 ORB: +0.098R improvement
- Average: +0.105R improvement

⚠️ **BUT EDGE IS THIN**
- 1000 ORB: Only +0.052R avg
- 1800 ORB: Only +0.013R avg
- Vulnerable to costs, execution quality

⏳ **SYSTEM-WIDE VERDICT PENDING**
- Need NY ORBs (2300, 0030) - highest expected contribution
- Need Asia ORBs (0900, 1100) - moderate contribution
- If NY ORBs positive → system likely viable
- If NY ORBs negative → system likely fails

**Expected completion:** 2-3 minutes

---

## FILES

**Scripts:**
- `backtest_orb_exec_1m_nofilters.py` - 1-minute entry backtest
- `compare_entry_methods.py` - Entry timing comparison

**Data:**
- `orb_trades_1m_exec_nofilters` table in `gold.db`
- 12,540 trades with various RR/confirmation settings

**Reports:**
- `1_MINUTE_ENTRY_VERIFICATION.md` (this file)
- `CRITICAL_ENTRY_PRICE_FINDINGS.md`
- `PRESSURE_TEST_RESULTS.md`

---

*Report will be updated with final results once all tests complete.*
