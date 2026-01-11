# MGC Trading Playbook

**Based on 740 days of historical data (2024-2026)**

This playbook documents high-probability ORB setups derived from systematic analysis of Micro Gold futures (MGC) trading patterns.

---

## Quick Reference - Best Setups

### Top 3 High-Probability Setups

1. **11:00 UP Breakout** (Asia Late)
   - Win Rate: 57.9%
   - Avg R: +0.16
   - Sample Size: 247 trades
   - Context: Works best during EXPANDED Asia sessions

2. **18:00 UP Breakout** (London Open)
   - Win Rate: 56.9%
   - Avg R: +0.14
   - Sample Size: 262 trades
   - Context: Strong across all London session types

3. **18:00 DOWN Breakout after London CONSOLIDATION**
   - Win Rate: 58.8%
   - Avg R: +0.18
   - Sample Size: 51 trades
   - Context: Specific to consolidation London sessions

---

## Complete ORB Performance Summary

### By Time Slot (Overall)

| ORB Time | Win Rate | Avg R | Total Trades | Assessment |
|----------|----------|-------|--------------|------------|
| 09:00 (Asia Open) | 45.2% | -0.10 | 493 | **AVOID** - Consistently negative |
| 10:00 (Asia Mid) | 46.8% | -0.06 | 515 | **AVOID** - Slightly negative |
| 11:00 (Asia Late) | 53.3% | +0.07 | 495 | **TRADEABLE** - Best Asia ORB |
| 18:00 (London Open) | 53.2% | +0.06 | 513 | **TRADEABLE** - Consistent edge |
| 23:00 (NY Open) | 48.3% | -0.03 | 518 | **MARGINAL** - Neutral to negative |
| 00:30 (NYSE) | 46.8% | -0.06 | 511 | **AVOID** - Consistently negative |

### By Direction

| ORB Time | Direction | Win Rate | Avg R | Trades |
|----------|-----------|----------|-------|--------|
| **09:00** | UP | 44.7% | -0.11 | 262 |
| **09:00** | DOWN | 45.9% | -0.08 | 231 |
| **10:00** | UP | 48.2% | -0.04 | 251 |
| **10:00** | DOWN | 45.5% | -0.09 | 264 |
| **11:00** | **UP** | **57.9%** | **+0.16** | **247** ✅ |
| **11:00** | DOWN | 48.8% | -0.02 | 248 |
| **18:00** | **UP** | **56.9%** | **+0.14** | **262** ✅ |
| **18:00** | DOWN | 49.4% | -0.01 | 251 |
| **23:00** | UP | 48.1% | -0.04 | 287 |
| **23:00** | DOWN | 48.5% | -0.03 | 231 |
| **00:30** | UP | 44.5% | -0.11 | 283 |
| **00:30** | DOWN | 49.6% | -0.01 | 228 |

---

## Session-Based Strategies

### Asia Session (09:00-17:00 Local)

**Asia EXPANDED (most common)**
- 11:00 UP: 52.4% WR, +0.05 R (397 trades) ✅ BEST
- 10:00: Mixed results, 46.9% WR, -0.06 R
- 09:00: Poor results, 45.0% WR, -0.10 R

**Key Insight:**
- Wait for the 11:00 ORB, especially if Asia is EXPANDED
- Favor UP breakouts
- Avoid 09:00 and 10:00 ORBs during Asia

### London Session (18:00-23:00 Local)

**After London CONSOLIDATION:**
- 18:00 DOWN: 58.8% WR, +0.18 R (51 trades) ✅ BEST EDGE
- 23:00: 53.4% WR, +0.07 R (88 trades) ✅

**After London SWEEP_HIGH:**
- 18:00: 53.7% WR, +0.07 R (229 trades) ✅
- 23:00: **AVOID** - 42.5% WR, -0.15 R (233 trades) ❌

**After London SWEEP_LOW:**
- 18:00: 52.5% WR, +0.05 R (162 trades)
- 23:00: 52.1% WR, +0.04 R (163 trades)

**After London EXPANSION:**
- 23:00: 55.9% WR, +0.12 R (34 trades) ✅

**Key Insight:**
- 18:00 is the best London ORB
- After CONSOLIDATION, favor DOWN breakouts
- **Avoid** 23:00 ORB after SWEEP_HIGH sessions

### NY Session (23:00-02:00 Local)

**During NY CONSOLIDATION:**
- **AVOID ALL ORBs** - 31-37% WR ❌
- This is the worst session type

**During NY EXPANSION:**
- 23:00: 52.0% WR, +0.04 R (100 trades)
- 00:30: 54.4% WR, +0.09 R (79 trades) ✅

**During NY SWEEP_HIGH or SWEEP_LOW:**
- Neutral to slightly negative results
- No clear edge

**Key Insight:**
- Only trade NY ORBs during EXPANSION
- Completely avoid during CONSOLIDATION

---

## Setups to AVOID

### Always Avoid These:

1. **NY Consolidation setups** (31-37% WR)
   - 23:00 during NY CONSOLIDATION: 31.6% WR, -0.37 R
   - 00:30 during NY CONSOLIDATION: 37.0% WR, -0.26 R

2. **23:00 after London SWEEP_HIGH** (42.5% WR, -0.15 R)

3. **09:00 ORBs in general** (45.2% WR, -0.10 R)

4. **00:30 ORBs in general** (46.8% WR, -0.06 R)
   - Exception: During NY EXPANSION (54.4% WR)

---

## Daily Workflow

### Morning Preparation (08:00-08:30 Brisbane Time)

1. **Update Data:**
   ```bash
   python daily_update.py
   ```

2. **Review Daily Alerts:**
   - Alerts auto-run after daily_update.py
   - Shows high-probability setups for today based on session conditions

3. **Check Session Context:**
   ```bash
   python query_features.py
   ```
   - Review Asia range, session types
   - Identify which ORBs to focus on

### During Trading Day

**09:00 ORB:** Skip (poor historical performance)

**10:00 ORB:** Skip (poor historical performance)

**11:00 ORB:** ✅ TRADE
- Look for UP breakouts
- Best during EXPANDED Asia sessions
- 57.9% WR, +0.16 R historical edge

**18:00 ORB:** ✅ TRADE
- Strong overall (56.9% WR UP breakouts)
- After CONSOLIDATION: Favor DOWN (58.8% WR)
- After SWEEP_HIGH: Take either direction (53.7% WR)

**23:00 ORB:** CONDITIONAL
- After London SWEEP_HIGH: **SKIP** (42.5% WR)
- After London EXPANSION: Take it (55.9% WR)
- During NY CONSOLIDATION: **SKIP** (31.6% WR)
- During NY EXPANSION: Take it (52.0% WR)

**00:30 ORB:** Usually SKIP
- Exception: During NY EXPANSION (54.4% WR)

### End of Day Review

1. **Filter Recent Setups:**
   ```bash
   python filter_orb_setups.py --orb 1100 --direction UP --last_days 30
   ```

2. **Analyze Performance:**
   ```bash
   python analyze_orb_performance.py
   ```

3. **Export for Deeper Analysis:**
   ```bash
   python export_csv.py daily_features --days 30
   ```

---

## Risk Management Rules

### Position Sizing
- **High Confidence Setups** (11:00 UP, 18:00 UP): 1-1.5% risk
- **Medium Confidence** (Conditional setups): 0.5-1% risk
- **Low Confidence / Learning**: 0.25-0.5% risk

### Entry Rules
- Wait for 5-minute bar to CLOSE outside ORB range
- ORB range = High and Low of 09:00-09:05, 10:00-10:05, etc. (5-minute window)
- Don't chase if price is already 2x ORB size away

### Stop Loss
- 1R = ORB size (distance from ORB breakout level to opposite ORB boundary)
- Stop should be at the opposite side of the ORB range

### Target
- Historical avg R is +0.07 to +0.18 for best setups
- Consider scaling out at +1R, letting winner run to +2R or session high/low

### Maximum Daily Trades
- **Recommended:** 2-3 ORBs per day maximum
- Focus on 11:00 and 18:00 as primary opportunities

---

## Advanced Filters

### Combine Multiple Conditions

**Example: Best 18:00 Setup**
```bash
python filter_orb_setups.py \
  --orb 1800 \
  --direction DOWN \
  --london_type CONSOLIDATION \
  --outcome WIN
```

**Example: Find Large Asia Days**
```bash
python filter_orb_setups.py \
  --min_asia_range 500 \
  --orb 1100 \
  --direction UP
```

---

## Key Statistics Summary

**Total Days Analyzed:** 740
**Date Range:** 2024-01-02 to 2026-01-09
**Total ORB Trades:** ~3,000 across all 6 ORBs

**Overall System:**
- Combined WR across all ORBs: ~49% (slightly losing)
- **BUT** selective setups have 55-59% WR with positive R
- Edge comes from *filtering for specific conditions*, not trading everything

**Best Time to Trade:** 11:00 and 18:00
**Worst Time to Trade:** 09:00, 00:30, and during NY Consolidation

---

## Notes and Disclaimers

1. **Historical performance does not guarantee future results**
   - Markets change, patterns can fail
   - Use this as ONE input in your decision-making

2. **Sample sizes matter**
   - Setups with <20 trades are LOW confidence
   - Setups with 50+ trades are HIGH confidence
   - Best setups have 200+ trades of history

3. **Session classification is important**
   - Asia/London/NY session types significantly affect ORB performance
   - Always check `daily_alerts.py` for context-specific recommendations

4. **Continuous improvement**
   - Re-run `analyze_orb_performance.py` monthly to check if edges persist
   - Export data and do your own analysis
   - Track your own trades in a journal

5. **This is a DISCRETIONARY system**
   - Not fully automated
   - Requires judgment on execution, market conditions, news events
   - Use alerts as guidance, not gospel

---

## Quick Command Reference

```bash
# Daily morning routine
python daily_update.py

# Check today's setup
python daily_alerts.py

# Find specific setups
python filter_orb_setups.py --orb 1100 --direction UP --last_days 30

# Performance analysis
python analyze_orb_performance.py

# Export for Excel analysis
python export_csv.py daily_features --days 90
python export_csv.py orb_performance

# Database health check
python check_db.py
python query_features.py
```

---

**Last Updated:** 2026-01-11
**Data Through:** 2026-01-09
