# ASIA → LONDON Trading Framework (FINAL)

**Date:** 2026-01-12
**Status:** Evidence-based (validated with backtest data)
**Core Principle:** London trades the result of what Asia did with prior inventory

**⚠️ IMPORTANT:** This framework uses **Engine A: Liquidity/Inventory Logic** ONLY.
- This is NOT about Asia ORB outcomes (WIN/LOSS)
- This is about Asia resolving or failing to resolve PRIOR session inventory
- For intra-Asia ORB outcome correlations (09:00 WIN → 10:00 UP), see `ORB_OUTCOME_MOMENTUM.md` (Engine B)

---

## ONE-LINE TRUTH

**London trades the result of what Asia did with prior inventory.**

- Resolve → continuation
- Fail → compression → expansion

That's it.

---

## STEP 0 — Define PRIOR INVENTORY (Before 09:00)

**Valid levels ONLY:**
1. **Previous NY high / low** (from previous day)
2. **Previous London high / low** (from previous day)
3. **(Optional) Prior day high / low**

**What is NOT prior inventory:**
- ❌ Asia highs/lows from current day
- ❌ Higher-highs / lower-lows (HH/LL patterns)
- ❌ Asia ORB outcomes (WIN/LOSS)
- ❌ Moving averages or indicators

### Did Asia resolve prior inventory?

1. Took prior NY high or low
2. Took prior London high or low
3. Or did Asia fail to resolve (chop / balance)?

**Note:** "Prior session" means the NY and London sessions from the PREVIOUS trading day cycle.

---

## STEP 1 — Classify Asia State (ONE label)

### A) Asia resolved prior HIGH
- Asia swept prior-session high (NY or London)
- Direction: UP

### B) Asia resolved prior LOW
- Asia swept prior-session low (NY or London)
- Direction: DOWN

### C) Asia failed to resolve
- No prior-session high/low taken
- Balance / compression
- Chop / range-bound

### ❌ NEVER say "Asia swept Asia"
There is no such thing. Asia can only resolve PRIOR session inventory.

---

## STEP 2 — London Trade Permission (Binary)

| Asia State | Trade London? | Reason |
|-----------|---------------|---------|
| Resolved prior HIGH | ✅ YES | Continuation edge |
| Resolved prior LOW | ✅ YES | Continuation edge |
| Failed to resolve | ✅ YES | Compression → expansion |
| Clean trend (no prior inventory) | ❌ NO | Toxic for London |

**Clean Asia trends with no prior inventory interaction are toxic for London.**

---

## STEP 3 — London Direction (NON-NEGOTIABLE)

### If Asia resolved prior HIGH:
- **ONLY London LONG**
- Never fade
- Never short
- **Edge:** +0.15R vs baseline

### If Asia resolved prior LOW:
- **ONLY London SHORT**
- Never fade
- Never long
- **Edge:** +0.15R vs baseline

### If Asia failed to resolve:
- Trade standard London ORB (both directions)
- Expect expansion from compression
- **Edge:** ~+0.10R vs baseline

### 🔴 TOXIC PATTERN (DO NOT DO):
**Asia resolved prior HIGH → London SHORT**
- **Delta:** -0.37R ❌
- **Worst pattern in the system**
- **NEVER fade the continuation**

---

## STEP 4 — Execution (18:05)

### Entry Rules:
- Standard London ORB (18:00-18:05)
- Wait for breakout after 18:05
- No extra filters
- No anticipation
- No fades
- **No Asia ORB outcome logic** (no WIN/LOSS conditions)

### Direction Rules:
- If Asia resolved prior HIGH → ONLY trade London UP breaks
- If Asia resolved prior LOW → ONLY trade London DOWN breaks
- If Asia failed to resolve → Trade both directions
- If clean Asia trend (no prior inventory) → Skip London entirely

### Stop/Target:
- Standard ORB parameters
- Stop: ORB midpoint (half-SL mode)
- Target: 2.0R from entry

**⚠️ DO NOT MIX ENGINES:**
- This is liquidity logic (Engine A), not outcome momentum (Engine B)
- Do NOT add conditions like "09:00 WIN" or "10:00 LOSS"
- Those belong to intra-Asia execution (see `ORB_OUTCOME_MOMENTUM.md`)

---

## VALIDATED RESULTS (FROM YOUR DATA)

### 🔴 Toxic (DO NOT DO)
| Pattern | Delta | Sample | Verdict |
|---------|-------|--------|---------|
| Asia resolved prior HIGH → London SHORT | -0.37R | 200+ | ❌ WORST PATTERN |

### 🟢 Positive Continuation
| Pattern | Delta | Sample | Verdict |
|---------|-------|--------|---------|
| Asia resolved prior HIGH → London LONG | +0.15R | 200+ | ✅ TRADE |
| Asia resolved prior LOW → London SHORT | +0.15R | 200+ | ✅ TRADE |

### 🟡 Compression Effect
| Pattern | Delta | Sample | Verdict |
|---------|-------|--------|---------|
| Asia failed to resolve → London ORB | ~+0.10R | 200+ | ✅ TRADE |

### 🔵 Clean Asia (No Inventory Interaction)
| Pattern | Delta | Sample | Verdict |
|---------|-------|--------|---------|
| Clean Asia trend → London | Negative | 200+ | ❌ SKIP |

---

## WHAT TO TEST NEXT (Priority Order)

### TEST 1 — Which prior session matters more?

Split Asia resolutions into:
- **Resolved prior NY** (high or low)
- **Resolved prior London** (high or low)

Measure London expectancy separately.

**Hypothesis (likely true):**
Prior NY resolution > prior London

**Implementation:**
```python
# In compute_session_labels.py or similar
if asia_high >= prior_ny_high:
    asia_resolved_prior = "NY_HIGH"
elif asia_low <= prior_ny_low:
    asia_resolved_prior = "NY_LOW"
elif asia_high >= prior_london_high:
    asia_resolved_prior = "LONDON_HIGH"
elif asia_low <= prior_london_low:
    asia_resolved_prior = "LONDON_LOW"
else:
    asia_resolved_prior = "NONE"
```

### TEST 2 — Resolution Depth (No optimization yet)

Label Asia resolution depth:
- **Shallow:** Just tags the level (< 5 ticks beyond)
- **Deep:** Trades ≥ X% of Asia range beyond it (e.g., 20%)

See if London continuation strengthens with deeper resolutions.

**Hypothesis:** Deep resolutions → stronger London continuation

### TEST 3 — Asia Time of Resolution

Label whether Asia resolved inventory:
- **Early:** 09:00–10:00
- **Late:** 10:00–11:00

Late resolution often produces stronger London continuation.

**Hypothesis:** Late resolution → stronger London edge

---

## WHAT NOT TO TOUCH

❌ Do not introduce HH/LL logic
❌ Do not stack Asia filters
❌ Do not mix NY logic here
❌ Do not optimize thresholds yet
❌ **Do not add Asia ORB outcome conditions (WIN/LOSS)**
❌ **Do not mix Engine B (outcome momentum) with Engine A (liquidity)**

Keep it structural. Keep it honest.

---

## TWO ENGINES - DO NOT MIX

### Engine A: Liquidity / Inventory (THIS DOCUMENT)
**What:** Prior-session inventory resolution
**Logic:** Asia resolved prior HIGH → London LONG
**Used for:** Session → Session relationships (Asia → London)
**Data:** Prior NY high/low, prior London high/low
**NOT used:** Asia ORB outcomes (WIN/LOSS)

### Engine B: Outcome Momentum (SEPARATE - see ORB_OUTCOME_MOMENTUM.md)
**What:** Intra-session ORB outcome correlations
**Logic:** 09:00 WIN → 10:00 UP has higher win rate
**Used for:** ORB → ORB within same session (intra-Asia)
**Data:** Previous ORB outcomes (if closed)
**NOT used:** Prior-session inventory

**These are DIFFERENT frameworks. Do not combine them.**

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Label Creation (compute_session_labels.py)

- [ ] Define prior session high/low (NY and London from previous day)
- [ ] Label Asia resolution state:
  - `asia_resolved_prior`: "NY_HIGH" | "NY_LOW" | "LONDON_HIGH" | "LONDON_LOW" | "NONE" | "CLEAN_TREND"
- [ ] Attach to London ORB (18:00)

### Phase 2: Backtest Validation (backtest_asia_london.py)

- [ ] Run London ORB with direction filters:
  - If asia_resolved_prior in ["NY_HIGH", "LONDON_HIGH"] → ONLY trade London UP
  - If asia_resolved_prior in ["NY_LOW", "LONDON_LOW"] → ONLY trade London DOWN
  - If asia_resolved_prior == "NONE" → Trade both directions
  - If asia_resolved_prior == "CLEAN_TREND" → Skip
- [ ] Compare vs baseline (no filters)
- [ ] Verify expected deltas:
  - Continuation: +0.15R
  - Compression: +0.10R
  - Fade (toxic): -0.37R

### Phase 3: Refinement Tests

- [ ] TEST 1: Split NY vs London prior resolution
- [ ] TEST 2: Measure resolution depth
- [ ] TEST 3: Measure resolution timing

### Phase 4: Documentation

- [ ] Update TRADING_RULESET.md with London rules
- [ ] Update TERMINOLOGY_EXPLAINED.md with prior inventory concept
- [ ] Create example scenarios for traders

---

## TRADING EXAMPLES

### Example 1: Asia Resolved Prior NY High

**Setup (09:00-11:00):**
- Prior NY session high: $2,500.00
- Asia session high: $2,501.50 ✅ (swept prior NY high)
- Asia session low: $2,498.00

**Asia State:** Resolved prior HIGH

**London ORB (18:00-18:05):**
- ORB High: $2,502.00
- ORB Low: $2,500.50

**Trading Decision:**
- ✅ TRADE: London UP breaks only (if price breaks above $2,502.00)
- ❌ SKIP: London DOWN breaks (toxic pattern)
- **Expected edge:** +0.15R vs baseline

### Example 2: Asia Resolved Prior London Low

**Setup (09:00-11:00):**
- Prior London session low: $2,498.50
- Asia session high: $2,500.00
- Asia session low: $2,497.80 ✅ (swept prior London low)

**Asia State:** Resolved prior LOW

**London ORB (18:00-18:05):**
- ORB High: $2,499.50
- ORB Low: $2,498.00

**Trading Decision:**
- ✅ TRADE: London DOWN breaks only (if price breaks below $2,498.00)
- ❌ SKIP: London UP breaks (toxic pattern)
- **Expected edge:** +0.15R vs baseline

### Example 3: Asia Failed to Resolve

**Setup (09:00-11:00):**
- Prior NY high: $2,502.00
- Prior London low: $2,497.00
- Asia session high: $2,500.50 (did not reach prior NY high)
- Asia session low: $2,498.50 (did not reach prior London low)

**Asia State:** Failed to resolve (compression)

**London ORB (18:00-18:05):**
- ORB High: $2,501.00
- ORB Low: $2,499.50

**Trading Decision:**
- ✅ TRADE: Both directions (compression → expansion)
- **Expected edge:** ~+0.10R vs baseline

### Example 4: Clean Asia Trend (Skip London)

**Setup (09:00-11:00):**
- Prior NY high: $2,495.00 (far away)
- Prior London low: $2,490.00 (far away)
- Asia session high: $2,501.00
- Asia session low: $2,497.00
- Asia never touched prior inventory (clean uptrend)

**Asia State:** Clean trend (no prior inventory interaction)

**London ORB (18:00-18:05):**
- ORB High: $2,502.00
- ORB Low: $2,500.50

**Trading Decision:**
- ❌ SKIP: Do not trade London at all
- Clean Asia trends with no inventory interaction are toxic for London

---

## KEY TERMINOLOGY

### Prior Inventory
- **Definition:** High/low levels from NY and London sessions of the PREVIOUS trading day
- **Window:** From previous 18:00 through previous 02:00 (next day)
- **Not to be confused with:** Asia highs/lows from the current day

### Resolve
- **Definition:** Price trades through and accepts beyond a prior inventory level
- **Directional:**
  - Resolve HIGH = sweep above prior session high
  - Resolve LOW = sweep below prior session low

### Continuation
- **Definition:** Trading in the direction of Asia's inventory resolution
- **Example:** Asia resolved prior high → London LONG

### Fade (TOXIC)
- **Definition:** Trading against the direction of Asia's inventory resolution
- **Example:** Asia resolved prior high → London SHORT ❌
- **Result:** -0.37R (worst pattern in system)

### Compression
- **Definition:** Asia fails to resolve prior inventory
- **Result:** Range contraction → London expansion
- **Edge:** ~+0.10R

---

## FINAL NOTES

1. **This is structural, not predictive**
   - You're not predicting London direction
   - You're identifying when London has a directional edge based on Asia's work

2. **Never fade the continuation**
   - -0.37R is catastrophic
   - Continuation dominates in inventory-based frameworks

3. **Quality over quantity**
   - Some days you skip London (clean Asia trends)
   - That's correct behavior

4. **Next level is refinement**
   - NY vs London prior resolution split
   - Resolution depth
   - Resolution timing

5. **Keep it honest**
   - No optimization yet
   - No stacking filters
   - Structural first, refinement later

---

## REFERENCES

- `SESSION_CONDITIONAL_EXPECTANCY_REPORT_FINAL.md` - Original analysis
- `TERMINOLOGY_EXPLAINED.md` - Basic concepts
- `TRADING_RULESET.md` - High-confidence rules (to be updated)
