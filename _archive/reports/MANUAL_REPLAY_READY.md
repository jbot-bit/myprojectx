# MANUAL REPLAY VALIDATION - READY TO EXECUTE

**Date:** 2026-01-12
**State Under Test:** 0030 ORB - NORMAL + D_MED + HIGH close + HIGH impulse
**Expected Edge:** 70% UP-favored, +44.5 tick median tail skew (post_60m)

---

## STATUS: DATA PREPARED, AWAITING MANUAL ANALYSIS

**Files generated:**
- ✅ 22 CSV files (1m + 5m bars for 11 valid dates)
- ✅ `replay_0030_analysis_template.csv` (blank template for observations)
- ✅ `visualize_replay_example.py` (text visualization helper)
- ✅ Example visualization run (2026-01-09 shown above)

**Dates ready for replay:**
1. 2026-01-09 ✅
2. 2025-12-31 ✅
3. 2025-09-19 ✅
4. 2025-09-03 ✅
5. 2025-08-28 ✅
6. 2025-08-05 ✅
7. 2025-07-24 ✅
8. 2025-07-22 ✅
9. 2025-07-17 ✅
10. 2025-03-13 ✅
11. 2025-02-25 ✅

**Skipped (NULL ORB data - holidays):**
- 2025-12-26 (Boxing Day)
- 2025-07-21
- 2025-06-23
- 2025-03-17

---

## EXECUTION HYPOTHESIS (LOCKED IN)

### State Definition
- **ORB:** 0030 (00:30-00:35 Brisbane time)
- **Pre-ORB conditions:**
  - `range_bucket = NORMAL` (not too tight, not too wide)
  - `disp_bucket = D_MED` (moderate displacement)
  - `close_pos_bucket = HIGH` (close near top of pre-ORB range)
  - `impulse_bucket = HIGH` (strong directional impulse)

### Expected Asymmetry
- **Direction:** UP-favored (70% of days)
- **Magnitude:** +44.5 tick median tail skew in 60-minute window
- **Sample:** 30 days total (5.9% frequency)

### Invalidation Rule (NO TRADE)
Strong DOWN drive in first 5-10 minutes with clean expansion → Skip this day

### Reaction Patterns to Observe (00:30-00:45)
- **A) Absorption/Stall:** Initial push fails, overlapping bars, wicks grow, range compresses
- **B) Fake Downside:** Quick push down, no follow-through, fast reclaim
- **C) Delayed Lift:** Chop 10-20 minutes, THEN expansion UP

### Entry Rule
**LONG ONLY** when reaction pattern visible AND price reclaims 5m range high (close above)

### Stop Placement
Below reaction low / compression base / fake-out extreme (structural, not arbitrary)

### Exit Rule
First range expansion OR +20-30 ticks OR 60-minute timeout (capture, not predict)

---

## MANUAL REPLAY PROCEDURE

### For Each Date:

**Step 1: Load data**
```bash
python visualize_replay_example.py
# Modify date_str to current date (e.g., "20260109")
```

OR open the CSV files directly:
- `replay_0030_YYYYMMDD_1m.csv`
- `replay_0030_YYYYMMDD_5m.csv`

**Step 2: Invalidation check (00:30-00:40)**
- Look at first 5m bar after ORB (00:40)
- Is there strong DOWN drive with clean expansion?
- If YES → mark `invalidation_check = "YES"` in template, skip to next date
- If NO → proceed to reaction analysis

**Step 3: Identify reaction pattern (00:30-00:45)**
- Review 1m bars in reaction window
- Classify as A / B / C / NONE
- Mark in `reaction_pattern` column

**Step 4: Check entry trigger**
- Did ANY 5m bar close ABOVE the 5m range high during reaction window?
- If YES → mark `entry_triggered = "YES"`, record `entry_price`
- If NO → mark `entry_triggered = "NO"`, skip outcome analysis

**Step 5: Place structural stop**
- Where is the clear structural low?
  - Reaction base (if absorption pattern)
  - Fake-out low (if fake downside pattern)
  - Compression low (if delayed lift pattern)
- Record in `stop_price` column

**Step 6: Determine outcome (60-minute window from entry)**
- **WIN:** Hit +20-30 ticks OR clean expansion UP before stop hit
- **LOSS:** Stop hit before target
- **TIMEOUT:** 60 minutes expired, no clear outcome (exit at market)
- Record in `outcome_60m` column

**Step 7: Calculate R-multiple**
- R = (entry_price - stop_price)
- If WIN: (profit in ticks) / R
- If LOSS: -1R (or worse if slippage)
- Record in `r_multiple` column

**Step 8: Notes**
- Free-form observations
- Anything notable about price action?
- Why did it win/lose?

---

## EXAMPLE ANALYSIS (2026-01-09)

**Observation from visualization:**

**ORB Window (00:30-00:35):**
- ORB High: 4507.90
- ORB Low: 4491.60
- ORB Size: 16.3 ticks (NORMAL bucket - reasonable)

**Initial reaction (00:30-00:40):**
- First 5m bar (00:30): DOWN from 4503.80 to 4498.70 (5-tick drop)
- Second 5m bar (00:35): UP from 4498.70 to 4505.30 (6.6-tick rise)
- Third 5m bar (00:40): DOWN from 4505.20 to 4497.20 (8-tick drop)

**1m detail (00:30-00:45):**
- High wick bars (87.9%, 85.7%, 91.2% wicks) → absorption/rejection
- Price testing ORB low (4491.60) multiple times
- Lots of chop, no clean expansion DOWN

**Post-ORB outcome (00:50-01:00):**
- Max high: 4509.00 (+11 ticks from ORB high)
- Min low: 4488.00 (-36 ticks from ORB low)
- **Tail skew: NEGATIVE** (went DOWN more than UP)

**Preliminary assessment:**
- **Invalidation:** NO (no clean DOWN expansion)
- **Reaction pattern:** A (Absorption/Stall - wicks, chop, rejection)
- **Entry triggered:** Possibly YES (00:35 bar closed at 4505.30, near ORB high 4507.90)
- **Outcome:** Likely LOSS (price went DOWN to 4488, would have hit stop)

**This is ONE example.** Need to analyze all 11 dates to determine if edge is executable.

---

## DECISION CRITERIA

After analyzing all 11 dates, calculate:

1. **Observable patterns:** How many dates show clear reaction patterns (A/B/C)? (X/11)
2. **Entry triggers:** How many dates trigger entry? (X/11)
3. **Win rate:** How many entries result in WIN? (X/triggered)
4. **Average R-multiple:** Mean of all r_multiple values (wins + losses)
5. **Positive expectancy:** Is (win_rate × avg_win_R) - (loss_rate × avg_loss_R) > 0?

**Thresholds for proceeding:**
- **Minimum observable patterns:** 7/11 (>60%)
- **Minimum entry triggers:** 5/11 (>45%)
- **Minimum win rate:** 50% (given asymmetry)
- **Minimum avg R-multiple:** +0.15R (thin but positive)

**If thresholds met:** Code full backtest with hard-coded rules
**If thresholds NOT met:** Kill state without attachment, test next strongest state

---

## WHAT THIS TEST IS (AND IS NOT)

### This test IS:
- Binary validation: Can ANY positive expectancy be extracted?
- Pattern recognition: Are reactions observable and consistent?
- Execution check: Can entries be triggered with structural stops?
- Reality check: Does statistical asymmetry survive execution?

### This test is NOT:
- Optimization: No parameter tuning, no curve-fitting
- Holy grail hunting: Thin edges are acceptable
- Predictive: We capture reactions, not predict direction
- High win rate: 50-60% WR is fine if R-multiples are positive

---

## NEXT ACTIONS

**Your move:**
1. Open `replay_0030_analysis_template.csv` in Excel
2. Work through each date using the procedure above
3. Fill in all columns for all 11 dates
4. Calculate summary statistics
5. Make decision: Code full backtest OR kill state

**Files to use:**
- `visualize_replay_example.py` - Text visualization helper (modify date_str)
- `replay_0030_YYYYMMDD_1m.csv` - Raw 1m bar data for each date
- `replay_0030_YYYYMMDD_5m.csv` - Raw 5m bar data for each date
- `replay_0030_analysis_template.csv` - Your analysis spreadsheet

**Expected time:** 10-15 minutes per date = 2-3 hours total

**Hard checkpoint:** You are willing to kill this state if execution fails. No emotional attachment. Honesty over hope.

---

## STATUS: WAITING FOR YOUR MANUAL ANALYSIS

All tools prepared. Data extracted. Template ready. Ball is in your court.

When analysis is complete, report findings and decision.
