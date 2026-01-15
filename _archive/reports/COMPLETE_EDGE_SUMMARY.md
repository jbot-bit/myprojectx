# COMPLETE EDGE STATE SUMMARY

**Date:** 2026-01-12
**Analysis:** All edge states discovered vs breakout baseline performance

---

## BREAKOUT BASELINE (1m entry, realistic execution)

| ORB  | Avg R   | Total R | Trades | Status |
|------|---------|---------|--------|--------|
| 1000 | +0.094R | +49.0R  | 523    | ✅ BEST |
| 1800 | +0.062R | +32.5R  | 522    | ✅ POSITIVE |
| 1100 | +0.006R | +3.0R   | 523    | ⚠️ MARGINAL |
| 0900 | -0.025R | -13.0R  | 522    | ❌ NEGATIVE |
| 2300 | -0.360R | -188.0R | 522    | ❌ DISASTER |
| 0030 | -0.396R | -207.0R | 523    | ❌ DISASTER |

---

## EDGE STATES DISCOVERED

### STRICT CRITERIA (Original Discovery):
- Sign skew: ≥60%
- Tail skew: ≥3 ticks
- Frequency: 1-15%
- Sample size: ≥30 days

**Result:** 15 edge states found (mostly in 0030 and 2300 - the LOSING sessions)

### RELAXED CRITERIA (Follow-up Search):
- Sign skew: ≥55%
- Tail skew: ≥2 ticks
- Frequency: 5-20%
- Sample size: ≥25 days

---

## EDGE STATES BY ORB

### 0030 ORB (Baseline: -0.396R) ❌ LOSING
**Strict criteria edge states:**
1. **NORMAL + D_MED + HIGH + HIGH** (TESTED - FAILED)
   - 30 days (5.9%), 70% UP-favored, +44.5 tick skew
   - **Execution test: -0.473R (3 wins, 2 losses, 60% WR but huge losses)**
   - **Verdict: Edge exists but uncapturable with liquidity reaction approach**

2. (Other 0030 states from original discovery - not yet detailed)

---

### 2300 ORB (Baseline: -0.360R) ❌ LOSING
**Strict criteria edge states:**
1. **TIGHT + D_SMALL + MID impulse**
   - 63.6% UP-favored, +30.0 tick median tail skew
   - NOT TESTED YET

2. **WIDE + D_MED**
   - 66% DN-favored, -27.5 tick median tail skew
   - NOT TESTED YET

---

### 1800 ORB (Baseline: +0.062R) ✅ POSITIVE
**Relaxed criteria edge states (just discovered):**
1. **NORMAL + D_SMALL + HIGH + MID** ⭐ STRONGEST
   - 28 days (6.3%), 71.4% UP-favored, +3.2 tick skew
   - **NOT TESTED YET - THIS IS YOUR BEST CANDIDATE**

2. **NORMAL + D_SMALL + MID + MID**
   - 33 days (7.4%), 60.6% UP-favored, +2.8 tick skew
   - NOT TESTED YET

3. **NORMAL + D_SMALL + MID + LOW**
   - 47 days (10.6%), 55.3% UP-favored, +2.3 tick skew
   - NOT TESTED YET

---

### 1000 ORB (Baseline: +0.094R) ✅ BEST
**No edge states found** (relaxed criteria tested)
- Implication: Edge is UNCONDITIONAL
- Trade all 1000 ORB setups with baseline parameters

---

### 1100 ORB (Baseline: +0.006R) ⚠️ MARGINAL
**Not yet searched for edge states**

---

### 0900 ORB (Baseline: -0.025R) ❌ NEGATIVE
**Not yet searched for edge states**

---

## CRITICAL INSIGHT

**Pattern observed:**
1. **LOSING sessions (0030, 2300):** Many strong edge states found (60-70% skew, 30-45 tick asymmetry)
2. **WINNING sessions (1000):** No edge states found (unconditional edge)
3. **WINNING sessions (1800):** Few moderate edge states found (55-71% skew, 2-3 tick asymmetry)

**What this means:**
- LOSING sessions have **strong statistical asymmetry** but **negative baseline** → Edge exists but can't be captured with breakout approach
- WINNING sessions have **weak/no asymmetry** but **positive baseline** → Edge is simpler, works unconditionally

**Implication:** You've been searching for complexity in the wrong place. The SIMPLE edges (1000, 1800 baseline) work. The COMPLEX edges (0030 states) don't translate to execution.

---

## WHAT YOU SHOULD TEST NEXT

### Option 1: Test 1800 ORB State #1 (RECOMMENDED) ⭐
**State:** NORMAL + D_SMALL + HIGH + MID
- Baseline: +0.062R (already positive)
- State: 71.4% UP-favored, +3.2 tick skew
- Sample: 28 days (6.3%)

**Why this is promising:**
- Baseline ALREADY positive (+0.062R)
- State shows strong directional bias (71.4%)
- Moderate tail skew (3.2 ticks)
- You're ADDING to an existing edge, not trying to fix a broken session

**Test approach:**
- Run same automated replay analysis
- Compare state performance vs 1800 baseline
- If state beats baseline significantly → trade state only
- If state matches baseline → trade all 1800 setups

---

### Option 2: Trade 1000 + 1800 Baseline (No States)
**1000:** All setups, RR=4.0, +0.094R avg
**1800:** All setups, RR=1.5, +0.062R avg

**Combined expectancy:**
- (523 trades × 0.094R) + (522 trades × 0.062R) = +49.0R + +32.5R = +81.5R over 2 years
- Average per trade: +81.5R / 1045 trades = **+0.078R avg**
- With slippage (-0.026R): **+0.052R net per trade**

**100 trades = +5.2R profit** (thin but viable)

---

### Option 3: Abandon State Filtering, Trade Baselines Only
**Accept that:**
- Edge states exist but don't improve execution
- Simple breakout edges work (1000, 1800)
- Complexity doesn't help

**Action:**
- Trade 1000 ORB (all setups, RR=4.0)
- Trade 1800 ORB (all setups, RR=1.5)
- Skip state filtering entirely

---

## YOUR QUESTION: "What about new implementation states?"

**Need clarification:** What do you mean by "new implementation states"?

Possible interpretations:
1. The edge states we just discovered for 1800 ORB?
2. A different state definition approach you had in mind?
3. Implementation-specific states (related to execution quality)?
4. Something else?

Please clarify and I'll address it.

---

## RECOMMENDATION

**Test 1800 ORB State #1 (NORMAL + D_SMALL + HIGH + MID)**

**Why:**
- Baseline already positive (+0.062R)
- Strongest state found (71.4% UP, +3.2 ticks)
- Testing adds conditional edge to existing baseline
- Low risk: If state fails, fall back to 1800 baseline

**Action:**
```bash
python prepare_manual_replay_1800.py
# Modify from 0030 script, use state: NORMAL + D_SMALL + HIGH + MID
python run_automated_replay_1800.py
```

**Decision criteria:**
- If state shows +0.15R or better → trade state only
- If state shows +0.05R to +0.15R → marginal improvement, trade state
- If state shows negative → abandon state, trade 1800 baseline

**Do you want me to run this test?**
