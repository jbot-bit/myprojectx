# GAP FILL TIMING ANALYSIS - WHEN TO FADE

## Executive Summary

Based on analysis of 424 filled gaps in MGC futures, this guide provides **actionable timing rules** for fading gaps.

**Key Finding**: Gap size determines optimal entry timing. Small gaps (<1.0 ticks) fill immediately 59% of the time, while large gaps (>2.0 ticks) only fill immediately 34% of the time.

---

## Critical Statistics

### Overall Timing Distribution

- **53.8%** of gaps fill in first 5 minutes (1 bar)
- **62.7%** of gaps fill within 15 minutes (3 bars)
- **68.9%** of gaps fill within 30 minutes (6 bars)
- **71.9%** of gaps fill within 60 minutes (12 bars)
- **46.2%** of gaps take LONGER than 5 minutes to fill

### By Gap Size

| Gap Size | Immediate Fill (5 min) | Within 15 min | Within 60 min | Median Fill Time |
|----------|------------------------|---------------|---------------|------------------|
| 0.0-0.5 ticks (Tiny) | 59.0% | 70.0% | 76.0% | 5 minutes |
| 0.5-1.0 ticks (Small) | 59.8% | 66.7% | 74.5% | 5 minutes |
| 1.0-2.0 ticks (Medium) | 48.6% | 54.1% | 73.0% | 10 minutes |
| 2.0-5.0 ticks (Large) | 34.4% | 46.9% | 59.4% | 22 minutes |
| >5.0 ticks (Huge) | 12.5% | 18.8% | 25.0% | 788 minutes |

---

## Entry Strategies by Gap Size

### STRATEGY 1: IMMEDIATE FADE (Gaps 0.0-1.0 ticks)

**When to use**: Gaps less than 1.0 ticks

**Entry rule**: Enter immediately at gap open (within first 5 minutes)

**Why it works**: 59.3% of small gaps fill immediately

**Trade setup**:
- Entry: Market order at gap open
- Stop loss: Entry ± (1.5 × gap size)
- Target: Previous close (100% gap fill)
- Time limit: Exit if not filled within 60 minutes

**Expected outcomes**:
- 59.3% fill within 5 minutes
- 68.9% fill within 15 minutes
- Low risk, high probability

**Adverse excursion**: Small gaps that don't fill immediately can run 4-26 ticks against you before filling

---

### STRATEGY 2: WAIT FOR PULLBACK (Gaps 1.0-2.0 ticks)

**When to use**: Gaps between 1.0 and 2.0 ticks

**Entry rule**: Wait 5-15 minutes for initial move away from fill, then enter on pullback toward fill price

**Why it works**: 51.4% of medium gaps run away first before filling

**Trade setup**:
- Watch first 5-15 minutes
- Wait for price to move AWAY from fill (in gap direction)
- Enter on first pullback toward fill price
- Stop loss: Entry ± (2.0 × gap size)
- Target: Previous close (100% gap fill)
- Time limit: Exit if not filled within 60 minutes

**Expected outcomes**:
- You'll MISS the 48.6% that fill immediately
- You'll CATCH the 51.4% that run away first
- 73.0% fill within 60 minutes total
- Medium risk, good probability

**Adverse excursion**: Medium gaps that delay can run 5-18 ticks against you, typically 33-138% of gap size

---

### STRATEGY 3: CONFIRMATION FADE (Gaps 2.0-5.0 ticks)

**When to use**: Gaps between 2.0 and 5.0 ticks

**Entry rule**: Wait 30 minutes for confirmation that gap isn't continuing

**Why it works**: Only 34.4% fill immediately; high risk of continuation

**Trade setup**:
- Watch first 30 minutes
- Only enter if gap has NOT continued strongly
- Enter if price shows clear rejection of gap direction
- Stop loss: Entry ± (2.5 × gap size)
- Target: 50-75% of gap fill (be conservative, don't expect full fill)
- Time limit: Exit if not filled within 90 minutes

**Expected outcomes**:
- You'll MISS the 34.4% that fill immediately
- 59.4% fill within 60 minutes (including immediate)
- High risk, lower probability
- Consider partial targets

**Adverse excursion**: Large delayed gaps can run 4-216 ticks against you, up to 480% of gap size (very dangerous!)

---

### STRATEGY 4: DON'T FADE (Gaps >5.0 ticks)

**When to use**: Gaps larger than 5.0 ticks

**Entry rule**: **DON'T ENTER**

**Why**: Only 12.5% fill immediately; likely a continuation move

**Alternative**: Trade in the DIRECTION of the gap instead of fading it

**Risk**: Extremely high - these gaps take 788 minutes median to fill (13+ hours)

---

## Decision Tree

```
STEP 1: Measure gap size at market open
│
├─ 0.0-0.5 ticks  → IMMEDIATE FADE (59% immediate fill)
├─ 0.5-1.0 ticks  → IMMEDIATE FADE (60% immediate fill)
├─ 1.0-2.0 ticks  → WAIT FOR PULLBACK (49% immediate, 51% delayed)
├─ 2.0-5.0 ticks  → WAIT 30 MINUTES (34% immediate, 66% delayed)
└─ >5.0 ticks     → DON'T FADE (12% immediate, 88% continuation)

STEP 2: Execute chosen strategy (see above)

STEP 3: Monitor for time-based exit
- If gap doesn't fill within expected timeframe, exit
- Don't let small loss become large loss
```

---

## Risk Management Rules

### Universal Rules (All Gap Sizes)

1. **Never risk more than 1% of account per trade**
2. **Set stop loss BEFORE entering**
3. **Use time-based stops**: If gap doesn't fill in expected timeframe, exit
4. **Don't re-enter after stop-out**: If stopped on a gap, don't try again on same gap
5. **Avoid news events**: Never fade gaps during FOMC, NFP, or major economic releases

### Gap-Size Specific Stops

- **Tiny/Small gaps (<1.0 ticks)**: Stop at 1.5× gap size
- **Medium gaps (1.0-2.0 ticks)**: Stop at 2.0× gap size
- **Large gaps (2.0-5.0 ticks)**: Stop at 2.5× gap size
- **Huge gaps (>5.0 ticks)**: Don't trade

### Time-Based Stops

- **Small gaps**: Exit if not filled within 60 minutes
- **Medium gaps**: Exit if not filled within 60 minutes
- **Large gaps**: Exit if not filled within 90 minutes

### Position Sizing

Calculate position size based on stop loss distance:

```
Position Size = (Account Risk Amount) / (Stop Loss Distance in dollars)

Example:
- Account: $10,000
- Risk per trade: 1% = $100
- Gap: 0.8 ticks UP (gap from 2000.0 to 2000.8)
- Strategy: Immediate fade (short at 2000.8)
- Stop: 1.5× gap = 1.2 ticks above entry = 2002.0
- Stop distance: 1.2 ticks = $12 per contract
- Position size: $100 / $12 = 8 contracts (round down)
```

---

## Performance Tracking

Track your results by gap size category to refine your filters:

| Gap Size | Trades | Win % | Avg RR | Notes |
|----------|--------|-------|--------|-------|
| 0.0-0.5 | | | | |
| 0.5-1.0 | | | | |
| 1.0-2.0 | | | | |
| 2.0-5.0 | | | | |

**Adjust your filters based on live performance**:
- If small gaps aren't filling as expected, tighten size filter
- If medium gaps are causing too many stops, switch to waiting for pullback
- If large gaps are too risky, skip them entirely

---

## Key Insights from Adverse Excursion Analysis

### What Happens in Delayed Fills?

When gaps DON'T fill immediately (46.2% of all gaps), they exhibit concerning behavior:

**Tiny gaps (0.0-0.5 ticks)**:
- Median 19.5 bars to fill (98 minutes)
- Can run 4-26 ticks against you (133-2000% of gap size!)
- Example: 0.2 tick gap ran 31 ticks away before filling

**Small gaps (0.5-1.0 ticks)**:
- Median 32 bars to fill (160 minutes)
- Can run 13-23 ticks against you (175-383% of gap size)
- Example: 0.6 tick gap ran 23 ticks away before filling

**Medium gaps (1.0-2.0 ticks)**:
- Median 15.5 bars to fill (78 minutes)
- Can run 5-26 ticks against you (33-260% of gap size)
- Example: 1.3 tick gap ran 18 ticks away before filling

**Large gaps (2.0-5.0 ticks)**:
- Median 31 bars to fill (155 minutes)
- Can run 4-216 ticks against you (15-480% of gap size!)
- Example: 4.5 tick gap ran 216 ticks away before filling (devastating)

### Critical Lesson

**Even small gaps can have massive adverse excursion if they don't fill immediately.**

This is WHY:
- Small gaps get immediate fade (minimize adverse excursion risk)
- Medium gaps wait for pullback (avoid initial adverse move)
- Large gaps wait 30 minutes or skip (avoid catastrophic adverse excursion)

---

## Common Mistakes to Avoid

1. **Fading large gaps immediately**: Large gaps (>2.0 ticks) only fill immediately 34% of the time. The other 66% will hurt.

2. **Not using stops**: Small gaps can run 20+ ticks against you. Always use stops.

3. **Revenge trading**: If stopped out on a gap, don't re-enter. Move on.

4. **Ignoring time limits**: If gap doesn't fill in expected timeframe, your thesis is wrong. Exit.

5. **Trading gaps during news**: News-driven gaps behave differently. Skip them.

6. **Fading huge gaps**: Gaps >5 ticks almost never fill quickly. Don't trade them.

7. **Over-sizing**: Adverse excursion can be 2-5× the gap size. Size accordingly.

---

## Quick Reference Guide

**I see a gap at market open. What do I do?**

1. **Measure gap size** (current price - previous close)
2. **Consult this table**:

| Gap Size | Action | Entry Timing | Stop | Expected Fill Time |
|----------|--------|--------------|------|-------------------|
| 0.0-0.5 ticks | IMMEDIATE FADE | Now | 1.5× gap | 5 minutes |
| 0.5-1.0 ticks | IMMEDIATE FADE | Now | 1.5× gap | 5 minutes |
| 1.0-2.0 ticks | WAIT PULLBACK | 5-15 min | 2.0× gap | 10 minutes |
| 2.0-5.0 ticks | WAIT 30 MIN | 30 min | 2.5× gap | 22 minutes |
| >5.0 ticks | DON'T FADE | N/A | N/A | 13+ hours |

3. **Execute chosen strategy**
4. **Monitor position and exit at target or time limit**

---

## Conclusion

**The right time to fade a gap depends on gap size.**

- **Small gaps (<1.0 ticks)**: Fade immediately. They fill fast.
- **Medium gaps (1.0-2.0 ticks)**: Wait for pullback. They run away first.
- **Large gaps (>2.0 ticks)**: Wait 30 minutes or skip. High risk.
- **Huge gaps (>5.0 ticks)**: Don't fade. Trade with the gap instead.

**Most profitable approach**: Focus on gaps <1.0 ticks with immediate fade strategy. These have the highest win rate and lowest adverse excursion risk.

---

## Files Generated

- `analyze_gap_fill_timing.py` - Main timing distribution analysis
- `analyze_gap_adverse_excursion.py` - Adverse excursion analysis
- `gap_fill_analysis.csv` - Source data (424 filled gaps)
- `GAP_FILL_TIMING_GUIDE.md` - This guide

## How to Update

To regenerate this analysis with new data:

```bash
python analyze_gap_fill_timing.py
python analyze_gap_adverse_excursion.py
```
