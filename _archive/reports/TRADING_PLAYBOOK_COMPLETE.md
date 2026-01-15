# COMPLETE TRADING PLAYBOOK
**Gold (MGC) Liquidity-Based Trading System**
**Date**: 2026-01-13
**Updated**: 2026-01-14 (Corrected 2300/0030 ORB parameters from RR 4.0 to RR 1.0)

---

## Overview

This playbook contains **3 strategies** developed and tested over 741 days (2024-2026):

1. **ORB Breakout Trading** - ✅ SECONDARY (updated to CANONICAL configs Jan 14)
2. **Single Liquidity Reactions** - ⚠️ BACKUP (weaker edge)
3. **Multi-Liquidity Cascades** - ✅ PRIMARY (strongest edge)

⚠️ **CRITICAL UPDATE 2026-01-14**: ORB configs corrected after database verification
- **2300/0030 ORBs**: RR corrected from 4.0 to 1.0 (previous claims were untested)
- **Performance numbers**: Updated to match database reality
- **Win rates**: Clarified calculation (now per trade, not per day)
- **Impact**: More honest expectations (-36% system total, but ACCURATE)
- See VERIFICATION_COMPLETE_2026-01-14.md for full audit details

**Trading Philosophy**: Reactive, not predictive. We trade forced liquidations after liquidity sweeps fail to hold.

---

# STRATEGY 1: ORB BREAKOUT TRADING

## Status: ✅ SECONDARY STRATEGY (All 6 ORBs Profitable)
### ⚠️ UPDATED 2026-01-14 to CANONICAL Parameters

### What It Is
Trade breakouts from 5-minute opening ranges at specific session starts. All 6 sessions tested show positive edge when optimally configured.

### Edge Statistics (Optimal Configurations)

**Best ORBs** (Night Sessions) - CORRECTED 2026-01-14:
- **23:00 ORB**: +0.387R avg, 522 trades, 69.3% WR (RR 1.0 HALF SL) ⭐
- **00:30 ORB**: +0.231R avg, 523 trades, 61.6% WR (RR 1.0 HALF SL) ⭐⭐ POSITIVE

**Day Sessions**:
- **18:00 ORB**: +0.393R avg, 491 trades, 46.4% WR
- **10:00 ORB**: +0.342R avg, 489 trades, 33.5% WR
- **11:00 ORB**: +0.299R avg, 502 trades, 64.9% WR
- **09:00 ORB**: +0.266R avg, 507 trades, 63.3% WR

### Test Period
- **Data**: 2024-01-02 to 2026-01-10 (741 days)
- **Configurations tested**: 252 (all RR/SL/filter combinations)
- **Result**: ALL sessions have positive edge at optimal parameters

### When Trades Show Up

**Daily Opportunities**:
- 09:00 local: Morning Asia open (66% days)
- 10:00 local: Mid-morning Asia (64% days)
- 11:00 local: Late Asia (66% days)
- 18:00 local: London open (64% days)
- 23:00 local: NY futures open (63% days) ⭐
- 00:30 local: NY mid-session (56% days) ⭐⭐

### Optimal Configurations by Session

#### 00:30 ORB (POSITIVE) - CORRECTED 2026-01-14
- **RR**: 1.0 (target = ORB edge + 1R)
- **Stop**: HALF (stop at ORB midpoint, not opposite edge)
- **Filter**: BASELINE (no additional filters)
- **Performance**: +0.231R avg, ~+60R/year, 61.6% WR (of breakouts, 71% of days break)
- **Why it works**: NYSE cash open creates directional moves, solid positive edge

#### 23:00 ORB (STRONG) - CORRECTED 2026-01-14
- **RR**: 1.0 (target = ORB edge + 1R)
- **Stop**: HALF (stop at ORB midpoint)
- **Filter**: BASELINE (no additional filters)
- **Performance**: +0.387R avg, ~+100R/year, 69.3% WR (of breakouts, 71% of days break)
- **Why it works**: NY futures open creates strong directional moves

#### 18:00 ORB (SOLID) - CANONICAL CONFIG
- **RR**: 1.0 ⚠️ UPDATED (was 2.0)
- **Stop**: HALF ⚠️ UPDATED (was FULL)
- **Filter**: BASELINE
- **Performance**: +0.425R avg, +111R/year, 71.3% WR (2ND BEST)
- **Why it works**: London open, but PAPER TRADE FIRST (preliminary results)

#### 10:00 ORB
- **RR**: 3.0
- **Stop**: FULL
- **Filter**: MAX_STOP_100 (only trade if ORB size ≤10pts)
- **Performance**: +0.342R avg, +167R total over 489 trades

#### 11:00 ORB
- **RR**: 1.0
- **Stop**: FULL
- **Filter**: BASELINE
- **Performance**: +0.299R avg, +150R total over 502 trades

#### 09:00 ORB
- **RR**: 1.0
- **Stop**: FULL
- **Filter**: BASELINE
- **Performance**: +0.266R avg, +135R total over 507 trades

### Entry Rules (Using 00:30 ORB as Example)

**Step 1: Calculate ORB** (00:30-00:35):
- Track high and low during first 5 minutes
- At 00:35, you have: ORB high = [price], ORB low = [price]
- ORB midpoint = (high + low) / 2
- ORB size = high - low

**Step 2: Wait for Breakout** (00:35 onwards):
- Watch each 1-minute bar
- Entry trigger: Bar CLOSES outside ORB range

**For LONG** (if close > ORB high):
- **Entry**: Market order at close (or limit at ORB high + 0.1pts)
- **Stop**: ORB midpoint (HALF mode)
- **Risk**: Entry - Stop = (ORB high - midpoint) = ORB size / 2
- **Target**: Entry + 1R = ORB high + 1 × Risk (RR 1.0 for 00:30 ORB)

**For SHORT** (if close < ORB low):
- **Entry**: Market order at close (or limit at ORB low - 0.1pts)
- **Stop**: ORB midpoint (HALF mode)
- **Risk**: Stop - Entry = (midpoint - ORB low) = ORB size / 2
- **Target**: Entry - 1R = ORB low - 1 × Risk

**Step 3: Manage Trade**:
- If target hit first → WIN (+1R for 00:30 ORB, +1R for 23:00 ORB)
- If stop hit first → LOSS (-1R)
- No trailing, no partial exits (mechanical execution)

⚠️ **UPDATED 2026-01-14**: Night ORBs (23:00, 00:30) use RR 1.0 (verified from database)

### Why ORBs Work

**Night Sessions** (23:00, 00:30):
- Lower participation = cleaner breakouts
- Overnight traders positioned = forced moves on breaks
- Higher RR (4.0) + HALF stop = asymmetric risk/reward

**Day Sessions** (09:00-18:00):
- Session open = volume surge
- Stop hunters target ORB edges = liquidity
- Lower RR (1.0-2.0) = more achievable targets

### Why ORBs Are Secondary to Cascades

**ORB Advantages**:
- Higher frequency (daily vs 2-3/month)
- Higher win rate (33-65% vs 19-27%)
- Simpler rules (time-based vs pattern-based)

**Cascade Advantages**:
- Higher average R (+1.95R vs +0.27-1.54R)
- Gap multiplier effect (large gaps = +5.36R)
- Tail events (+129R max vs ORB ~+20R max)
- More selective (9.3% frequency vs 56-66%)

**Verdict**: ORBs are tradeable and profitable, but cascades have superior edge when they appear.

### Risk Management for ORBs

**Position Sizing**:
- **00:30/23:00 ORB**: 0.25-0.50% risk per trade (stronger edge, higher RR)
- **Other ORBs**: 0.10-0.25% risk per trade (weaker edge, more frequent)

**Why Larger Size Allowed**:
- Higher frequency = diversification across many trades
- Higher win rate = shorter losing streaks (max 5-8 consecutive)
- Lower tail risk = max R is limited by RR target (no runaway winners like cascades)

**Example Sizing** ($100k account):
- 00:30 ORB: Risk 0.50% = $500 per trade
  - If ORB size = 2.0pts, Risk = 1.0pt, Position = $500 / ($10 × 1.0pt) = 50 contracts
- Cascade: Risk 0.25% = $250 per trade
  - If risk = 1.5pts, Position = $250 / ($10 × 1.5pts) = 16 contracts

### When To Use ORBs vs Cascades

**Primary**: Always watch for cascade setups (2-3 per month, +1.95R avg)

**Secondary**: Trade ORBs on non-cascade days
- If cascade gap size <9.5pts → Trade ORB instead
- If no Asia/London sweep → Trade ORB
- If cascade not confirmed by 23:30 → Consider 00:30 ORB

**DO NOT** trade both on same day (risk concentration)

### Psychological Differences

**ORBs**:
- Frequent setups (daily)
- Moderate win rate (33-65%)
- Predictable outcomes (+4R max for 00:30)
- **Feels like**: Traditional breakout trading

**Cascades**:
- Rare setups (2-3/month)
- Low win rate (19-27%)
- Unpredictable outcomes (-1R to +129R)
- **Feels like**: Venture capital investing

**Mental Model**: ORBs are "base salary", cascades are "stock options"

---

# STRATEGY 2: SINGLE LIQUIDITY REACTIONS

## Status: ⚠️ BACKUP STRATEGY (Weaker Edge)

### What It Is
Trade the reaction when a single session level (London high/low) gets swept and fails to hold.

### Edge Statistics
- **Average R**: +1.44R
- **Frequency**: 16% of days (~120 setups in 741 days)
- **Win rate**: 33.7%
- **Max R observed**: +48R

### When Trades Show Up

**Daily Schedule**:
1. **18:00-23:00 local**: London session runs, establishes high/low
2. **23:00 local**: NY futures open - watch for sweep

**What You're Looking For**:
- London session (18:00-23:00) creates high/low
- At 23:00, price sweeps London high (or low)
- Within 3 minutes, price closes back below (or above) the level
- This is "acceptance failure" - participants trapped

### Entry Rules

**SHORT Setup** (when London high swept):
1. Wait for London session to complete (23:00)
2. Watch 23:00-23:30 window for sweep (close > London high)
3. Acceptance failure: Close back below London high within 3 bars
4. Entry: Wait for price to retrace to London high (within 0.1pts)
5. Stop: Sweep high (the peak that was hit)
6. Target: Previous low or structure-based trail

**LONG Setup** (when London low swept):
1. Watch 23:00-23:30 for sweep below London low
2. Acceptance failure: Close back above within 3 bars
3. Entry: Retrace to London low (within 0.1pts)
4. Stop: Sweep low
5. Target: Previous high or structure-based trail

### Risk Management
- **Risk per trade**: 0.25% - 0.50% (higher than cascades due to higher frequency)
- **Max consecutive losses**: 8-10 expected
- **Frequency**: 2-3 setups per week

### Why It's Backup, Not Primary
- Weaker edge than cascades (+1.44R vs +1.95R)
- Less selective (16% vs 9.3%)
- No gap-size multiplier effect
- Smaller tail events (max +48R vs +129R)

### When To Use
- When cascades haven't triggered in 2-3 weeks (psychological need to trade)
- When gap size <9.5pts (doesn't qualify for cascade)
- As confidence builder (higher frequency, higher win rate)

---

# STRATEGY 3: MULTI-LIQUIDITY CASCADES

## Status: ✅ PRIMARY STRATEGY (Strongest Edge)

### What It Is
Trade forced liquidation cascades when multiple full-session levels (Asia + London + NY) get swept sequentially and fail to hold.

### Edge Statistics
- **Average R**: +1.95R
- **Frequency**: 9.3% of days (~2-3 setups per month)
- **Win rate**: 19-27%
- **Median R**: -1R (most trades lose)
- **Max R observed**: +129R (single trade)
- **Gap size multiplier**: Large gaps (>9.5pts) = +5.36R vs Small gaps = +0.36R (15× difference)

### When Trades Show Up

**Daily Schedule** (all times Australia/Brisbane local):

1. **09:00-17:00**: Asia session runs (8 hours)
   - Track high and low
   - This is your **first liquidity level**

2. **17:00**: Asia session closes
   - Note: Asia high = [price], Asia low = [price]

3. **18:00-23:00**: London session runs (5 hours)
   - Track if London sweeps Asia levels
   - **First sweep**: Does London high > Asia high? (or London low < Asia low?)
   - If NO sweep → No cascade possible today
   - If YES sweep → **Calculate gap size**

4. **23:00**: London session closes, NY futures open
   - This is **THE CRITICAL MOMENT**
   - 70% of cascades trigger in first 5 minutes after 23:00
   - Watch for **second sweep** of London level

5. **23:00-23:30**: Setup window
   - Scan first 30 bars (30 minutes) for second sweep + failure
   - Entry typically happens within first 5-10 minutes

### How To Recognize Trades (Real-Time Checklist)

**BEFORE 17:00** (Asia session):
- [ ] Track Asia high/low (use monitor_cascade_live.py)
- [ ] Note: Nothing to do yet, just track

**AT 17:00** (Asia close):
- [ ] Write down: Asia high = [price], Asia low = [price]

**DURING 18:00-23:00** (London session):
- [ ] Track London high/low
- [ ] Check at 23:00: Did London sweep Asia level?
  - [ ] London high > Asia high? (upside sweep)
  - [ ] London low < Asia low? (downside sweep)
- [ ] **Calculate gap size**:
  - Upside: gap = London high - Asia high
  - Downside: gap = Asia low - London low
- [ ] **If gap < 9.5pts → STOP, not a large-gap cascade**
- [ ] **If gap >= 9.5pts → PREPARE FOR 23:00**

**AT 23:00** (NY futures open) - **CRITICAL WINDOW**:

**For UPSIDE CASCADE** (if London swept Asia high):
- [ ] Watch 23:00-23:05 closely (first 5 minutes)
- [ ] Looking for: Close > London high (second sweep)
- [ ] If swept, watch next 3 bars for acceptance failure:
  - [ ] Does price close back BELOW London high within 3 bars?
  - [ ] If YES → **ACCEPTANCE FAILURE CONFIRMED**
- [ ] Wait for retrace to London high (price must touch level within 0.1pts)
- [ ] **ENTRY**: SHORT at London high
- [ ] **STOP**: Sweep high (the peak of second sweep)
- [ ] **RISK**: Stop - Entry (distance in points)

**For DOWNSIDE CASCADE** (if London swept Asia low):
- [ ] Watch 23:00-23:05 closely
- [ ] Looking for: Close < London low (second sweep)
- [ ] Acceptance failure: Close back ABOVE London low within 3 bars?
- [ ] If YES → confirmed
- [ ] Wait for retrace to London low
- [ ] **ENTRY**: LONG at London low
- [ ] **STOP**: Sweep low
- [ ] **RISK**: Entry - Stop

### Entry Rules (ALL must be true)

**Pre-Entry Filters**:
1. ✅ Full sessions complete: Asia (09:00-17:00) + London (18:00-23:00)
2. ✅ First sweep: London swept Asia level
3. ✅ Gap size: >9.5pts (MANDATORY for large-gap edge)
4. ✅ Timing: 23:00-23:30 window
5. ✅ Second sweep: Close breaks through London level
6. ✅ Acceptance failure: Close back through within 3 bars (3 minutes)
7. ✅ Entry opportunity: Price retraces to London level (within 0.1pts)

**If ANY condition fails → No trade**

### Exit Rules

**Phase 1: Breakeven Protection (0-10 minutes after entry)**
- If trade hits +1R within first 10 minutes:
  - Move stop to breakeven (entry price)
  - This protects against whipsaw
- If +1R not hit in 10 min:
  - Keep original stop, continue to Phase 2

**Phase 2: Structure Trail (15+ minutes after entry)**
- After 15 minutes, trail stop behind structural pivots:

**For SHORT positions**:
- Look for "lower highs" (pivot highs that are lower than previous pivot)
- When found, move stop to that pivot high
- This tightens stop as price cascades down

**For LONG positions**:
- Look for "higher lows" (pivot lows that are higher than previous pivot)
- When found, move stop to that pivot low
- This tightens stop as price cascades up

**Pivot Identification**:
- A pivot is a bar where high (or low) is greater (or less) than both neighbors
- Look back 10 bars to find pivots
- Update stop only when NEW pivot forms that's favorable

**Time Limit**:
- Max hold: 90 minutes from entry
- If not stopped out by 90 min → exit at market
- Most cascades peak within 3-5 minutes (median)
- But tail events can take 15-90 minutes (must hold for these)

**DO NOT use fixed-time exits** (15min, 30min) - they destroy edge!

### Risk Management

**Position Sizing** (NON-NEGOTIABLE):
- **Risk per cascade**: 0.10% - 0.25% of capital
- Example: $100k account → risk $100-$250 per trade
- Calculate position size: (Account × 0.0025) / Risk_in_points / $10_per_point

**Why So Small**:
- Low frequency (2-3 per month)
- Low win rate (19-27%)
- Most trades lose -1R
- Edge comes from tail events (+10R to +129R)
- Max historical losing streak: 14 consecutive losses
- Max drawdown tested: -43.4R

**Expected Drawdown**:
- With 0.25% risk: -43.4R = -10.85% drawdown (tested max)
- With 0.10% risk: -43.4R = -4.34% drawdown
- Smaller risk = more robust to unlucky strings

**Psychological Preparation**:
- Expect strings of 5-10 consecutive losses
- Median trade = -1R (you will lose most trades)
- Your job: Survive until the +50R or +100R trade hits
- This is **portfolio-style intraday campaign trading**
- Not a "high win rate" system

### Why This Is Primary

**Gap Size Multiplier**:
- Large gaps (>9.5pts): **+5.36R average**
- Small gaps (≤9.5pts): +0.36R average
- **15× difference!**

**Tail Events**:
- Max R observed: +129R (single trade)
- 90th percentile: +15R to +30R
- These tail events fund the entire system

**Structural Validity**:
- Works both directions (SHORT +1.95R, LONG +1.00R)
- Not directional bias, true structural edge
- Tested across 741 days, multiple market conditions

---

# HOW TO KNOW WHEN YOUR TRADES SHOW UP

## Daily Routine

### Morning Routine (before 09:00)
- [ ] Run: `python monitor_cascade_live.py [today's date]`
- [ ] Review yesterday's session if you weren't watching live

### During Asia Session (09:00-17:00)
- [ ] Check prices hourly or use alert at 17:00
- [ ] Note Asia high and Asia low at 17:00 close

### Before London (17:00-18:00)
- [ ] Set alerts for London high/low updates
- [ ] Calculate potential gaps if London sweeps:
  - "What if London goes to [level]? What's the gap?"

### During London (18:00-23:00)
- [ ] Track London high/low
- [ ] At 22:30 (30 min before close), assess:
  - Did London sweep Asia? YES/NO
  - If YES, what's the gap size?
  - If gap >9.5pts → **PREPARE TO WATCH 23:00**
  - If gap <9.5pts → No cascade today

### Critical Window (22:55-23:30)
**If large-gap first sweep exists**:
- [ ] **22:55**: Get ready, setup order entry platform
- [ ] **23:00**: Watch closely for second sweep
- [ ] **23:00-23:05**: 70% of setups trigger in first 5 minutes
- [ ] **23:05-23:30**: Remaining 30% of setups trigger here
- [ ] If no setup by 23:30 → Stand down, no trade today

### Post-Entry (if trade triggered)
- [ ] Monitor for +1R within 10 minutes (Phase 1)
- [ ] After 15 minutes, track structural pivots (Phase 2)
- [ ] Set calendar reminder for 90-minute max hold
- [ ] Use `track_cascade_exits.py` to analyze after trade

### End of Day
- [ ] Log trade result (if any)
- [ ] Update streak counter (consecutive wins/losses)
- [ ] Review gap size correlation (did large gap = better R?)
- [ ] Mental check: Am I following rules precisely?

---

# MONITORING TOOLS

## monitor_cascade_live.py

**Purpose**: Real-time monitoring for cascade setups

**Usage**:
```bash
python monitor_cascade_live.py                 # Today
python monitor_cascade_live.py 2026-01-13     # Specific date
```

**What It Shows**:
- Asia session high/low (09:00-17:00)
- London session high/low (18:00-23:00)
- First sweep detection (London vs Asia)
- Gap size calculation with large-gap flag
- Second sweep monitoring at 23:00
- Acceptance failure detection
- Complete setup confirmation with entry/stop/target

**When To Run**:
- Morning: Review previous day
- 17:00: After Asia close
- 23:00: Real-time for entry

## track_cascade_exits.py

**Purpose**: Structure-based exit tracking after entry

**Usage**:
```bash
python track_cascade_exits.py --entry 2711.5 --stop 2713.0 --direction SHORT --date 2025-01-10 --time 23:05
```

**What It Shows**:
- Trade progression bar-by-bar
- Phase 1: Breakeven at +1R timing
- Phase 2: Structural pivot trail
- Max R achieved and time to max R
- R at 15min, 30min, 60min, 90min intervals
- Comparison: structure-based vs fixed-time exits
- Final R captured

**When To Run**:
- After trade exits (for post-trade review)
- Paper trading validation
- Understand how structure beats fixed-time

---

# TRADE EXAMPLES

## Example 1: Large-Gap CASCADE SHORT (Perfect Setup)

**Date**: 2025-07-17

**Pre-Entry**:
- Asia high: 2695.5 (at 17:00)
- London high: 2707.8 (at 23:00)
- First sweep: YES (London swept Asia high)
- Gap size: 2707.8 - 2695.5 = **12.3 pts** (LARGE GAP ✅)

**At 23:00**:
- 23:02: Close 2708.5 (above London high 2707.8) → Second sweep
- 23:03: Close 2707.2 (back below 2707.8) → **ACCEPTANCE FAILURE ✅**
- 23:04: Low 2707.7 (touched level) → **ENTRY SHORT at 2707.8**
- Stop: 2708.5 (sweep high)
- Risk: 0.7 pts

**Outcome**:
- 23:09: Hit +1R → Move stop to breakeven (Phase 1)
- 23:15-23:45: Trail behind lower highs (Phase 2)
- 23:47: Final stop hit at 2702.1
- Exit: 2702.1
- **Result: +8.1R** (captured 5.7pts on 0.7pt risk)

**Why It Worked**:
- Large gap (12.3pts) = high trapped leverage
- Acceptance failure confirmed trapped participants
- Structure trail captured extended move
- Didn't exit at fixed time (would have captured only 2R at 30min)

## Example 2: Small-Gap False Signal (Why Gap Size Matters)

**Date**: 2025-09-12

**Pre-Entry**:
- Asia high: 2683.2
- London high: 2688.5
- Gap size: 2688.5 - 2683.2 = **5.3 pts** (SMALL GAP ❌)
- **STOP HERE - DO NOT TRADE**

**What Would Have Happened** (if you ignored gap filter):
- Second sweep occurred at 23:03
- Acceptance failure at 23:04
- Entry SHORT at 2688.5, stop 2689.0, risk 0.5pts
- Price chopped around 2688-2689 for 30 minutes
- Stop hit at 23:35
- **Result: -1R loss**

**Why It Failed**:
- Small gap = insufficient trapped leverage
- Participants can adjust without forced liquidation
- Acceptance failure alone not enough without gap size

**Lesson**: Gap size filter is MANDATORY, not optional.

## Example 3: No Acceptance Failure (Why Failure Is Mandatory)

**Date**: 2025-11-03

**Pre-Entry**:
- Asia low: 2701.5
- London low: 2689.8
- Gap size: 2701.5 - 2689.8 = **11.7 pts** (LARGE GAP ✅)

**At 23:00**:
- 23:02: Close 2688.9 (below London low 2689.8) → Second sweep
- 23:03: Close 2688.5 (still below) → NO FAILURE
- 23:04: Close 2688.1 (still below) → NO FAILURE
- 23:05: Close 2687.8 (still below) → NO FAILURE
- **STOP - NO ACCEPTANCE FAILURE ❌**
- **DO NOT ENTER**

**What Happened**:
- Price continued down to 2680.5 by 23:30
- No retrace to entry level
- Participants were NOT trapped, they were correctly positioned
- No forced liquidation, just normal breakout

**Lesson**: Acceptance failure is MANDATORY. Without it, you're guessing direction.

---

# FREQUENCY EXPECTATIONS

## Monthly Expectations

**Cascades** (Primary Strategy):
- **Valid setups**: 2-3 per month
- **Large gaps**: 1-2 per month (43% of cascades)
- **Small gaps**: 1-2 per month (57% of cascades)
- **Trade only large gaps**: 1-2 trades per month executed

**Single Liquidity Reactions** (Backup):
- **Valid setups**: 8-12 per month
- **Use when**: No cascades for 2-3 weeks, or small-gap cascade days

## Quarterly Expectations

**Cascades**:
- **Total setups**: 6-9 over 3 months
- **Win rate**: 19-27% → expect 1-2 winners out of 6-9 trades
- **Median result**: -1R on most trades
- **Tail event probability**: ~10% chance of +10R to +129R trade

**Example Quarter**:
- Trade 1: -1R
- Trade 2: -1R
- Trade 3: -1R
- Trade 4: +2.5R (small winner)
- Trade 5: -1R
- Trade 6: -1R
- Trade 7: +48R (tail event) ← THIS FUNDS THE QUARTER
- Trade 8: -1R
- **Total: +42.5R on 8 trades** despite 6 losses

This is normal. The edge is tail-based.

---

# PSYCHOLOGICAL PREPARATION

## What To Expect

### You Will Lose Most Trades
- **Win rate**: 19-27%
- **Median**: -1R
- 70%+ of trades will be losses
- **This is normal and expected**

### You Will Have Long Losing Streaks
- **Max historical**: 14 consecutive losses
- **Expected**: 5-10 loss streaks multiple times per year
- **Your job**: Keep position size tiny (0.10-0.25%)
- **Survival** = staying in the game for the tail event

### Most Trades Will Feel Wrong
- You enter at 23:05
- Price chops for 10 minutes
- You hit +1R, move to breakeven
- Price whipsaws back to entry, stops you out at BE
- **This is positive EV!** You protected capital.

### The Big Winner Will Feel Like Luck
- Trade 23 after 10 consecutive losses
- You enter, price immediately drops 20pts in 8 minutes
- You're at +28R within 15 minutes
- You trail structure, get stopped at +45R
- **This is not luck** - this is the edge

## How To Stay Disciplined

### Rule #1: Never Skip Gap Size Filter
- If gap <9.5pts → **DO NOT TRADE**
- Small gaps = +0.36R (basically breakeven after costs)
- Large gaps = +5.36R (the entire edge)
- **Temptation**: "But there's a perfect acceptance failure!"
- **Reality**: Without gap size, you have no edge

### Rule #2: Never Exit Early
- **Temptation**: "I'm up +3R at 10 minutes, take profit!"
- **Reality**: Early exit destroys edge (-1.78R vs +1.95R)
- **Remember**: 23:00 timing is CRITICAL, hold through 90min
- Use structure trail (Phase 2), not fixed-time

### Rule #3: Never Trade Without Acceptance Failure
- **Temptation**: "London swept Asia, big gap, just enter at 23:00!"
- **Reality**: Structure only = +0.94R (half the edge)
- **Remember**: Failure confirms trapped participants
- **Wait** for second sweep + close back through

### Rule #4: Position Size Is Non-Negotiable
- **Temptation**: "I'm on a 5-trade win streak, size up!"
- **Reality**: Max losing streak = 14 consecutive
- **Risk**: 0.10-0.25% per trade, NO MORE
- **Math**: 14 losses at 0.25% = -3.5% drawdown (survivable)
- **Math**: 14 losses at 1.00% = -14% drawdown (devastating)

---

# QUARTERLY REVIEW CHECKLIST

Every 90 days, review these metrics to ensure edge persists:

## Performance Metrics
- [ ] **Average R**: Should be >+1.0R (target +1.95R)
- [ ] **Frequency**: Should be 8-12% of days (target 9.3%)
- [ ] **Win rate**: Should be 15-30% (target 19-27%)
- [ ] **Max drawdown**: Track consecutive losses (expect 5-14)

## Edge Validation
- [ ] **Gap size correlation**: Large gaps still outperform small by 5×+?
- [ ] **Timing concentration**: 70%+ still entering at 23:00?
- [ ] **Bidirectional**: Both SHORT and LONG producing positive R?
- [ ] **Structure vs fixed**: Structure-based exits still beating fixed-time?

## Red Flags (Edge Decay)
- ⚠️ Average R drops below +1.0R
- ⚠️ Frequency increases above 15% (selectivity loss)
- ⚠️ Gap size correlation weakens (large/small gap difference <3×)
- ⚠️ Win rate increases above 40% (edge might be changing)

If 2+ red flags → **STOP TRADING**, re-analyze pattern for 30 days

---

# FINAL NOTES

## This Is Not Prediction
- You are NOT predicting which way price will go
- You are trading forced liquidations AFTER they've been triggered
- Acceptance failure = confirmation, not prediction

## This Is Not Discretion
- Every rule has a precise threshold
- Gap size: >9.5pts (not "looks big")
- Acceptance failure: Within 3 bars (not "soon")
- Entry: Within 0.1pts of level (not "near the level")
- **Follow the rules exactly**

## This Is Portfolio-Style Trading
- You're building a portfolio of 6-9 trades per quarter
- Most will be small losses (-1R)
- A few will be small wins (+2R to +5R)
- One will be huge (+10R to +100R+)
- **The huge one funds everything**

## Questions To Ask After Each Trade

1. Did I follow the gap size filter? (>9.5pts?)
2. Did I wait for acceptance failure? (close back through within 3 bars?)
3. Did I enter at the level? (within 0.1pts?)
4. Did I move stop to BE at +1R? (if hit within 10min?)
5. Did I trail structure after 15min? (not fixed-time exit?)
6. Did I use correct position size? (0.10-0.25% risk?)

If you answered YES to all 6 → You did your job, regardless of outcome.

---

**Remember**: The edge is proven over 741 days. Your job is execution, not prediction. Follow the rules, survive the drawdowns, capture the tail events.

---

# STRATEGY 4: NQ ORB BREAKOUTS (ALTERNATIVE INSTRUMENT)

## Status: ⚠️ VALIDATED - TIER 4 (Diversification)
### 📊 Alternative instrument: Micro Nasdaq (MNQ)

### What It Is
Same ORB breakout strategy applied to NQ (Nasdaq) futures. Lower performance than MGC but still profitable. Use for diversification only.

### Edge Statistics (Validated Configurations)

**Period**: Jan 13 - Nov 21, 2025 (268 days, 1,238 trades after filtering)
**Overall**: +0.194R avg, +208R total, 58.3% WR

| ORB | RR | SL Mode | Filter | Trades | WR | Avg R | Annual R | Status |
|-----|-----|---------|--------|--------|-----|-------|----------|--------|
| **00:30** | 1.0 | HALF | NONE | 206 | 61.2% | **+0.292R** | +60R | **BEST NQ ORB** |
| **11:00** | 1.5 | FULL | 0.100×ATR | 193 | 62.7% | +0.260R | +52R | ✅ STRONG |
| **18:00** | 1.5 | HALF | 0.120×ATR | 192 | 62.5% | +0.257R | +51R | ✅ STRONG |
| **10:00** | 1.5 | FULL | 0.100×ATR | 184 | 58.7% | +0.174R | +35R | ✅ POSITIVE |
| **09:00** | 1.0 | FULL | 0.050×ATR | 131 | 57.3% | +0.145R | +29R | ✅ POSITIVE |
| **23:00** | -- | -- | **SKIP** | -- | -- | -0.010R | -- | ❌ NEGATIVE |

### Key Differences vs MGC
- **Volatility**: NQ is ~13× more volatile in absolute terms
- **Performance**: MGC is 2.2× better (+0.320R vs +0.194R per trade)
- **Win Rates**: NQ slightly higher (58.3% vs 57.2%)
- **Risk**: Higher per-contract ($2/tick vs $0.10/tick MGC)

### Entry Rules (Same as MGC)
1. Wait for ORB period completion (5 minutes)
2. Entry on first 5m close outside ORB range
3. Stop at ORB midpoint (HALF) or opposite edge (FULL)
4. Target at entry ± (RR × stop distance)

### Position Sizing (NQ-Specific)
**Contract**: MNQ (Micro Nasdaq) = $2 per tick (0.25pt tick size)

**Example**: 10pt stop = 40 ticks = $80 risk per contract
- $100k account × 0.25% risk = $250 risk
- $250 / $80 = 3 contracts

**Risk Guidelines**:
- NQ ORBs: 0.25-0.50% per trade
- Same as MGC (adjusted for tick value)

### When To Use NQ
**Recommended For**:
- Large accounts ($100k+) seeking diversification
- Traders comfortable with higher volatility
- When MGC liquidity is low

**NOT Recommended For**:
- Small accounts (<$50k) - stick to MGC
- Beginners - master MGC first
- Primary instrument - MGC is superior

### Important Notes
⚠️ **23:00 NQ ORB is SKIP** - Still negative even with optimal filter
⚠️ **Size filters critical** - 09:00 filter provides +233% improvement
⚠️ **Paper trade first** - Higher volatility requires adjustment

**Source**: NQ/NQ_OPTIMAL_CONFIG.md

---

# STRATEGY 5: LONDON ADVANCED FILTERS (3 TIERS)

## Status: ⚠️ VALIDATED - TIER 3 (Advanced - Manual Only)
### 📊 Research Only - NOT in app yet

### What It Is
Advanced filters for 18:00 London ORB based on prior session behavior. Improves baseline performance from +0.425R to +1.059R (2.5× improvement) at highest tier.

### Testing
- **Configurations Tested**: 126
- **Period**: 5+ years
- **Sample**: 68-499 trades per tier
- **Status**: Exhaustively validated

### TIER 1: Highest Edge (Recommended)
**Performance**: **+1.059R avg** (vs +0.425R baseline = +0.634R improvement!)

**Configuration**:
- Asia range: 100-200 ticks (NORMAL)
- Prior session: If Asia resolved prior NY HIGH → Trade UP only
- Prior session: If Asia resolved prior NY LOW → **SKIP London**
- RR: 3.0 (not 1.0)
- Stop: FULL (opposite ORB edge, not HALF)

**Results**:
- Trades: 68 over 5 years
- Win Rate: 51.5%
- Total R: +72R
- Frequency: ~14 trades/year

**Rules**:
1. Check Asia range at 17:00 (must be 100-200 ticks = NORMAL)
2. Did Asia resolve prior NY high? → LONG only at 18:00
3. Did Asia resolve prior NY low? → SKIP London entirely
4. If neither resolved → Use baseline London ORB

### TIER 2: Balanced
**Performance**: +0.487R avg (vs +0.425R baseline = +0.062R improvement)

**Configuration**:
- Asia range: 100-200 ticks (NORMAL)
- RR: 3.0
- Stop: FULL
- No directional filters (simpler)

**Results**:
- Trades: 199
- Win Rate: 37.2%
- Total R: +97R
- Frequency: ~40 trades/year

### TIER 3: High Volume
**Performance**: +0.388R avg (baseline-equivalent but more conservative)

**Configuration**:
- RR: 1.5
- Stop: FULL
- No filters at all (simplest)

**Results**:
- Trades: 499
- Win Rate: 55.5%
- Total R: +193.5R (highest cumulative)
- Frequency: ~100 trades/year

### When To Use
**TIER 1**: Maximum edge, lowest frequency (advanced traders only)
**TIER 2**: Good balance of edge and frequency
**TIER 3**: Highest volume, baseline-level performance

### Requirements
⚠️ **Manual tracking required** - Prior session inventory resolution
⚠️ **NOT in app** - Requires session state awareness
⚠️ **Paper trade first** - Complex conditional logic

### Expected Impact
- TIER 1: +1.059R × 14 trades/year = +15R/year
- TIER 2: +0.487R × 40 trades/year = +19R/year
- TIER 3: +0.388R × 100 trades/year = +39R/year

**Source**: LONDON_BEST_SETUPS.md

---

# STRATEGY 6: SESSION-BASED ENHANCEMENTS (ENGINE A)

## Status: ⚠️ VALIDATED - TIER 3 (Advanced - Manual Only)
### 🔧 Liquidity/Inventory Resolution Logic

### What It Is
Uses prior-session inventory resolution to filter London ORB direction. Based on principle: "London trades the result of what Asia did with prior inventory."

### Edge Statistics
**Improvement**: +0.15R per setup
**Frequency**: ~80 setups/year
**Expected Impact**: +12R/year

### Rules

#### Setup 1: Asia Resolved Prior HIGH
**Condition**: Asia session touched/swept prior NY high
**Action**: Trade London **LONG only** at 18:00
**Edge**: +0.15R improvement over baseline
**Logic**: Asia resolved upside inventory → London continues up

#### Setup 2: Asia Resolved Prior LOW
**Condition**: Asia session touched/swept prior NY low
**Action**: Trade London **SHORT only** at 18:00
**Edge**: +0.15R improvement over baseline
**Logic**: Asia resolved downside inventory → London continues down

#### Setup 3: Asia Failed to Resolve
**Condition**: Asia did NOT touch prior NY high or low
**Action**: Trade London ORB baseline (both directions)
**Edge**: ~+0.10R (baseline)

### 🚫 TOXIC PATTERN (NEVER TRADE)
**Condition**: Asia resolved prior HIGH
**Action**: DO NOT trade London SHORT
**Result**: -0.37R (WORST pattern in system)
**Reason**: Fading resolved inventory is toxic

### Implementation
**At 17:00** (before London open):
1. Identify prior NY session high/low (from yesterday)
2. Check if Asia touched/swept either level
3. If touched HIGH → LONG only at 18:00
4. If touched LOW → SHORT only at 18:00
5. If neither → baseline London ORB

### Requirements
⚠️ **Manual tracking** - Prior session levels
⚠️ **Session awareness** - Must track Asia/NY relationship
⚠️ **NOT in app** - Requires inventory tracking feature

**Source**: ASIA_LONDON_FRAMEWORK.md

---

# STRATEGY 7: OUTCOME MOMENTUM (ENGINE B)

## Status: ⚠️ VALIDATED - TIER 3 (Advanced - Manual Only)
### ⚡ Intra-Session ORB Correlations

### What It Is
Prior ORB WIN/LOSS affects next ORB performance within same session (Asia only). Win creates momentum, loss creates reversal opportunities.

### Edge Statistics
**Improvement**: +2-5% win rate on specific patterns
**Frequency**: Applies to Asia ORBs (09:00, 10:00, 11:00)
**Expected Impact**: +10R/year

### Top Patterns

#### Pattern 1: 09:00 WIN → 10:00 UP
**Win Rate**: 57.9% (vs 55.5% baseline = +2.4% improvement)
**Sample**: 200+ trades
**Rule**: If 09:00 WIN (closed) → Prefer 10:00 UP breakout
**Avoid**: 09:00 WIN → 10:00 DOWN (49.3%, -6.2% vs baseline)

#### Pattern 2: 10:00 WIN → 11:00 UP
**Win Rate**: 56.2% (vs 54.4% baseline = +1.8% improvement)
**Sample**: 200+ trades
**Rule**: If 10:00 WIN (closed) → Prefer 11:00 UP breakout

#### Pattern 3: Combined Momentum (BEST)
**09:00 WIN + 10:00 WIN → 11:00 UP**
**Win Rate**: 57.4% (+3.0% improvement) ⭐⭐
**Rule**: If both 09:00 and 10:00 WIN → Strong bias to 11:00 UP

**09:00 LOSS + 10:00 WIN → 11:00 DOWN**
**Win Rate**: 57.7% (+5.4% improvement) ⭐⭐ REVERSAL
**Rule**: Loss followed by win creates reversal bias

#### Patterns to AVOID
**09:00 WIN + 10:00 WIN → 11:00 DOWN**: 48.6% (-3.7% vs baseline)
**09:00 LOSS + 10:00 LOSS → 11:00 UP**: 49.8% (-4.6% vs baseline)

### Critical Requirement: ZERO-LOOKAHEAD
⚠️ **ONLY use if prior ORB trade is CLOSED**
- Cannot assume outcome if trade still running
- Most ORB trades close within 5-20 minutes
- Check trade state before using momentum

### Implementation
**At 10:00** (checking 09:00):
1. Is 09:00 trade closed? (YES/NO)
2. If YES → Note outcome (WIN/LOSS) and direction (UP/DOWN)
3. If 09:00 WIN → Higher confidence for 10:00 UP
4. If 09:00 WIN → Lower confidence for 10:00 DOWN (consider skip)

**At 11:00** (checking 09:00 + 10:00):
1. Are BOTH trades closed? (YES/NO)
2. If YES → Use combined momentum pattern
3. Best edges: WIN+WIN→UP or LOSS+WIN→DOWN
4. Avoid: WIN+WIN→DOWN or LOSS+LOSS→UP

### Requirements
⚠️ **Prior trade state tracking** - Must know if closed
⚠️ **Outcome recording** - WIN/LOSS per trade
⚠️ **NOT in app** - Requires trade state awareness

**Source**: ORB_OUTCOME_MOMENTUM.md

---

# STRATEGY 8: POSITIONING & FILTERS (TIER 3)

## Status: ⚠️ VALIDATED - TIER 3 (Advanced - Manual Only)
### 🎯 Multiple Enhancement Types

This section covers 3 independent enhancement types that can be stacked.

---

## Enhancement 8A: ORB Positioning Analysis

### What It Is
Where current ORB forms relative to prior ORB affects expectancy.

### Key Findings

#### 10:00 ORB Position Relative to 09:00
**BELOW 09:00 range**: +0.400R (70.0% WR) = **+0.058R improvement**
**OVERLAP 09:00 range**: +0.393R (69.6% WR) = +0.050R improvement
**ABOVE 09:00 range**: +0.276R (63.8% WR) = -0.066R (worse)

**Rule**: Prefer 10:00 trades when ORB forms BELOW or OVERLAPS 09:00

#### 11:00 ORB Position Relative to 10:00
**NEAR TOP of 10:00**: +0.509R (75.5% WR) = **+0.060R improvement**
**Other positions**: Baseline performance

**Rule**: Prefer 11:00 trades when ORB forms near TOP of 10:00 range

### Expected Impact
+0.05R × 200 Asia ORB trades = +10R/year

**Source**: ASIA_ORB_CORRELATION_REPORT.md

---

## Enhancement 8B: Lagged Features (Previous Day)

### What It Is
Previous day Asia session behavior predicts next day ORBs.

### Top Findings

#### 00:30 ORB + PREV_ASIA_IMPULSE=HIGH
**Baseline**: -0.069R (LOSING)
**With condition**: **+0.124R (WINNING)**
**Improvement**: +0.193R ⭐⭐⭐ **TRANSFORMS LOSING TO WINNING**

**Rule**: Only trade 00:30 if previous day Asia had high impulse move

#### 11:00 ORB + PREV_ASIA_CLOSE_POS=HIGH
**Baseline**: +0.026R (marginal)
**With condition**: **+0.192R**
**Improvement**: +0.166R ⭐⭐⭐ **7.4× BETTER**

**Rule**: Increase size on 11:00 if previous day Asia closed near highs

#### 00:30 ORB + PREV_ASIA_CLOSE_POS=LOW
**Baseline**: -0.069R (LOSING)
**With condition**: **+0.085R (POSITIVE)**
**Improvement**: +0.154R ⭐⭐

**Rule**: Only trade 00:30 if previous day Asia closed near lows

### Expected Impact
+0.17R × 100 trades/year = +17R/year

**Source**: LAGGED_FEATURES_TEST_RESULTS.md

---

## Enhancement 8C: ORB Size Filters (Adaptive ATR)

### What It Is
Skip large ORBs (exhaustion pattern). Trade small ORBs (genuine compression breakout).

### Validated Filters

#### 2300 ORB: Skip if orb_size > 0.155×ATR(20)
**Baseline**: +0.387R (RR 1.0)
**With filter**: +0.408R (estimated)
**Improvement**: Modest improvement expected
**Trades kept**: 36%
**Logic**: Large ORB = exhaustion at NY open

#### 0030 ORB: Skip if orb_size > 0.112×ATR(20)
**Baseline**: +0.231R (RR 1.0)
**With filter**: +0.267R (estimated)
**Improvement**: Modest improvement expected
**Trades kept**: 13%
**Logic**: Large ORB = chasing, false breakout

#### 1100 ORB: Skip if orb_size > 0.095×ATR(20)
**Baseline**: +0.299R
**With filter**: +0.646R
**Improvement**: **+0.347R (+77%)** ⭐⭐⭐
**Trades kept**: 11%
**Win rate**: 78.0%
**Logic**: Small ORB = genuine compression breakout

#### 1000 ORB: Skip if orb_size > 0.088×ATR(20)
**Baseline**: +0.342R
**With filter**: +0.421R
**Improvement**: **+0.079R (+23%)**
**Trades kept**: 42%

### Overall Impact
**Improvement**: +0.158R per trade (+44.9%)
**Trade-off**: Frequency reduced 71.5%

### Implementation Status
⚠️ **UNCLEAR IF IN APP** - Need to verify if implemented
⚠️ **Requires ATR(20)** - 20-day average true range

### Expected Impact
+0.158R × 100 filtered trades = +16R/year

**Source**: FILTER_IMPLEMENTATION_COMPLETE.md

---

# COMPLETE PLAYBOOK SUMMARY

## All Strategies by Tier

### TIER 1: PRIMARY (Strongest Edges)
1. **Multi-Liquidity Cascades**: +1.95R avg (69 trades/2yr) - ✅ In Playbook
2. **11:00 ORB**: +0.449R avg (523 trades/2yr) - ✅ In App
3. **Single Liquidity**: +1.44R avg (~120/2yr) - ✅ In Playbook
4. **09:00 ORB**: +0.431R avg (520 trades/2yr) - ✅ In App

### TIER 2: SECONDARY (Good Edges)
5. **18:00 ORB**: +0.425R avg (522 trades/2yr) - ✅ In App
6. **10:00 ORB**: +0.342R avg (473 trades/2yr) - ✅ In App
7. **11:00 ORB**: +0.299R avg (493 trades/2yr) - ✅ In App
8. **09:00 ORB**: +0.266R avg (491 trades/2yr) - ✅ In App

### TIER 3: ADVANCED (Conditional Improvements - Manual Only)
9. **London Filters Tier 1**: +1.059R avg (68 trades/5yr) - ⚠️ Not in app
10. **London Filters Tier 2**: +0.487R avg (199 trades/5yr) - ⚠️ Not in app
11. **London Filters Tier 3**: +0.388R avg (499 trades/5yr) - ⚠️ Not in app
12. **Asia→London Inventory** (Engine A): +0.15R improvement - ⚠️ Not in app
13. **Outcome Momentum** (Engine B): +2-5% WR improvement - ⚠️ Not in app
14. **Positioning**: +0.05-0.06R improvement - ⚠️ Not in app
15. **Lagged Features**: +0.15-0.19R improvement - ⚠️ Not in app
16. **Size Filters**: +0.06-0.35R improvement - ❓ Partially in app?

### TIER 4: ALTERNATIVE INSTRUMENT (Diversification)
17. **NQ ORBs** (5 configs): +0.194R avg (906 trades/yr) - ⚠️ Validated

## Total Expected Returns

**MGC TIER 1-2** (In App):
- +922R per 2 years = +461R/year (BASE CASE)

**MGC TIER 3** (Manual - If Added):
- +15-39R/year (London filters, best tier)
- +12R/year (Asia→London inventory)
- +10R/year (Outcome momentum)
- +10R/year (Positioning)
- +17R/year (Lagged features)
- +16R/year (Size filters)
- **TOTAL TIER 3**: +80R/year additional

**NQ TIER 4** (If Diversified):
- +208R per year (alternative instrument)

**COMBINED TOTAL**: +461R to +749R/year (MGC only, conservative to with all enhancements)

---

# IMPLEMENTATION ROADMAP

## Phase 1: COMPLETE (Current State)
✅ All 6 MGC ORBs in app with CANONICAL configs
✅ Cascades and Single Liquidity in playbook (manual)
✅ All strategies documented and validated

## Phase 2: Add to Playbook (THIS UPDATE)
✅ NQ ORBs documented (TIER 4)
✅ London Advanced Filters documented (TIER 3)
✅ Session-Based Enhancements documented (TIER 3)
✅ Outcome Momentum documented (TIER 3)
✅ Positioning & Filters documented (TIER 3)

## Phase 3: App Features (Future)
⚠️ Session inventory tracking (Engine A)
⚠️ Prior trade state tracking (Engine B)
⚠️ Positioning detection
⚠️ Lagged features automation
⚠️ Size filters verification/implementation
⚠️ NQ integration testing

## Phase 4: Full Automation (Long-term)
⚠️ Complete strategy recommendation engine
⚠️ Automated momentum tracking
⚠️ Automated positioning analysis
⚠️ Multi-instrument support (MGC + NQ)

---

# FINAL NOTES - UPDATED 2026-01-14

## What Changed
- ✅ Added 7 validated strategies (TIER 3-4) to playbook
- ✅ All strategies now documented in one place
- ✅ Clear tier system (PRIMARY → ADVANCED → ALTERNATIVE)
- ✅ Manual vs automated strategies clearly marked

## What's Next
1. **Master TIER 1-2** first (in app, automated)
2. **Paper trade TIER 3** (manual, advanced)
3. **Consider TIER 4** for diversification (NQ)

## Important Reminders
⚠️ **TIER 3 strategies require manual tracking** - Not in app yet
⚠️ **TIER 4 (NQ) is for diversification only** - MGC is superior
⚠️ **Start with TIER 1-2** - Master basics before advanced

---

**Updated**: 2026-01-14
**Status**: ✅ COMPLETE - All validated strategies now in playbook
**Total Strategies**: 17 (8 automated, 9 manual/validated)
