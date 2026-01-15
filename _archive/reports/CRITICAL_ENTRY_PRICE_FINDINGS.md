# CRITICAL FINDING: ENTRY PRICE ASSUMPTION FLAW

**Date:** 2026-01-12
**Severity:** CRITICAL
**Impact:** ENTIRE SYSTEM PROFITABILITY IN QUESTION

---

## EXECUTIVE SUMMARY

The "worst-case execution" backtest (`backtest_worst_case_execution.py`) is NOT actually worst-case.

**Critical flaw:** It assumes entry at **exact ORB high/low**, which is unrealistic.

**Reality:** Market orders fill at **close price**, which can be significantly worse.

**Impact:** When tested with realistic entry (at close), system shows **NEGATIVE** expected value.

---

## EVIDENCE

### Worst-Case Backtest Results (Entry at ORB Edge)

| ORB  | Avg R Per Trade | Entry Assumption        |
|------|----------------|-------------------------|
| 0900 | **+0.266R**    | Entry = ORB high/low    |
| 1000 | +0.342R        | Entry = ORB high/low    |
| 1100 | +0.299R        | Entry = ORB high/low    |
| 1800 | +0.393R        | Entry = ORB high/low    |
| 2300 | +1.077R        | Entry = ORB high/low    |
| 0030 | +1.541R        | Entry = ORB high/low    |
| **System** | **+0.626R avg** | Theoretical best fill |

### Delayed Entry Test Results (Entry at Close Price)

| ORB  | Avg R Per Trade | Entry Assumption     | Degradation |
|------|----------------|----------------------|-------------|
| 0900 | **-0.137R**    | Entry = close price  | **-0.403R** |
| 1000 | -0.060R        | Entry = close price  | -0.402R     |
| 1100 | -0.070R        | Entry = close price  | -0.369R     |
| 1800 | -0.085R        | Entry = close price  | -0.478R     |
| 2300 | -0.825R        | Entry = close price  | -1.902R     |
| 0030 | -0.798R        | Entry = close price  | -2.339R     |
| **System** | **-0.329R avg** | Realistic market fill | **-0.955R diff** |

---

## THE PROBLEM

### What the Worst-Case Backtest Does

```python
# backtest_worst_case_execution.py (lines 115-130)

if direction == 'UP':
    entry = orb_high  # ← ASSUMES YOU GET THIS PRICE
    stop = orb_low
    target = entry + rr * risk
```

**This assumes:**
- You enter EXACTLY at the ORB high (for UP breakouts)
- You enter EXACTLY at the ORB low (for DOWN breakouts)

**How this happens in reality:**
- ORB closes at 09:05
- Price moves from 2045.5 (ORB high) to 2046.2 (close)
- You submit market order → fills at 2046.2 (NOT 2045.5)
- **Slippage: 7 ticks worse** than backtest assumption

### What the Delayed Entry Test Does

```python
# test_delayed_entry_robustness.py (lines 120-142)

# Find first close outside ORB
if bar['close'] > orb_high:
    signal_bar_idx = idx
    break

# Entry price = close of that bar
entry_price = entry_bar['close']  # ← REALISTIC FILL
```

**This is realistic:**
- Entry triggered by close outside ORB
- Order fills at that close price (market order assumption)
- Accounts for natural slippage from ORB edge to close

---

## WHY THIS MATTERS

### Degradation per Trade

**Average degradation from theoretical to realistic entry:**

- Asia ORBs (09:00, 10:00, 11:00): **~0.39R per trade**
- London ORB (18:00): **~0.48R per trade**
- NY ORBs (23:00, 00:30): **~2.1R per trade**

### System-Wide Impact

- **Theoretical (worst-case backtest):** +0.626R avg per trade
- **Realistic (delayed entry test):** -0.329R avg per trade
- **Difference:** **-0.955R per trade**

**Over 2893 trades (2 years):**
- Theoretical: +1816R total
- Realistic: **-952R total** (LOSING SYSTEM)

---

## ROOT CAUSE

### The Backtest Assumes Limit Orders

The entry assumption is equivalent to:

```
IF close > ORB high THEN
    Enter limit order at ORB high
    Hope it fills
END IF
```

**But this is not how ORB breakout trading works:**

1. You CANNOT enter at ORB high after price has already moved above it
2. A limit order at ORB high will NOT fill (price has moved away)
3. Reality requires a MARKET order → fills at current price (close)

### The Math

**Example: 0900 ORB UP breakout**

```
ORB high: 2045.5
ORB low:  2040.0
ORB range: 5.5 points = 55 ticks

Entry bar close: 2046.8 (13 ticks above ORB high)

Theoretical entry: 2045.5 (ORB high)
Realistic entry: 2046.8 (close)
Slippage: 13 ticks = 0.236R (13 / 55)

Stop: 2040.0
Theoretical risk: 5.5 points
Realistic risk: 6.8 points (23% larger)

With RR 1.0:
Theoretical target: 2051.0
Realistic target: 2053.6

If stopped out:
Theoretical loss: -1.0R
Realistic loss: -1.236R

Additional cost: 0.236R per trade
```

### Across 507 trades (0900 ORB):

- Theoretical: +135R
- **Realistic: -69R**
- **Difference: -204R**

---

## COMPARISON TO SLIPPAGE TEST

The slippage test (entry at close) shows identical baseline results to delayed entry test:

| ORB  | Delayed Entry (Baseline) | Slippage Test (Baseline) | Match? |
|------|--------------------------|--------------------------|--------|
| 0900 | -0.137R                  | -0.137R                  | ✅ Yes |
| 1000 | -0.060R                  | -0.060R                  | ✅ Yes |
| 1100 | -0.070R                  | -0.070R                  | ✅ Yes |
| 1800 | -0.085R                  | -0.085R                  | ✅ Yes |
| 2300 | -0.825R                  | -0.825R                  | ✅ Yes |
| 0030 | -0.798R                  | -0.798R                  | ✅ Yes |

**Both tests agree:** With realistic entry at close, system is NEGATIVE.

---

## WHAT ABOUT 1-TICK SLIPPAGE?

The slippage test shows:

| Test | System Avg R | Verdict |
|------|-------------|---------|
| 0 ticks (entry at close) | -0.329R | NEGATIVE |
| 1 tick slippage added | -0.355R | MORE NEGATIVE |
| 2 ticks slippage added | -0.402R | EVEN WORSE |

**This confirms:** Even WITHOUT additional slippage, the realistic entry assumption makes system unprofitable.

---

## POTENTIAL EXPLANATIONS

### 1. Entry Timing Is Everything

The backtest assumes you capture the ORB edge price. In reality:

- By the time close prints outside ORB → price has already moved
- This move IS the signal → but you pay for it with worse entry
- Typical overshoot: 5-20 ticks beyond ORB edge

### 2. High RR Setups Suffer Most

| ORB | RR | Theoretical Avg R | Realistic Avg R | Degradation |
|-----|----|--------------------|------------------|-------------|
| 0900| 1.0| +0.266R            | -0.137R          | -0.403R     |
| 0030| 4.0| +1.541R            | -0.798R          | -2.339R     |

**NY ORBs (RR 4.0) degrade by 2+ R per trade.**

Why? Larger targets require more follow-through. Entry slippage eats into already-thin edges.

### 3. Close-to-Close Is NOT Edge-to-Close

- **Worst-case backtest measures:** ORB edge → target
- **Reality measures:** Close price → target

If close is 10 ticks beyond ORB edge:
- You lose 10 ticks on entry
- Target is 10 ticks further away
- Stop is 10 ticks closer
- Effective risk increases, target becomes harder to hit

---

## LOSS CLUSTERING WITH REALISTIC ENTRY

The loss clustering analysis (using worst-case parameters with realistic entry) shows:

- **Max daily loss:** -6.0R (one day with 6 losing trades)
- **-3R+ days:** 49 days (9.4% of trading days)
- **-6R days:** 1 occurrence

**This exceeds most prop account limits (-3R daily max).**

---

## WHAT NEEDS TO HAPPEN

### Immediate Actions Required

1. ✅ **Acknowledge flaw:** Worst-case backtest entry assumption is unrealistic
2. ❌ **Rerun parameter sweep** with realistic entry (entry = close)
3. ❌ **Determine if ANY configurations are profitable** with realistic fills
4. ❌ **If profitable configs exist:**
   - Identify which ORBs survive
   - Find new optimal RR/SL/filters
   - Recalculate expected returns
5. ❌ **If NO configs are profitable:**
   - System is NOT deployable
   - Edge does not exist with realistic execution

### Options to Test

**Option 1: Limit Order Entry**
- Place limit order AT ORB high/low
- Wait for pullback to fill
- Test fill rate (how often does it fill?)
- Measure performance on filled trades only

**Option 2: Tighter Entry Criteria**
- Only enter if close is within X ticks of ORB edge
- Filter out trades with large overshoot
- Reduces trade count but improves entry quality

**Option 3: Scale Entry Points**
- 50% position at ORB edge (limit order)
- 50% position at close (market order)
- Average entry price between theoretical and realistic

**Option 4: Intrabar Entry**
- Use 1-minute bars instead of 5-minute
- Enter on FIRST 1m close outside ORB
- Earlier entry = closer to ORB edge

---

## HYPOTHESIS: WHY WORST-CASE STILL SHOWED PROFIT

The "worst-case" backtest used:
- **Worst-case intrabar resolution** (stop before target if both hit)
- **Best-case entry assumption** (fill at ORB edge)

These two effects partially offset:
- Worst-case resolution: Reduces wins
- Best-case entry: Improves entry quality

**Net result:** Showed positive, but used conflicting assumptions.

**Truth:** You cannot have both.
- If you get perfect fills (ORB edge) → intrabar resolution matters less
- If you get realistic fills (close) → even with worst-case resolution, system fails

---

## VALIDATION: OTHER TESTS

### Delayed Entry Results

| Delay | System Avg R | Interpretation |
|-------|-------------|----------------|
| +0 bars | -0.329R | Entry at close (realistic) |
| +1 bar  | -0.180R | Better! (price retraces) |
| +2 bars | -0.258R | Worse again |

**Interesting finding:** +1 bar delay IMPROVES performance vs immediate entry.

**Why?** Waiting 5 minutes allows price to retrace slightly, giving better entry.

**This suggests:** Immediate entry at breakout close is TOO aggressive.

---

## WHAT THIS MEANS FOR DEPLOYMENT

### Current Status

| What We Thought | Reality Check |
|----------------|---------------|
| System profitable (+1816R) | System NEGATIVE (-952R) with realistic fills |
| All 6 ORBs tradeable | Unknown - need retest with realistic entry |
| Worst-case tested | Entry assumption was best-case, not worst |
| Ready for deployment | **NOT READY** - requires complete revalidation |

### Path Forward

1. **STOP:** Do not deploy current system
2. **RETEST:** Complete parameter sweep with realistic entry
3. **REASSESS:** Determine if profitable configurations exist
4. **REDESIGN:** If needed, explore alternative entry methods
5. **REVALIDATE:** Full pressure-test suite with new parameters

**Estimated time to resolution:** 1-2 weeks of testing

---

## LESSONS LEARNED

### What "Worst-Case" Really Means

A truly worst-case backtest must pessimize EVERY dimension:

- ✅ Intrabar resolution (stop before target)
- ❌ Entry price (assumed best, not worst)
- ❌ Entry timing (assumed immediate, not delayed)
- ❌ Slippage (not included)
- ❌ Spread (not included)
- ❌ Failed fills (not considered)

**We only tested 1 of 6 dimensions.**

### Realistic vs Pessimistic

| Assumption | Realistic | Pessimistic | We Used |
|-----------|-----------|-------------|---------|
| Entry price | Close | Close + 2 ticks | **ORB edge** |
| Intrabar fill | Random | Stop first | **Stop first** ✅ |
| Slippage | 1 tick | 2 ticks | **0 ticks** |
| Spread | 1 tick | 2 ticks | **0 ticks** |

**We were pessimistic in 1 area, optimistic in 3 others.**

---

## FINAL VERDICT

❌ **SYSTEM IS NOT VALIDATED FOR DEPLOYMENT**

The "worst-case execution" backtest used unrealistic entry assumptions that inflated performance by ~0.95R per trade.

**When corrected for realistic entry:**
- System shows NEGATIVE expected value
- All 6 ORBs appear unprofitable
- Requires complete revalidation

**DO NOT DEPLOY** until realistic-entry parameter sweep is complete and shows positive edge.

---

## NEXT STEPS (PRIORITY ORDER)

1. ✅ Document this finding (this file)
2. ❌ Create `backtest_realistic_entry.py` - Entry at close price
3. ❌ Run full 252-config sweep with realistic entry
4. ❌ Compare results to worst-case backtest
5. ❌ If any configs are profitable:
   - Update canonical parameters
   - Rerun all pressure tests
   - Update all documentation
6. ❌ If NO configs are profitable:
   - Test alternative entry methods (limit orders, tighter criteria, etc.)
   - Consider fundamental strategy redesign
7. ❌ Write final deployment decision report

**Expected timeline:** 5-7 days of continuous testing

---

*This is a SHOWSTOPPER finding. All previous conclusions are invalidated until this is resolved.*
