# ORB Outcome Momentum Framework (Engine B)

**Date:** 2026-01-12
**Status:** Evidence-based (validated with backtest data)
**Core Principle:** Prior ORB outcomes create momentum for subsequent ORBs within the same session

**⚠️ IMPORTANT:** This framework uses **Engine B: Outcome Momentum Logic** ONLY.
- This is about intra-session ORB → ORB correlations (09:00 WIN → 10:00 UP)
- This is NOT about prior-session inventory resolution
- For Asia → London liquidity logic, see `ASIA_LONDON_FRAMEWORK.md` (Engine A)

---

## ONE-LINE TRUTH

**When an early ORB wins, the next ORB in the same direction has better odds.**

Winning momentum tends to continue within a session. Losing momentum creates reversal opportunities.

---

## SCOPE: INTRA-ASIA ONLY

This framework applies to:
- **09:00 → 10:00** (Asia Early → Asia Mid)
- **10:00 → 11:00** (Asia Mid → Asia Late)
- **09:00 + 10:00 → 11:00** (Combined momentum)

**Not applicable to:**
- ❌ Asia → London (use Engine A instead)
- ❌ Asia → NY (different session, different logic)
- ❌ London → NY (limited data, untested)

---

## CRITICAL REQUIREMENT: Zero-Lookahead

**You can ONLY use prior ORB outcomes if the trade is CLOSED.**

### ✅ Valid:
- 09:00 trade closed at 09:47 with WIN → Can use for 10:00 decision
- 10:00 trade closed at 10:22 with LOSS → Can use for 11:00 decision

### ❌ Invalid:
- 09:00 trade still OPEN at 10:00 → CANNOT use outcome (unknown)
- 10:00 trade still running at 11:00 → CANNOT use outcome

**In practice:** Most ORB trades close quickly (within 5-20 minutes), so this correlation is usually valid. But you MUST verify trade state before using outcome.

---

## STEP 1 — Check Prior ORB State

Before the next ORB opens, ask:

### Is the previous ORB trade closed?

**If YES:**
- Record outcome: WIN or LOSS
- Record direction: UP or DOWN
- Use for next ORB decision

**If NO (still OPEN):**
- Cannot use outcome
- Trade next ORB using baseline stats
- Do NOT assume outcome

---

## STEP 2 — Apply Correlation Pattern (If Closed)

### Pattern 1: 09:00 → 10:00
| 09:00 Outcome | 10:00 Direction | Win Rate | Delta vs Baseline | Sample | Verdict |
|---------------|----------------|----------|-------------------|--------|---------|
| WIN | UP | 57.9% | +2.4% | 200+ | ✅ HIGHER EDGE |
| WIN | DOWN | 49.3% | -6.2% | 200+ | ⚠️ LOWER EDGE |
| LOSS | UP | 52.7% | -2.8% | 200+ | ⚠️ LOWER EDGE |
| LOSS | DOWN | 53.8% | +1.1% | 200+ | ~ BASELINE |

**Baseline:** 10:00 UP = 55.5% WR, 10:00 DOWN = 52.7% WR

**Actionable:**
- If 09:00 WIN (closed) → Prefer 10:00 UP (57.9% vs 55.5%)
- If 09:00 WIN (closed) → Avoid 10:00 DOWN (49.3% vs 52.7%)

### Pattern 2: 10:00 → 11:00
| 10:00 Outcome | 11:00 Direction | Win Rate | Delta vs Baseline | Sample | Verdict |
|---------------|----------------|----------|-------------------|--------|---------|
| WIN | UP | 56.2% | +1.8% | 200+ | ✅ HIGHER EDGE |
| WIN | DOWN | 51.4% | -0.9% | 200+ | ~ BASELINE |
| LOSS | UP | 53.1% | -1.3% | 200+ | ~ BASELINE |
| LOSS | DOWN | 54.3% | +2.0% | 200+ | ✅ REVERSAL |

**Baseline:** 11:00 UP = 54.4% WR, 11:00 DOWN = 52.3% WR

**Actionable:**
- If 10:00 WIN (closed) → Prefer 11:00 UP (56.2% vs 54.4%)
- If 10:00 LOSS (closed) → Consider 11:00 DOWN reversal (54.3% vs 52.3%)

### Pattern 3: 09:00 + 10:00 → 11:00 (Combined Momentum)
| 09:00 | 10:00 | 11:00 Direction | Win Rate | Delta vs Baseline | Sample | Verdict |
|-------|-------|----------------|----------|-------------------|--------|---------|
| WIN | WIN | UP | 57.4% | +3.0% | 200+ | ✅✅ BEST EDGE |
| WIN | WIN | DOWN | 48.6% | -3.7% | 200+ | ❌ AVOID |
| LOSS | WIN | UP | 54.1% | -0.3% | 200+ | ~ BASELINE |
| LOSS | WIN | DOWN | 57.7% | +5.4% | 200+ | ✅✅ REVERSAL |
| WIN | LOSS | UP | 51.2% | -3.2% | 200+ | ⚠️ LOWER |
| WIN | LOSS | DOWN | 53.9% | +1.6% | 200+ | ~ BASELINE |
| LOSS | LOSS | UP | 49.8% | -4.6% | 200+ | ❌ AVOID |
| LOSS | LOSS | DOWN | 55.1% | +2.8% | 200+ | ✅ REVERSAL |

**Baseline:** 11:00 UP = 54.4% WR, 11:00 DOWN = 52.3% WR

**Actionable:**
- **Best edges:**
  - 09:00 WIN + 10:00 WIN → 11:00 UP (57.4%, +3.0%)
  - 09:00 LOSS + 10:00 WIN → 11:00 DOWN (57.7%, +5.4%)
- **Avoid:**
  - 09:00 WIN + 10:00 WIN → 11:00 DOWN (48.6%, -3.7%)
  - 09:00 LOSS + 10:00 LOSS → 11:00 UP (49.8%, -4.6%)

---

## STEP 3 — Execution Rules

### Entry:
- Standard ORB execution (09:05, 10:05, 11:05)
- Wait for break confirmation
- No anticipation

### Position Sizing:
- **Higher edge patterns** (57%+ WR): Consider 1.5x position
- **Baseline patterns** (52-55% WR): Standard 1x position
- **Lower edge patterns** (<50% WR): Skip or reduce to 0.5x

### Risk Management:
- These are SMALL edges (2-5% WR improvement)
- Do NOT over-leverage
- Still respect standard stop-loss rules

---

## WHAT THIS IS NOT

❌ **Not prediction** - You're not predicting the next ORB direction
❌ **Not guaranteed** - 57% WR still means 43% failure rate
❌ **Not inventory logic** - This is outcome momentum, not liquidity resolution
❌ **Not for session transitions** - This is intra-Asia only (not Asia → London)

---

## REAL-TIME TRADING FLOW

### At 10:00 (Checking 09:00 State)

**Step 1:** Check 09:00 trade state
- Is 09:00 trade closed? (Check trade log)
- If YES → Note outcome (WIN/LOSS) and direction (UP/DOWN)
- If NO → Skip correlation, use baseline

**Step 2:** Wait for 10:00 ORB (10:00-10:05)

**Step 3:** Evaluate 10:00 break direction
- If 10:00 breaks UP:
  - 09:00 WIN (closed)? → **Higher confidence** (57.9% vs 55.5%)
  - 09:00 LOSS or OPEN? → **Baseline confidence** (55.5%)

- If 10:00 breaks DOWN:
  - 09:00 WIN (closed)? → **Lower confidence** (49.3% vs 52.7%) → Consider skip
  - 09:00 LOSS or OPEN? → **Baseline confidence** (52.7%)

**Step 4:** Execute or skip based on confidence level

### At 11:00 (Checking 09:00 + 10:00 State)

**Step 1:** Check both 09:00 and 10:00 trade states
- Are BOTH closed? → Can use combined momentum pattern
- Is EITHER open? → Cannot use that outcome, use simpler pattern

**Step 2:** Wait for 11:00 ORB (11:00-11:05)

**Step 3:** Evaluate 11:00 break direction
- If 11:00 breaks UP:
  - 09:00 WIN + 10:00 WIN? → **BEST EDGE** (57.4%)
  - Other patterns → Check table above

- If 11:00 breaks DOWN:
  - 09:00 LOSS + 10:00 WIN? → **BEST REVERSAL** (57.7%)
  - 09:00 WIN + 10:00 WIN? → **AVOID** (48.6%)
  - Other patterns → Check table above

**Step 4:** Execute or skip based on pattern

---

## IMPLEMENTATION NOTES

### Data Required:
- Prior ORB entry time
- Prior ORB exit time (or current state: OPEN/CLOSED)
- Prior ORB outcome (WIN/LOSS, only if closed)
- Prior ORB direction (UP/DOWN)

### Code Structure:
```python
# At 10:00 decision point
if orb_0900_state == "CLOSED":
    if orb_0900_outcome == "WIN":
        if orb_1000_direction == "UP":
            confidence = "HIGH"  # 57.9%
        elif orb_1000_direction == "DOWN":
            confidence = "LOW"   # 49.3%, consider skip
    elif orb_0900_outcome == "LOSS":
        confidence = "BASELINE"  # Use standard 10:00 stats
else:
    # 09:00 still OPEN
    confidence = "BASELINE"  # Cannot use outcome
```

### State Tracking:
You need to track:
- `orb_state`: "OPEN" | "CLOSED"
- `orb_outcome`: "WIN" | "LOSS" | "UNKNOWN"
- `orb_direction`: "UP" | "DOWN" | "NONE"

**Critical:** Update state as soon as TP or SL is hit, BEFORE next ORB opens.

---

## WHAT TO TEST NEXT

### TEST 1: Time decay of correlation
- Does the edge weaken if 09:00 closed more than X minutes ago?
- Hypothesis: Fresher outcomes = stronger correlation

### TEST 2: Magnitude of WIN/LOSS
- Does a big WIN (>2R) create stronger momentum than small WIN (1R)?
- Does a big LOSS create stronger reversal signal?

### TEST 3: ORB size relationship
- Does correlation strengthen when prior ORB was large?
- Small ORBs vs large ORBs - different momentum behavior?

### TEST 4: Extend to other sessions
- Does London ORB outcome affect 23:00 NY ORB?
- Likely not (different session, different participants)

---

## TWO ENGINES - DO NOT MIX

### Engine A: Liquidity / Inventory (SEPARATE - see ASIA_LONDON_FRAMEWORK.md)
**What:** Prior-session inventory resolution
**Logic:** Asia resolved prior HIGH → London LONG
**Used for:** Session → Session relationships (Asia → London)
**Data:** Prior NY high/low, prior London high/low

### Engine B: Outcome Momentum (THIS DOCUMENT)
**What:** Intra-session ORB outcome correlations
**Logic:** 09:00 WIN → 10:00 UP has higher win rate
**Used for:** ORB → ORB within same session (intra-Asia)
**Data:** Previous ORB outcomes (if closed)

**These are DIFFERENT frameworks. Do not combine them.**

---

## KEY TAKEAWAYS

1. **Outcome momentum is real** - 09:00 WIN → 10:00 UP = 57.9% vs 55.5%
2. **Only use if closed** - Zero-lookahead is critical
3. **Small edges** - 2-5% WR improvement, not 20%
4. **Intra-Asia only** - Don't apply to Asia → London (use Engine A)
5. **Combined momentum strongest** - 09:00 + 10:00 → 11:00 patterns
6. **Reversal patterns exist** - 09:00 LOSS + 10:00 WIN → 11:00 DOWN (57.7%)

---

## GLOSSARY

### Outcome
**Definition:** Whether a prior ORB trade hit TP (WIN) or SL (LOSS)
**Valid only if:** Trade is CLOSED before next ORB
**Not the same as:** Break direction (UP/DOWN)

### State
**Definition:** Current position status
**Values:** OPEN | CLOSED | FLAT
**Usage:** Check state before using outcome

### Momentum
**Definition:** Winning outcomes increase probability of same-direction wins
**Example:** 09:00 WIN → 10:00 UP = 57.9%
**Not:** Guaranteed or predictive

### Reversal
**Definition:** Losing outcomes sometimes increase probability of opposite-direction wins
**Example:** 09:00 LOSS + 10:00 WIN → 11:00 DOWN = 57.7%
**Usage:** Selective, pattern-specific

### Correlation
**Definition:** Statistical relationship between prior outcome and next ORB performance
**Size:** 2-5% WR improvement
**Not:** Causation or certainty

---

## REFERENCES

- `TERMINOLOGY_EXPLAINED.md` - Basic concepts (UP/DOWN vs WIN/LOSS)
- `ASIA_LONDON_FRAMEWORK.md` - Engine A (liquidity logic)
- `TRADING_RULESET.md` - Complete trading rules
- Data source: `orb_trades_5m_exec` table, 2020-2026 backtest
