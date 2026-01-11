# ORB Trading Terminology - Simple Explanation

## The Basics: UP/DOWN vs WIN/LOSS

### UP/DOWN = **Break Direction** (What Happened)
- **UP** = Price broke **ABOVE** the ORB high (bullish breakout)
- **DOWN** = Price broke **BELOW** the ORB low (bearish breakout)
- This is what you see in real-time when price moves

### WIN/LOSS = **Trade Outcome** (Did You Make Money?)
- **WIN** = Price hit your profit target BEFORE hitting your stop loss
- **LOSS** = Price hit your stop loss BEFORE hitting your profit target
- This is only known AFTER the trade closes

---

## Example: "10:00 UP after 09:00 WIN"

This means:
1. **09:00 ORB** happened first (at 9:00 AM)
   - Price broke UP or DOWN (direction)
   - Trade was placed
   - **Trade CLOSED** (hit target or stop) **BEFORE 10:00**
   - Result: **WIN** (made money) - **KNOWN at 10:00**

2. **10:00 ORB** happens next (at 10:00 AM)
   - Price broke **UP** (above the 10:00 ORB high)
   - **AND** we know 09:00 was a WIN (because it's already closed)
   - Historical data shows: When 09:00 wins, 10:00 UP breakouts win **57.9%** of the time (vs 55.5% normally)

**Why This Matters:** It's a **correlation pattern** - winning momentum tends to continue. If the first trade of the day wins, the second trade in the same direction has better odds.

### ⚠️ CRITICAL: Zero-Lookahead Requirement

**"10:00 UP after 09:00 WIN" is ONLY valid if:**
- The 09:00 trade is **CLOSED** (WIN or LOSS) before 10:00
- You can **truthfully** know the outcome at decision time

**If 09:00 trade is still OPEN at 10:00:**
- You **CANNOT** use "09:00 WIN" as a condition
- You must track trade state separately:
  - `09_outcome = WIN/LOSS` (only if closed/decided)
  - `09_state = OPEN/FLAT/UNKNOWN`
  - `09_realized = WIN/LOSS/UNKNOWN`

**In practice:** Most ORB trades close quickly (within minutes), so this correlation is usually valid. But you must verify the previous trade is closed before using its outcome.

---

## How ORB Trading Works

### What is an ORB?
**Opening Range Breakout** - A 5-minute range at market open:
- **ORB High** = Highest price in first 5 minutes
- **ORB Low** = Lowest price in first 5 minutes
- **ORB Range** = High - Low

### The Trade Setup
1. **Wait** for the 5-minute ORB to complete
2. **Watch** for price to break above (UP) or below (DOWN) the ORB
3. **Enter** when price breaks out
4. **Stop Loss** = Opposite side of ORB (if UP break, stop = ORB low)
5. **Profit Target** = 1R (same distance as ORB range)

**Example:**
- ORB High: $2,500.00
- ORB Low: $2,499.50
- ORB Range: $0.50 (5 ticks)

**UP Breakout Trade:**
- Entry: $2,500.00 (when price breaks above)
- Stop: $2,499.50 (ORB low)
- Risk: $0.50 per contract (entry - stop)
- Target: Depends on RR setting
  - If RR = 1.0: $2,500.50 (entry + 1 × risk = 1R)
  - If RR = 2.0: $2,501.00 (entry + 2 × risk = 2R)
  - If RR = 3.0: $2,501.50 (entry + 3 × risk = 3R)
- **Profit Target = RR × Risk** (not always 1R)

---

## How This Helps You Trade

### Real-Time Trading Flow

#### **Before 09:00 (Morning Prep)**
Run: `python daily_alerts.py`
- Shows what setups are available today
- Shows historical win rates for current conditions
- Tells you which ORBs to watch

#### **At 09:00 (Asia Open)**
1. **Check PRE_ASIA range** (07:00-09:00)
   - If > 50 ticks → Trade 09:00 ORB
   - If < 30 ticks → Skip 09:00

2. **Wait for ORB to form** (09:00-09:05)
3. **Watch for breakout** (after 09:05)
4. **Enter trade** if breakout happens
5. **Record outcome** (WIN/LOSS) for tomorrow's correlations

#### **At 10:00 (Asia Mid)**
1. **Check 09:00 trade state:**
   - ✅ **If 09:00 trade is CLOSED** → Check outcome (WIN/LOSS)
   - ⚠️ **If 09:00 trade is still OPEN** → Cannot use outcome (state = OPEN/UNKNOWN)
2. **Wait for 10:00 ORB** (10:00-10:05)
3. **Watch for breakout**
4. **If 09:00 was CLOSED and WIN, and 10:00 breaks UP:**
   - Higher confidence (57.9% win rate vs 55.5%)
   - Consider larger position size
5. **If 09:00 was CLOSED and LOSS:**
   - Still trade 10:00 UP (52.7% win rate)
   - But lower confidence
6. **If 09:00 is still OPEN:**
   - Use baseline 10:00 UP stats (55.5% win rate)
   - Cannot use correlation pattern

#### **At 11:00 (Asia Late)**
1. **Check both 09:00 and 10:00 trade states:**
   - ✅ **If both CLOSED** → Use outcomes for correlation
   - ⚠️ **If either still OPEN** → Cannot use that outcome
2. **Best setups (only if both previous trades are CLOSED):**
   - 09:00 WIN + 10:00 WIN → 11:00 UP (57.4% WR)
   - 09:00 LOSS + 10:00 WIN → 11:00 DOWN (57.7% WR)
3. **If trades still open:**
   - Use baseline stats or simpler filters (e.g., PRE_ASIA > 50 ticks)
   - Skip correlation-based patterns

---

## Practical Example: Trading Today

### Scenario: It's 10:00 AM

**What you know:**
- 09:00 ORB happened
- 09:00 broke UP
- **09:00 trade state: CLOSED** ✅
- 09:00 trade: **WIN** (hit target before 10:00)

**What you're watching:**
- 10:00 ORB forming (10:00-10:05)
- Price is near the ORB high

**Your decision:**
- If price breaks UP above 10:00 ORB high → **ENTER**
- Why? Historical data shows: "10:00 UP after 09:00 WIN" = 57.9% win rate
- This is better than the baseline 55.5% win rate
- You have **higher confidence** this will work

**If price breaks DOWN:**
- Skip it (10:00 DOWN after 09:00 WIN = only 49.3% win rate)
- Not worth the risk

### Alternative Scenario: 09:00 Trade Still Open

**What you know:**
- 09:00 ORB happened
- 09:00 broke UP
- **09:00 trade state: OPEN** ⚠️ (still running, hasn't hit target or stop)

**What you're watching:**
- 10:00 ORB forming (10:00-10:05)
- Price is near the ORB high

**Your decision:**
- If price breaks UP above 10:00 ORB high → **ENTER**
- **BUT:** Cannot use "after 09:00 WIN" correlation (09:00 outcome unknown)
- Use baseline 10:00 UP stats: 55.5% win rate
- Still tradeable, but lower confidence than correlation pattern

---

## Key Takeaways

1. **UP/DOWN** = Direction of breakout (real-time)
2. **WIN/LOSS** = Trade result (known **ONLY after trade closes**)
3. **Correlations** = Patterns that improve your odds
   - "10:00 UP after 09:00 WIN" = 57.9% vs 55.5% baseline
   - **BUT:** Only valid if previous trade is CLOSED
   - Use this to size positions and filter trades

4. **Zero Lookahead** = Only use info available NOW
   - Can use: PRE_ASIA range (known at 09:00)
   - Can use: Previous ORB outcomes **IF CLOSED** (known after they close)
   - Cannot use: Previous ORB outcomes if still OPEN
   - Cannot use: Session types (not known until session ends)

5. **Trade State Tracking:**
   - `outcome = WIN/LOSS` (only if closed/decided)
   - `state = OPEN/FLAT/UNKNOWN` (current position status)
   - Always verify trade is closed before using outcome in correlations

6. **Best Edge:** 10:00 UP breakout
   - Works 55.5% of the time standalone
   - Works 57.9% after 09:00 WIN (if 09:00 is closed)
   - This is your bread and butter trade

7. **Risk/Reward:**
   - Profit Target = **RR × Risk** (not always 1R)
   - System uses variable RR (1.5, 2.0, 3.0, etc.)
   - Higher RR = larger target, lower win rate, higher avg R

---

## Tools to Use

1. **Morning Prep:** `python daily_alerts.py`
   - Shows today's setups

2. **Real-Time Signals:** `python realtime_signals.py --time 1000`
   - Shows what's available right now
   - Shows historical performance

3. **Edge Discovery:** Use the Streamlit app
   - Discover new patterns
   - Test different filters

4. **End of Day:** Record outcomes
   - Track 09:00, 10:00, 11:00 results
   - Use for tomorrow's correlations

---

## Remember

- **Win rates are 50-58%** (not 70%+)
- **This is honest, tradeable data**
- **Small edges compound over time**
- **Risk management is critical**
- **Only trade when conditions match**

