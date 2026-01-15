# High-Confidence Trading Ruleset

**Created:** 2026-01-12
**Updated:** 2026-01-12 (Added Two Engines framework)
**Based on:** 2,845 backtested trades (2020-12-20 to 2026-01-10)
**Approach:** Conservative - only filter what clearly doesn't work

---

## Core Philosophy

**"Only exclude what we're SURE is broken"**

- Skip sessions that lose everywhere (high confidence)
- Trade profitable sessions without over-optimizing (avoid curve-fitting)
- Use simple rules that make logical sense
- Be honest about in-sample optimization risks

---

## TWO TRADING ENGINES (KEEP SEPARATE)

This ruleset uses **TWO DIFFERENT** trading frameworks. **Do not mix them.**

### Engine A: Liquidity / Inventory Logic
**Scope:** Session → Session relationships (Asia → London)
**Based on:** Prior-session inventory resolution
**Document:** `ASIA_LONDON_FRAMEWORK.md`

### Engine B: Outcome Momentum
**Scope:** ORB → ORB within same session (intra-Asia)
**Based on:** Prior ORB outcomes (WIN/LOSS) if closed
**Document:** `ORB_OUTCOME_MOMENTUM.md`

**See sections below for details on each engine.**

---

## High-Confidence Rules (START HERE)

### ✅ Trade These Sessions:

| Session | Entry | Stop | Target | Expected |
|---------|-------|------|--------|----------|
| **09:00 ORB** | 1 close outside | Half-ORB (midpoint) | 2.0 × ORB_range | -22.8R ⚠️ |
| **10:00 ORB** | 1 close outside | Half-ORB (midpoint) | 2.0 × ORB_range | +28.6R ✓ |
| **11:00 ORB** | 1 close outside | Half-ORB (midpoint) | 2.0 × ORB_range | +12.6R ✓ |
| **18:00 ORB** | 1 close outside | Half-ORB (midpoint) | 2.0 × ORB_range | +54.0R ✓✓ |

### ❌ Skip These Sessions:

| Session | Reason | R Saved |
|---------|--------|---------|
| **23:00 ORB** | Loses across all ORB sizes | +75.8R |
| **00:30 ORB** | Loses across all ORB sizes | +33.5R |

### Universal Settings:

- **Timeframe:** 5-minute bars
- **ORB Period:** First 5 minutes of session
- **Entry Confirmation:** 1 consecutive 5m close outside ORB
- **Stop Placement:** ORB midpoint (half-SL mode)
- **Buffer:** 0 ticks
- **Risk Definition:** 1R = ORB range size (high - low)
- **Reward:** 2.0R target (2.0 × ORB_range from entry)
- **Filters:** MAX_STOP = 100 ticks, ASIA_TP_CAP = 150 ticks

---

## Expected Performance

### High-Confidence Ruleset:

**Backtest Results:**
- **Trades:** 1,987
- **Total R:** +72.5R
- **Avg R/trade:** +0.036R
- **Improvement vs baseline:** +109.4R

**Conservative Real-World Expectation:**
- **50-80% of backtest:** +43.5R to +58.0R
- **Still profitable:** Turns -36.9R into profit
- **Adequate sample size:** ~2,000 trades

**Why Conservative?**
- In-sample optimization (we saw the outcomes)
- Market conditions change
- Execution slippage/commissions not included
- Psychological factors in live trading

---

## Medium-Confidence Add-Ons (Optional - Paper Trade First)

### Additional ORB Range Filters:

If you want to get aggressive (higher overfitting risk):

| Session | Additional Filter | Backtest Impact | Risk Level |
|---------|------------------|-----------------|------------|
| **09:00** | Only trade ORB > 50 ticks | +50.5R (42% WR) | ⚠️ MEDIUM (small sample: 64 trades) |
| **11:00** | Only trade ORB > 30 ticks | +32.2R | ⚠️ MEDIUM (240 trades) |

**Medium-Confidence Ruleset Results:**
- **Trades:** 1,316 (33% fewer)
- **Total R:** +155.2R
- **Potential extra:** +82.7R vs high-confidence

**⚠️ Warnings:**
- Fewer trades = higher variance
- Could be curve-fitted to historical data
- 09:00 filter based on only 64 trades (risky)
- **MUST paper trade before going live**

---

## Problem: 09:00 Session

**09:00 loses -22.8R in high-confidence ruleset!**

### Why Keep It?

Two options - pick one:

**Option A: Skip 09:00 Entirely (Ultra-Conservative)**
- Removes 497 losing trades
- Portfolio becomes: 1,490 trades, +95.3R
- Safest approach
- Only trade 10:00, 11:00, 18:00

**Option B: Use Medium-Confidence Filter (ORB > 50)**
- Only trades 64 times when ORB > 50 ticks
- Makes +27.7R with 42% WR
- Small sample = higher risk
- Could work if pattern is real (explosive days)

**Recommendation:** **Start with Option A** (skip 09:00 entirely). Add back later if you want to test the filter.

---

## Revised Ultra-Conservative Ruleset

### Trade Only These 3 Sessions:

| Session | Expected R | Win Rate | Trades |
|---------|-----------|----------|--------|
| **10:00 ORB** | +28.6R | 33.4% | 509 |
| **11:00 ORB** | +12.6R | 31.8% | 478 |
| **18:00 ORB** | +54.0R | 36.0% | 503 |
| **TOTAL** | **+95.3R** | **33.7%** | **1,490** |

**Skip:** 09:00, 23:00, 00:30

**Expected Real-World:** +57R to +76R (60-80% of backtest)

This is the **safest, highest-confidence approach.**

---

## ENGINE A: Asia → London Direction Filters (Liquidity Logic)

**Status:** Evidence-based, validated (+0.15R edge)
**Apply to:** 18:00 London ORB ONLY

### Core Rule:

**London direction is determined by how Asia handled prior inventory.**

### Prior Inventory Definition:
- Previous NY session high/low
- Previous London session high/low
- (Optional) Previous day high/low

### Trading Rules:

| Asia State | London Direction | Edge | Action |
|-----------|------------------|------|--------|
| Asia resolved prior HIGH | LONG ONLY | +0.15R | ✅ Trade London UP breaks |
| Asia resolved prior LOW | SHORT ONLY | +0.15R | ✅ Trade London DOWN breaks |
| Asia failed to resolve | BOTH directions | ~+0.10R | ✅ Standard London ORB |
| Asia clean trend (no inventory touch) | SKIP | Negative | ❌ Skip London entirely |

### 🚫 NEVER FADE:
- If Asia resolved prior HIGH → **DO NOT** trade London SHORT
- **Delta:** -0.37R (toxic)
- This is the worst pattern in the system

### Implementation:
1. **Before market open:** Identify prior NY/London highs and lows
2. **At 11:00 (end of Asia):** Did Asia touch/sweep any prior levels?
3. **At 18:00 London ORB:** Filter direction based on Asia resolution
4. **Do NOT add Asia ORB outcomes** (WIN/LOSS) - that's Engine B, not applicable here

**Full details:** See `ASIA_LONDON_FRAMEWORK.md`

---

## ENGINE B: Intra-Asia Outcome Momentum (ORB Correlations)

**Status:** Evidence-based, validated (2-5% WR improvement)
**Apply to:** 10:00 and 11:00 ORBs within Asia session

### Core Rule:

**When an early ORB wins, the next ORB in the same direction has better odds.**

### ⚠️ CRITICAL: Zero-Lookahead Requirement

**Only use if prior ORB trade is CLOSED.**
- If 09:00 still OPEN at 10:00 → Cannot use outcome
- If 10:00 still OPEN at 11:00 → Cannot use outcome

### 09:00 → 10:00 Correlations:

| 09:00 Outcome | 10:00 Direction | Win Rate | Delta | Action |
|---------------|----------------|----------|-------|--------|
| WIN (closed) | UP | 57.9% | +2.4% | ✅ Higher confidence |
| WIN (closed) | DOWN | 49.3% | -6.2% | ⚠️ Skip or reduce size |
| LOSS (closed) | UP | 52.7% | -2.8% | ~ Baseline |
| LOSS (closed) | DOWN | 53.8% | +1.1% | ~ Baseline |
| OPEN/UNKNOWN | Either | Baseline | — | Use standard stats |

**Baseline:** 10:00 UP = 55.5%, 10:00 DOWN = 52.7%

### 09:00 + 10:00 → 11:00 Combined Momentum:

| 09:00 | 10:00 | 11:00 Direction | Win Rate | Delta | Action |
|-------|-------|----------------|----------|-------|--------|
| WIN | WIN | UP | 57.4% | +3.0% | ✅✅ Best edge |
| WIN | WIN | DOWN | 48.6% | -3.7% | ❌ Avoid |
| LOSS | WIN | DOWN | 57.7% | +5.4% | ✅✅ Reversal |
| LOSS | LOSS | UP | 49.8% | -4.6% | ❌ Avoid |

**Baseline:** 11:00 UP = 54.4%, 11:00 DOWN = 52.3%

### Implementation:
1. **At 10:00:** Check if 09:00 trade is closed
   - If YES → Use outcome to adjust 10:00 confidence
   - If NO → Trade 10:00 using baseline stats
2. **At 11:00:** Check if BOTH 09:00 and 10:00 are closed
   - If YES → Use combined momentum pattern
   - If NO → Use simpler pattern or baseline

### Position Sizing Adjustment:
- **High edge patterns (57%+ WR):** Consider 1.5x size
- **Baseline patterns (52-55% WR):** Standard 1x size
- **Low edge patterns (<50% WR):** Skip or 0.5x size

**Full details:** See `ORB_OUTCOME_MOMENTUM.md`

---

## DO NOT MIX ENGINES

**Wrong Approach:**
- "Asia resolved prior HIGH AND 09:00 was a WIN → London LONG"
- This combines two different frameworks incorrectly

**Correct Approach:**
- **For London 18:00:** Use Engine A only → "Asia resolved prior HIGH → London LONG"
- **For Asia 10:00/11:00:** Use Engine B only → "09:00 WIN → 10:00 UP higher confidence"

**These are SEPARATE frameworks for DIFFERENT sessions.**

---

## Implementation Checklist

### Before Going Live:

- [ ] Verify gold.db has current data
- [ ] Understand 1R = ORB range (NOT entry-to-stop)
- [ ] Know ORB times in Brisbane local time
- [ ] Set up alerts for 10:00, 11:00, 18:00 ORBs
- [ ] Confirm MAX_STOP=100, ASIA_TP_CAP=150 in your code
- [ ] Paper trade for 20-30 trades minimum

### Daily Workflow:

#### Before Market Open (08:00-09:00):
- [ ] Identify prior NY high/low (from previous day)
- [ ] Identify prior London high/low (from previous day)
- [ ] Set alerts for 10:00, 11:00, 18:00 ORBs

#### At Each ORB Close (09:05, 10:05, 11:05, 18:05):
1. **Calculate ORB parameters:**
   - Note ORB high, low, range
   - Calculate 1R = ORB_range in ticks
   - Calculate target = entry ± (2.0 × ORB_range)
   - Calculate stop = ORB midpoint

2. **Apply Engine filters (if applicable):**
   - **For 10:00:** Check if 09:00 is closed → Use Engine B
   - **For 11:00:** Check if 09:00 + 10:00 closed → Use Engine B
   - **For 18:00:** Check Asia prior inventory resolution → Use Engine A

3. **Watch for entry:**
   - Wait for 1 consecutive 5m close outside ORB
   - Verify direction is allowed by filters (if any)
   - Enter at close price
   - Place stop at midpoint
   - Place target at entry ± 2R

4. **Manage trade:**
   - Let it run (no adjustments)
   - Accept outcome (WIN/LOSS)
   - **Record time of close** (needed for Engine B)
   - Log result with actual R-multiple

5. **Track performance:**
   - Compare actual vs expected (+95R target for high-confidence)
   - Track Engine A and Engine B performance separately
   - If significantly worse after 50 trades, reassess

---

## Key Insights from Analysis

### What Works:
1. ✅ **18:00 ORB is strongest** (+54R, 36% WR, works all ORB sizes)
2. ✅ **Skipping 23:00/00:30 saves 109R** (biggest single improvement)
3. ✅ **Half-SL at midpoint works** (buffer=0 is optimal)
4. ✅ **1R = ORB range** (professional definition, clean logic)

### What Doesn't Work:
1. ❌ **23:00 and 00:30 sessions lose everywhere**
2. ❌ **09:00 struggles without volatility filter**
3. ❌ **Buffers on half-SL hurt performance** (move stop toward ORB edge)

### Surprising Findings:
1. **Large ORB outliers (>50 ticks) are often profitable** (not noise!)
2. **Session personality matters more than ORB size** (each session different)
3. **18:00 prefers SMALL ORBs** (< 20 ticks = 41% WR)
4. **09:00 needs LARGE ORBs** (> 50 ticks = 42% WR)

---

## Honest Risk Disclosure

### This Ruleset Could Fail Because:

1. **In-Sample Optimization**
   - Rules found by looking at outcomes
   - "Cheating" - saw the answers before making rules
   - May not generalize to future

2. **Market Regime Change**
   - Patterns based on 2020-2026 data
   - Could shift with different volatility/trends
   - No guarantee of persistence

3. **Sample Size Issues**
   - Some filters based on <100 trades
   - High variance in small samples
   - Lucky streaks could disappear

4. **Execution Reality**
   - Slippage not included
   - Commissions not included
   - Psychological pressure in live trading
   - Can't always get filled at close price

### Why It Might Still Work:

1. **Logical Foundation**
   - Skipping 23:00/00:30 is obvious (they lose)
   - Session personalities make sense (volatility regimes)
   - Rules are simple (not over-optimized)

2. **Conservative Approach**
   - Only filtering clear losers
   - Not cherry-picking specific conditions
   - Large sample size (~1,500-2,000 trades)

3. **Realistic Expectations**
   - Expecting 50-80% of backtest
   - Still profitable even at 50%
   - Edge doesn't need to be huge

---

## Next Steps

### Phase 1: Paper Trading (30 days minimum)

**Goal:** Validate rules in live conditions

**Track:**
- Every trade (entry, exit, R-multiple)
- Session performance separately
- Compare to backtest expectations
- Note market conditions (volatility, trends)

**Success Criteria:**
- Total R within 50-80% of backtest expectations
- Win rates roughly match (±5%)
- No catastrophic drawdowns
- Can execute consistently

### Phase 2: Live Trading (Small Size)

**Start with 1 contract per trade:**
- Risk $50-100 per R (adjust to your comfort)
- Track same metrics as paper trading
- Plan to run 50-100 trades before scaling

**Red Flags to Watch:**
- Win rate < 25% (below backtest by >10%)
- Multiple large losing days (>-3R)
- Can't find entries (price gaps through ORB)
- Psychological pressure causing mistakes

### Phase 3: Optimization (After 3+ Months)

**Only if edge persists:**
- Test medium-confidence ORB filters
- Experiment with RR variations (1.5, 2.5, 3.0)
- Try different confirmation requirements
- Consider session-specific RR ratios

**DON'T:**
- Change rules after every losing trade
- Add complexity without reason
- Chase backtest perfection
- Ignore losing sessions' lessons

---

## Quick Reference Card

```
HIGH-CONFIDENCE RULES (Copy This)
==================================

TRADE:
  10:00 ORB | 11:00 ORB | 18:00 ORB

SKIP:
  09:00 ORB | 23:00 ORB | 00:30 ORB

ENTRY:
  1× 5m close outside ORB

STOP:
  ORB midpoint (half-SL, buffer=0)

TARGET:
  Entry ± (2.0 × ORB_range)

1R DEFINITION:
  ORB_high - ORB_low (in ticks)

EXPECTED:
  +95R (backtest)
  +57 to +76R (realistic)
  ~1,490 trades
```

---

## Files Reference

### Core Documents:
- `TRADING_RULESET.md` - This file (complete trading rules)
- `ASIA_LONDON_FRAMEWORK.md` - Engine A (liquidity logic)
- `ORB_OUTCOME_MOMENTUM.md` - Engine B (outcome correlations)
- `TERMINOLOGY_EXPLAINED.md` - Beginner-friendly explanations
- `R_DEFINITIONS.md` - Technical R definitions

### Analysis Scripts:
- `high_confidence_ruleset.py` - This analysis script
- `backtest_orb_exec_5mhalfsl_orbR.py` - Corrected backtest with ORB-R logic
- `test_session_orb_filters.py` - Full filter comparison (all options)

### Database:
- `orb_trades_5m_exec_orbr` - Results table
- `AUDIT_SUMMARY.md` - Complete backtest audit results

---

**Last Updated:** 2026-01-12 (Added Two Engines framework)
**Status:** Ready for paper trading
**Confidence Levels:**
- HIGH: 3-session baseline (10:00, 11:00, 18:00)
- MEDIUM: ORB size filters (09:00 > 50 ticks, 11:00 > 30 ticks)
- VALIDATED: Engine A (Asia → London, +0.15R)
- VALIDATED: Engine B (Intra-Asia momentum, +2-5% WR)
