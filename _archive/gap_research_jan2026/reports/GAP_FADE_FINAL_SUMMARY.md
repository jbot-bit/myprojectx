# GAP FADE TIMING ANALYSIS - FINAL SUMMARY

## The Answer to "When Should I Fade a Gap?"

**SHORT ANSWER**: It depends on gap size. Small gaps (<1.0 ticks) should be faded immediately. Medium gaps (1.0-2.0 ticks) need a pullback wait. Large gaps (>2.0 ticks) should be avoided entirely.

---

## The Data (424 Historical Filled Gaps)

### Overall Timing
- **53.8%** of gaps fill within 5 minutes (immediate)
- **46.2%** of gaps take longer (delayed)
- **71.9%** of gaps fill within 60 minutes
- **94.6%** of all gaps eventually fill

### Critical Insight
**Gap size predicts fill timing better than any other factor.**

---

## The Three Strategies (With Real Win Rates)

### Strategy 1: IMMEDIATE FADE
**Gap Size**: 0.0 - 1.0 ticks
**Entry**: Immediately at gap open (within first 5 minutes)
**Exit Rules**:
- Target: Previous close (100% fill)
- Stop: 1.5× gap size
- Time limit: 60 minutes

**Performance**:
- **Win Rate: 74%** (228 wins / 308 trades)
- Breakeven win rate needed: 60%
- **You have a 14% edge!**

**Breakdown**:
- Gaps 0.0-0.5 ticks: 74.9% win rate
- Gaps 0.5-1.0 ticks: 72.4% win rate

**Risk/Reward**: 1:0.67 (risk 1.5 ticks to make 1.0 tick)

**This is your bread and butter strategy. Trade it aggressively.**

---

### Strategy 2: WAIT FOR PULLBACK
**Gap Size**: 1.0 - 2.0 ticks
**Entry**: Wait 5-15 minutes, enter on pullback toward fill
**Exit Rules**:
- Target: Previous close (100% fill)
- Stop: 2.0× gap size
- Time limit: 60 minutes

**Performance**:
- **Win Rate: ~40-45%** (estimated)
- Breakeven win rate needed: 66.7%
- **You're BELOW breakeven with this strategy**

**Alternative**: Immediate fade of 1.0-2.0 tick gaps shows 72% win rate

**Recommendation**: For gaps 1.0-2.0 ticks, use IMMEDIATE FADE (Strategy 1 approach) instead of waiting for pullback. The wait strategy underperforms.

**Risk/Reward**: 1:0.50

---

### Strategy 3: WAIT 30 MINUTES (DON'T USE)
**Gap Size**: 2.0 - 5.0 ticks
**Entry**: Wait 30 minutes for confirmation
**Exit Rules**:
- Target: 50-75% of gap (partial fill)
- Stop: 2.5× gap size
- Time limit: 90 minutes

**Performance**:
- **Win Rate: ~30-40%** (very low)
- Breakeven win rate needed: 76.9%
- **Far below breakeven - not tradeable**

**Alternative**: Even immediate fade only achieves 50% win rate on these gaps

**Recommendation**: **DO NOT TRADE gaps >2.0 ticks.** The edge is not there.

**Risk/Reward**: 1:0.30 (terrible)

---

## Revised Strategy Recommendations

Based on the win rate analysis, here's what you should ACTUALLY do:

### ONLY TRADE STRATEGY: Immediate Fade of Small Gaps

**Trade**: Gaps 0.0 - 1.0 ticks ONLY
**Entry**: Immediately at gap open
**Stop**: 1.5× gap size
**Target**: Full gap fill
**Time limit**: 60 minutes
**Expected Win Rate**: **74%**
**Breakeven Needed**: 60%
**Your Edge**: +14%

**This is the only gap fade strategy with a significant edge.**

### What About Medium/Large Gaps?

**Gaps 1.0-2.0 ticks**:
- If you MUST trade them: Use immediate fade (72% win rate)
- Better approach: SKIP them and wait for smaller gaps
- The slightly lower win rate (72% vs 74%) isn't worth the increased risk

**Gaps >2.0 ticks**:
- **DO NOT TRADE**
- Win rate drops to 50% or less
- Risk/reward is terrible
- Wait for next day's smaller gap

---

## The Simple Rule

```
IF gap < 1.0 ticks:
    FADE immediately
    Expected win rate: 74%

ELIF gap >= 1.0 and gap < 2.0:
    OPTIONAL: Fade immediately
    Expected win rate: 72%
    (Or skip and wait for tomorrow)

ELSE:
    DO NOT TRADE
    Expected win rate: <50%
```

---

## Position Sizing Example

**Account**: $10,000
**Risk per trade**: 1% = $100

**Example Trade**:
- Gap size: 0.6 ticks
- Stop loss: 0.6 × 1.5 = 0.9 ticks = $90 per contract
- Position size: $100 / $90 = 1.11 contracts → Trade 1 contract
- Expected win rate: 72.4%
- Risk: $90
- Reward: $60 (0.6 ticks)

**Over 100 trades**:
- Wins: 72 × $60 = $4,320
- Losses: 28 × $90 = $2,520
- Net profit: $1,800
- Return: 18% on risked capital

---

## Gap Direction: Does It Matter?

**NO.**

- UP gaps: 54.4% immediate fill, median 5 minutes
- DOWN gaps: 52.8% immediate fill, median 5 minutes
- Difference: 1.6% (not significant)

**Trade both up and down gaps equally.**

---

## Key Statistics Summary Table

| Gap Size | Sample Size | Immediate Fill % | Win Rate (60 min) | Breakeven Needed | Edge | Trade It? |
|----------|-------------|------------------|-------------------|------------------|------|-----------|
| 0.0-0.5 ticks | 203 | 59.0% | **74.9%** | 60.0% | +14.9% | **YES** |
| 0.5-1.0 ticks | 105 | 59.8% | **72.4%** | 60.0% | +12.4% | **YES** |
| 1.0-2.0 ticks | 75 | 48.6% | **72.0%** | 66.7% | +5.3% | OPTIONAL |
| 2.0-5.0 ticks | 38 | 34.4% | **50.0%** | 76.9% | -26.9% | **NO** |
| >5.0 ticks | 27 | 12.5% | **25.0%** | 76.9% | -51.9% | **NO** |

---

## Adverse Excursion Warning

Even when gaps fill eventually, they can run HARD against you first:

**Tiny gaps (0.0-0.5 ticks)**:
- Can run 4-26 ticks against you (up to 2000% of gap size!)
- This is why stops are critical

**Small gaps (0.5-1.0 ticks)**:
- Can run 13-23 ticks against you (up to 383% of gap size)
- Stops prevent catastrophic losses

**Medium gaps (1.0-2.0 ticks)**:
- Can run 5-26 ticks against you (up to 260% of gap size)
- Higher variance, more risk

**Large gaps (2.0-5.0 ticks)**:
- Can run 4-216 ticks against you (up to 480% of gap size!)
- This is why we don't trade them

**THE CRITICAL LESSON**: Always use stops. Even "small" gaps can blow up accounts without stops.

---

## Daily Trading Workflow

### Pre-Market (Before 23:00 UTC)
1. Note yesterday's close: _______
2. Check economic calendar for major news today
3. If major news (FOMC, NFP), SKIP gap trading today
4. Prepare for potential gap at open

### At Market Open (23:00 UTC)
1. Measure gap size: Current price - Previous close = _______
2. Is gap < 1.0 ticks?
   - YES → Execute Strategy 1 (immediate fade)
   - NO → Check if 1.0-2.0 ticks
     - YES → Optional: Execute Strategy 1 (immediate fade) or SKIP
     - NO → SKIP trade, wait for tomorrow

### During Trade
1. Monitor position
2. Move stop to breakeven if gap 50% filled (optional)
3. If 60 minutes pass and gap not filled → EXIT at market
4. If stop hit → ACCEPT loss, don't re-enter

### Post-Trade
1. Record in journal (win/loss, gap size, timing)
2. Update win rate tracker by gap size
3. Adjust filters if needed after 50+ trades

---

## Risk Management Checklist

Before entering ANY gap fade trade:

- [ ] Gap size < 1.0 ticks? (If NO, don't trade)
- [ ] Stop loss calculated and ready to enter? (1.5× gap)
- [ ] Position size calculated? (Risk 1% max)
- [ ] No major news today? (If news, don't trade)
- [ ] 60-minute time limit alarm set?
- [ ] Account can handle loss if stopped? (Don't overtrade)

---

## Performance Expectations

### Month 1 (Learning Phase)
- Expect 60-65% win rate as you learn execution
- Some slippage and timing mistakes
- Focus on following the rules

### Month 2-3 (Consistency Phase)
- Should achieve 70-74% win rate
- Better execution, less slippage
- Refine entry timing

### Month 4+ (Optimization Phase)
- Maintain 72-75% win rate
- Consider tightening filters (e.g., only 0.0-0.8 tick gaps)
- Scale position size carefully

**Do NOT expect to hit 74% win rate immediately. Give yourself time to learn.**

---

## When to Stop Trading Gaps

Stop gap trading for the day if:
- [ ] Down 3% on gap trades today (3 losses in a row)
- [ ] Stopped out 3 times consecutively
- [ ] Feeling emotional or frustrated
- [ ] Major unexpected news breaks

Stop gap trading entirely if:
- [ ] After 50 trades, win rate < 60%
- [ ] Account down 10% from gap trading
- [ ] Can't follow the rules consistently
- [ ] Experiencing significant stress

**It's OK if gap fading isn't for you. Not every strategy fits every trader.**

---

## The Bottom Line

**ONLY fade gaps < 1.0 ticks, immediately at market open, with 1.5× stops.**

Everything else is noise. The edge is in small gaps. Focus there.

Expected performance: **74% win rate** with proper execution.

---

## Files Generated in This Analysis

1. `analyze_gap_fill_timing.py` - Main timing distribution analysis
2. `analyze_gap_adverse_excursion.py` - Adverse excursion and entry strategy analysis
3. `gap_fade_win_rate_analysis.py` - Win rate calculations for each strategy
4. `GAP_FILL_TIMING_GUIDE.md` - Comprehensive guide (all strategies)
5. `GAP_FADE_QUICK_REFERENCE.md` - One-page trading card
6. `GAP_FADE_FINAL_SUMMARY.md` - This document (actionable recommendations)

## Source Data

- `gap_fill_analysis.csv` - 448 gaps analyzed (424 filled, 24 unfilled)
- `gold.db` - 5-minute bar data for adverse excursion analysis

## How to Update This Analysis

```bash
# Regenerate gap analysis with new data
python analyze_gaps.py  # (Your existing gap detection script)

# Run timing analysis
python analyze_gap_fill_timing.py

# Run adverse excursion analysis
python analyze_gap_adverse_excursion.py

# Run win rate analysis
python gap_fade_win_rate_analysis.py
```

---

**Print this page. Keep it on your desk. Follow it religiously.**

Good luck!
