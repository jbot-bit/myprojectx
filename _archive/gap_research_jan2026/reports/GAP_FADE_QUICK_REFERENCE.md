# GAP FADE QUICK REFERENCE CARD

## One-Page Trading Guide

### Gap Size Decision Matrix

| Gap Size (ticks) | Immediate Fill % | Strategy | Entry Timing | Stop Loss | Expected Fill Time |
|------------------|------------------|----------|--------------|-----------|-------------------|
| 0.0 - 0.5 | 59.0% | IMMEDIATE FADE | Enter NOW | 1.5× gap | 5 min |
| 0.5 - 1.0 | 59.8% | IMMEDIATE FADE | Enter NOW | 1.5× gap | 5 min |
| 1.0 - 2.0 | 48.6% | WAIT PULLBACK | Wait 5-15 min | 2.0× gap | 10 min |
| 2.0 - 5.0 | 34.4% | WAIT 30 MIN | Wait 30 min | 2.5× gap | 22 min |
| > 5.0 | 12.5% | DON'T FADE | Skip trade | N/A | 13+ hours |

---

## The Three Rules

1. **Small gaps (<1.0 ticks)**: Fade immediately. 59% fill in 5 minutes.
2. **Medium gaps (1.0-2.0 ticks)**: Wait for pullback. 51% run away first.
3. **Large gaps (>2.0 ticks)**: Wait 30 minutes or skip. High risk.

---

## Trade Execution Checklist

### Pre-Trade (Before Market Open)
- [ ] Identify previous day's close price
- [ ] Calculate gap size at market open (current - previous close)
- [ ] Determine which strategy to use (see table above)
- [ ] Calculate position size based on stop loss distance
- [ ] Check if major news event today (if yes, skip gap fade)

### During Trade
- [ ] Enter at specified timing
- [ ] Set stop loss immediately
- [ ] Set time-based alarm (60 or 90 minutes)
- [ ] Monitor for fill or stop-out

### Post-Trade
- [ ] Record trade in journal
- [ ] Update performance tracker by gap size
- [ ] If stopped out, DO NOT re-enter same gap

---

## Stop Loss Distance Calculation

**Formula**: Stop distance = Gap size × Multiplier

| Gap Size | Multiplier | Example Gap | Stop Distance |
|----------|------------|-------------|---------------|
| 0.0-1.0 ticks | 1.5× | 0.8 ticks | 1.2 ticks (12 points) |
| 1.0-2.0 ticks | 2.0× | 1.5 ticks | 3.0 ticks (30 points) |
| 2.0-5.0 ticks | 2.5× | 3.0 ticks | 7.5 ticks (75 points) |

---

## Position Sizing Formula

```
Position Size = (Account Risk Amount) / (Stop Loss Distance in $)

For MGC:
- 1 tick = 0.1 point = $10 per contract
- Example: 1.2 tick stop = $120 per contract
```

**Example Calculation**:
- Account: $10,000
- Risk per trade: 1% = $100
- Stop: 1.2 ticks = $120
- Position: $100 / $120 = 0.83 contracts → Trade 1 contract MAX

---

## Time-Based Exit Rules

| Gap Size | Exit if Not Filled Within |
|----------|----------------------------|
| 0.0-1.0 ticks | 60 minutes |
| 1.0-2.0 ticks | 60 minutes |
| 2.0-5.0 ticks | 90 minutes |

**If time limit reached and gap hasn't filled**: Exit immediately. Your thesis was wrong.

---

## Win Rate Expectations

| Gap Size | Expected Win Rate | Rationale |
|----------|------------------|-----------|
| 0.0-1.0 ticks | 55-60% | Most fill within 15 minutes |
| 1.0-2.0 ticks | 45-50% | Miss immediate fills, catch delayed fills |
| 2.0-5.0 ticks | 30-40% | High risk, lower probability |

Track your actual win rates. If below expectations, adjust filters.

---

## Red Flags (DO NOT TRADE)

- [ ] Gap >5 ticks (too large, likely continuation)
- [ ] Major news event scheduled (FOMC, NFP, etc.)
- [ ] Extremely low volume at open (illiquid conditions)
- [ ] Gap on a holiday or Friday before long weekend
- [ ] You've already been stopped out on this gap today

---

## When to Trade WITH the Gap (Not Fade)

If you see a gap >5 ticks:
- Don't fade it
- Consider trading IN THE DIRECTION of the gap
- Use ORB or momentum strategy instead
- These gaps often continue for several hours

---

## Performance Tracking Template

| Date | Gap Size | Direction | Strategy Used | Entry Price | Exit Price | Result | Notes |
|------|----------|-----------|---------------|-------------|------------|--------|-------|
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |

**Calculate weekly**: Win rate by gap size category. Adjust filters if needed.

---

## Summary Statistics (Historical Data)

Based on 424 filled gaps in MGC futures:

- **53.8%** fill in first 5 minutes
- **62.7%** fill within 15 minutes
- **68.9%** fill within 30 minutes
- **71.9%** fill within 60 minutes

**Key insight**: Most gaps that WILL fill do so within the first hour. If not filled after 60 minutes, probability drops significantly.

---

## What to Do When Stopped Out

1. **Accept the loss** - Don't revenge trade
2. **Don't re-enter this gap** - Move on
3. **Review trade** - Did you follow the rules?
4. **Update statistics** - Track why the trade failed
5. **Wait for next gap** - Fresh opportunity tomorrow

---

## Advanced: When to Adjust Strategy

**If your live results show**:

- Small gaps not filling → Tighten size filter to 0.0-0.8 ticks only
- Medium gaps stopping you out → Skip medium gaps, only trade small
- Large gaps too risky → Don't trade anything >1.5 ticks
- Win rate <50% on small gaps → Review entry timing, maybe wait for pullback

**Trust the process**: This guide is based on 424 historical gaps. Your live performance may vary. Adjust based on YOUR results.

---

## Emergency Rules

If you find yourself in any of these situations:

- **Down 3% in a day on gap fades** → STOP trading gaps for the day
- **Stopped out 3 times in a row** → STOP, review strategy, start fresh tomorrow
- **Account down 10% from gap trading** → STOP, reassess if gap fading fits your personality
- **Feeling emotional about a gap trade** → STOP, take a break, come back calm

Mental capital is as important as financial capital. Protect both.

---

## Daily Prep (2 Minutes)

1. Note previous close: ______
2. Check for news today: Yes / No
3. If yes to news, skip gap trading today
4. If no news, ready to trade gaps per strategy

**Remember**: You don't HAVE to fade every gap. Be selective. Only trade setups that match the criteria.

---

Print this guide. Keep it next to your trading station. Follow it religiously for 50 trades before making any modifications.

Good luck!
