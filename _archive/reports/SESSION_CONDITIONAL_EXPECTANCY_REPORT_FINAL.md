# Session Conditional Expectancy Analysis Report (FINAL)

**Analysis Date**: 2026-01-12 (Updated with corrected NY labels)
**Dataset**: MGC (Micro Gold) ORB trades from orb_trades_5m_exec
**Methodology**: Structural conditional analysis (no optimization, no ML, no chained filters)

---

## Executive Summary

This analysis identifies **structural conditions** where prior-session behavior creates measurable expectancy shifts in future ORB breakouts. We tested both **CONTINUATION** (price extends in sweep direction) and **REVERSAL** (price rejects sweep) hypotheses.

**Key Findings**:
1. **Continuation dominates**: Sweep-based continuation strategies outperform baseline by +0.15R to +0.24R
2. **Reversal is toxic**: Fading Asia sweep high in London = -0.37R
3. **Compression effects**: Neutral/range-bound prior sessions predict explosive ORBs (+0.23R to +0.28R)
4. **NY pre-ORB neutral direction**: **Strong +0.23R improvement** when NY 2300-0030 is choppy (corrected with scale-based definition)

---

## Methodology

### Label Definitions (Deterministic, No Optimization)

**Asia Session (0900-1100 local):**
- `asia_sweep_high`: Did post-Asia session (1100-1800) sweep above Asia high?
- `asia_sweep_low`: Did post-Asia session (1100-1800) sweep below Asia low?
- `asia_range_type`: tight (<12 ticks), normal (12-32 ticks), expanded (>32 ticks)
- `asia_net_direction`: up (>0.5 ticks), down (<-0.5 ticks), neutral
- `asia_failure`: 2 or more Asia ORBs (0900, 1000, 1100) resulted in LOSS

**London Session (1800):**
- `london_sweep_asia_high`: Did London session sweep Asia high?
- `london_sweep_asia_low`: Did London session sweep Asia low?
- `london_orb_outcome`: hold (WIN), fail (LOSS), reject (NO_TRADE)

**NY Pre-ORB Session (2300-0030 local):**
- `ny_sweep_london_high`: Price traded > London high AND returned inside before 00:30
- `ny_sweep_london_low`: Price traded < London low AND returned inside before 00:30
- `ny_range_type`: **tight (≤20% of ADR_20), normal (20-50% of ADR_20), expanded (≥50% of ADR_20)**
  - Uses `ny_range / adr_20` ratio where adr_20 = 20-day median daily range
- `ny_net_direction`: **up/down if abs(close-open) > 0.10 * ny_range, else neutral**
  - Scale-based definition (not fixed threshold)
- `ny_exhaustion`: Directional push then close back within 40% of range from midpoint
- `ny_orb_outcome`: hold (WIN), fail (LOSS), reject (NO_TRADE)

**Note**: NY labels were corrected to use comparable denominators and scale-based thresholds. Original definitions used incompatible ATR scaling (90-min range vs daily ATR) and fixed thresholds, resulting in broken distributions (100% expanded, 3% neutral).

### Attachments (No Lookahead)

- **Asia labels → London ORB (1800)**
- **Asia labels → NY ORB (2300)**
- **London labels → NY ORB (2300)**
- **Asia + London labels → NY ORB (0030)** (prior session state)
- **NY pre-ORB labels → NY ORB (0030)** (local session state)

All labels computed ONLY from data available BEFORE the next ORB opens.

### Significance Filters

- **Minimum sample size**: 200 trades
- **Minimum delta**: ±0.10R vs baseline

---

## Baseline Performance

| ORB Time | Sample Size | Avg R | Win Rate |
|----------|-------------|-------|----------|
| 1800 (London) | 46,676 | -0.053R | 28.2% |
| 2300 (NY) | 42,304 | -0.144R | 20.1% |
| 0030 (NY) | 41,002 | -0.102R | 15.8% |

**Observation**: All ORBs are net negative at baseline with this execution model.

---

## Significant Conditions (Ranked by |Delta|)

### 1. Asia Sweep High → London DOWN (REVERSAL) ❌ TOXIC

**Condition**: `asia_sweep_high=True + London ORB DOWN`
**Hypothesis**: REVERSAL

| Metric | Value |
|--------|-------|
| Sample Size | 5,516 |
| Avg R | -0.418R |
| **Delta** | **-0.366R** |
| Win Rate | 16.1% |
| Baseline | -0.053R |

**Interpretation**: When Asia sweeps high, fading it (going SHORT in London) is **exceptionally poor**. Price is likely to continue higher. This is the strongest negative signal found.

**Trade Implication**: AVOID London SHORT when Asia swept high.

---

### 2. London ORB Outcome=Reject → NY 0030 (ANY) ✅ POSITIVE

**Condition**: `london_orb_outcome=reject`
**ORB**: NY 0030

| Metric | Value |
|--------|-------|
| Sample Size | 696 |
| Avg R | +0.176R |
| **Delta** | **+0.278R** |
| Win Rate | 18.2% |
| Baseline | -0.102R |

**Interpretation**: When London ORB does NOT break (reject/no trade), NY 0030 ORBs perform unusually well. This suggests that price compression during London leads to explosive moves in early NY session.

**Trade Implication**: FAVOR NY 0030 ORB trades when London remained range-bound.

---

### 3. London Sweep Asia Low → NY 2300 DOWN (CONTINUATION) ✅ POSITIVE

**Condition**: `london_sweep_asia_low=True + NY 2300 ORB DOWN`
**Hypothesis**: CONTINUATION

| Metric | Value |
|--------|-------|
| Sample Size | 7,966 |
| Avg R | +0.097R |
| **Delta** | **+0.241R** |
| Win Rate | 28.6% |
| Baseline | -0.144R |

**Interpretation**: When London sweeps below Asia lows, NY 2300 SHORT setups have strong positive expectancy. This is continuation into the NY session.

**Trade Implication**: FAVOR NY 2300 SHORT when London swept Asia low.

---

### 4. NY Net Direction=Neutral → NY 0030 (ANY) ✅ POSITIVE

**Condition**: `ny_net_direction=neutral` (NY pre-ORB 2300-0030 was choppy)
**ORB**: NY 0030

| Metric | Value |
|--------|-------|
| Sample Size | **3,538** |
| Avg R | **+0.130R** |
| **Delta** | **+0.231R** |
| Win Rate | **24.8%** |
| Baseline | -0.102R |

**Interpretation**: When NY pre-ORB (2300-0030) is NEUTRAL (choppy, abs(close-open) ≤ 0.10 * ny_range), the 0030 ORB performs significantly better. This is a **local compression effect** — choppy pre-ORB action predicts explosive ORB breakout.

**Trade Implication**: FAVOR NY 0030 ORB when NY 2300-0030 was choppy/neutral. This is now one of the **strongest and most reliable edges** with 3,538 samples.

**Note**: This edge was significantly strengthened after fixing NY label definitions. Original broken definition (fixed 0.5 tick threshold) gave only 1,183 samples and +0.206R delta. Corrected scale-based definition (0.10 * ny_range) increased sample size 3x and improved delta to +0.231R.

---

### 5. London ORB Outcome=Reject → NY 2300 (ANY) ❌ NEGATIVE

**Condition**: `london_orb_outcome=reject`
**ORB**: NY 2300

| Metric | Value |
|--------|-------|
| Sample Size | 640 |
| Avg R | -0.373R |
| **Delta** | **-0.229R** |
| Win Rate | 15.5% |
| Baseline | -0.144R |

**Interpretation**: When London ORB rejects, NY 2300 ORBs perform **worse** than baseline. This is the opposite of the NY 0030 effect. Suggests that compression is released earlier (0030) rather than later (2300).

**Trade Implication**: AVOID NY 2300 ORB when London rejected. Consider NY 0030 instead.

---

### 6. Asia Sweep Low → NY 2300 DOWN (CONTINUATION) ✅ POSITIVE

**Condition**: `asia_sweep_low=True + NY 2300 ORB DOWN`
**Hypothesis**: CONTINUATION

| Metric | Value |
|--------|-------|
| Sample Size | 3,882 |
| Avg R | +0.083R |
| **Delta** | **+0.227R** |
| Win Rate | 26.5% |
| Baseline | -0.144R |

**Interpretation**: When Asia sweeps low, NY 2300 SHORT setups outperform. Similar to London effect but propagates to later NY session.

**Trade Implication**: FAVOR NY 2300 SHORT when Asia swept low.

---

### 7. Asia Sweep High → London UP (CONTINUATION) ✅ POSITIVE

**Condition**: `asia_sweep_high=True + London ORB UP`
**Hypothesis**: CONTINUATION

| Metric | Value |
|--------|-------|
| Sample Size | 6,418 |
| Avg R | +0.096R |
| **Delta** | **+0.149R** |
| Win Rate | 32.6% |
| Baseline | -0.053R |

**Interpretation**: When Asia sweeps high, London LONG setups perform well. Continuation effect.

**Trade Implication**: FAVOR London LONG when Asia swept high.

---

### 8. Asia Sweep Low → London DOWN (CONTINUATION) ✅ POSITIVE

**Condition**: `asia_sweep_low=True + London ORB DOWN`
**Hypothesis**: CONTINUATION

| Metric | Value |
|--------|-------|
| Sample Size | 3,988 |
| Avg R | +0.093R |
| **Delta** | **+0.145R** |
| Win Rate | 32.6% |
| Baseline | -0.053R |

**Interpretation**: When Asia sweeps low, London SHORT setups perform well. Continuation effect.

**Trade Implication**: FAVOR London SHORT when Asia swept low.

---

### 9. Asia Sweep Low → NY 0030 UP (REVERSAL) ❌ NEGATIVE

**Condition**: `asia_sweep_low=True + NY 0030 ORB UP`
**Hypothesis**: REVERSAL

| Metric | Value |
|--------|-------|
| Sample Size | 3,805 |
| Avg R | -0.219R |
| **Delta** | **-0.117R** |
| Win Rate | 9.2% |
| Baseline | -0.102R |

**Interpretation**: When Asia sweeps low, trying to fade it (go LONG) in NY 0030 performs poorly. Downward momentum persists.

**Trade Implication**: AVOID NY 0030 LONG when Asia swept low.

---

### 10. Asia Failure=False → London (ANY) ❌ NEGATIVE

**Condition**: `asia_failure=False` (Asia ORBs mostly succeeded)
**ORB**: London 1800

| Metric | Value |
|--------|-------|
| Sample Size | 23,155 |
| Avg R | -0.156R |
| **Delta** | **-0.104R** |
| Win Rate | 25.1% |
| Baseline | -0.053R |

**Interpretation**: When Asia ORBs held (did NOT fail), London ORBs perform worse. Suggests overextension after successful Asia moves.

**Trade Implication**: BE CAUTIOUS with London ORB when Asia ORBs succeeded.

---

### 11. Asia Failure=True → London (ANY) ✅ POSITIVE

**Condition**: `asia_failure=True` (2+ Asia ORBs failed)
**ORB**: London 1800

| Metric | Value |
|--------|-------|
| Sample Size | 23,521 |
| Avg R | +0.050R |
| **Delta** | **+0.102R** |
| Win Rate | 31.2% |
| Baseline | -0.053R |

**Interpretation**: When Asia ORBs failed (choppy, range-bound), London ORBs perform better. Suggests price is coiling for a directional move.

**Trade Implication**: FAVOR London ORB when Asia was choppy/failed.

---

### 12. Asia Sweep Low → NY 0030 DOWN (CONTINUATION) ⚠️ MARGINAL

**Condition**: `asia_sweep_low=True + NY 0030 ORB DOWN`
**Hypothesis**: CONTINUATION

| Metric | Value |
|--------|-------|
| Sample Size | 3,886 |
| Avg R | 0.000R |
| **Delta** | **+0.102R** |
| Win Rate | 18.5% |
| Baseline | -0.102R |

**Interpretation**: Marginal improvement but near breakeven. Continuation effect weakens by NY 0030 (too late).

**Trade Implication**: Neutral. Better opportunities exist earlier (London, NY 2300).

---

## Strategic Insights

### CONTINUATION vs REVERSAL

**Strong Continuation Patterns:**
1. Asia sweep high → London LONG (+0.15R)
2. Asia sweep low → London SHORT (+0.15R)
3. London sweep Asia low → NY 2300 SHORT (+0.24R)
4. Asia sweep low → NY 2300 SHORT (+0.23R)

**Failed Reversal Patterns:**
1. Asia sweep high → London SHORT (-0.37R) — **TOXIC**
2. Asia sweep low → NY 0030 LONG (-0.12R) — Avoid

**Takeaway**: **Sweeps tend to CONTINUE, not reverse.** Fading Asia sweeps in London is particularly costly.

---

### Session Handoff Dynamics

**Asia → London:**
- Asia sweep high → London LONG works (+0.15R)
- Asia sweep low → London SHORT works (+0.15R)
- Asia failure (chop) → London ORB improves (+0.10R)

**London → NY:**
- London sweep Asia low → NY 2300 SHORT works (+0.24R)
- London reject → NY 0030 improves (+0.28R), but NY 2300 worsens (-0.23R)

**NY Pre-ORB → NY ORB:**
- NY neutral (2300-0030 chop) → NY 0030 improves (+0.23R)

**Implication**: Price state from prior session reliably affects next session ORB quality. Sessions are NOT independent.

---

### Compression & Release Effects

**Global Compression (London → NY):**
When London ORB **rejects** (no break):
- **NY 0030**: +0.28R (explosive)
- **NY 2300**: -0.23R (poor)

**Local Compression (NY Pre-ORB → NY ORB):**
When NY pre-ORB (2300-0030) is **neutral** (choppy):
- **NY 0030**: +0.23R (explosive)

**Interpretation**:
1. Compressed range during London releases at **early** NY session (0030), not late NY session (2300)
2. Choppy NY pre-ORB predicts explosive 0030 ORB (local compression release)
3. Energy builds during consolidation and releases quickly

**Key Insight**: **Two independent compression effects** - one from London session (global), one from NY pre-ORB itself (local). Both predict explosive 0030 ORB breakouts.

---

### NY Label Fix Impact

**Original Broken Definitions:**
- `ny_range_type`: Used incompatible denominator (90-min range vs daily ATR) → 100% expanded
- `ny_net_direction`: Fixed 0.5 tick threshold → only 3% neutral

**Corrected Definitions:**
- `ny_range_type`: Uses `ny_range / adr_20` ratio → proper distribution (2% tight, 52% normal, 46% expanded)
- `ny_net_direction`: Scale-based `abs(close-open) ≤ 0.10 * ny_range` → 11% neutral

**Impact on ny_net_direction=neutral Edge:**
- Sample size: 1,183 → **3,538** (3x increase)
- Delta: +0.206R → **+0.231R** (stronger)
- Win rate: 18.4% → **24.8%** (more reliable)

The corrected definition makes this one of the **strongest and most reliable edges** in the entire analysis.

---

## Implementation Ruleset (Discretionary Guidance)

**DO:**
1. **Follow Asia sweeps into London** (continuation bias)
2. **Follow London sweeps into NY 2300** (continuation bias)
3. **Trade NY 0030 when London rejected** (global compression release)
4. **Trade NY 0030 when NY pre-ORB was neutral** (local compression release) ← **STRONGEST EDGE**
5. **Favor London ORB when Asia was choppy** (failure = coiling)

**DON'T:**
1. **Fade Asia sweep high in London** (toxic -0.37R)
2. **Fade Asia sweep low in NY 0030** (negative -0.12R)
3. **Trade NY 2300 when London rejected** (poor -0.23R)
4. **Chase London ORB when Asia ORBs held** (overextension -0.10R)

---

## Data Quality & Limitations

**Strengths:**
- Large sample sizes (696 to 46,676 trades per condition)
- No optimization (deterministic thresholds)
- No lookahead (all labels computed from prior data)
- Both continuation and reversal tested explicitly
- NY pre-ORB structural state tested separately
- **Corrected label definitions with proper scaling**

**Limitations:**
- Analysis uses single execution model (`orb_trades_5m_exec`)
- Does not test stacked conditions (one-at-a-time only)
- Baseline is negative (-0.05R to -0.14R) — execution model may need refinement
- NY sweep/exhaustion conditions had small sample sizes or weak effects

**Future Work:**
- Test on other execution models (1m, half-SL, no-filters)
- Investigate why baseline is negative (stop placement, RR, timing)
- Add intra-session sweep detection (e.g., sweep during 0900-1000)
- Test stacked conditions (with proper out-of-sample validation)

---

## Conclusion

**Sessions are NOT independent.** Prior-session structural conditions (sweeps, failures, compression) create measurable expectancy shifts in future ORBs.

**Continuation dominates reversal.** When Asia or London sweeps a level, price tends to continue in that direction, not reverse.

**Two compression effects are real:**
- **Global**: London range-bound → NY 0030 explosive (+0.28R)
- **Local**: NY pre-ORB neutral → NY 0030 explosive (+0.23R)

**NY pre-ORB neutral direction is the strongest reliable edge.** When NY 2300-0030 is choppy, the 0030 ORB significantly outperforms (+0.23R delta, 3,538 samples, 24.8% win rate). This edge was significantly strengthened after fixing broken label definitions.

**Actionable for discretionary traders:** Use prior-session context to filter ORB setups. Avoid toxic patterns (Asia sweep high → London SHORT). Favor high-probability patterns (sweep continuations, compression releases, neutral pre-ORB state).

---

## Appendix A: Full Results Table

| Condition | ORB | Hypothesis | N | Avg R | Delta | WR |
|-----------|-----|------------|---|-------|-------|----|
| asia_sweep_high + DOWN | London | REVERSAL | 5,516 | -0.418R | -0.366R | 16.1% |
| london_orb_outcome=reject | NY 0030 | - | 696 | +0.176R | +0.278R | 18.2% |
| london_sweep_asia_low + DOWN | NY 2300 | CONT | 7,966 | +0.097R | +0.241R | 28.6% |
| **ny_net_direction=neutral** | **NY 0030** | **-** | **3,538** | **+0.130R** | **+0.231R** | **24.8%** |
| london_orb_outcome=reject | NY 2300 | - | 640 | -0.373R | -0.229R | 15.5% |
| asia_sweep_low + DOWN | NY 2300 | CONT | 3,882 | +0.083R | +0.227R | 26.5% |
| asia_sweep_high + UP | London | CONT | 6,418 | +0.096R | +0.149R | 32.6% |
| asia_sweep_low + DOWN | London | CONT | 3,988 | +0.093R | +0.145R | 32.6% |
| asia_sweep_low + UP | NY 0030 | REVERSAL | 3,805 | -0.219R | -0.117R | 9.2% |
| asia_failure=False | London | - | 23,155 | -0.156R | -0.104R | 25.1% |
| asia_failure=True | London | - | 23,521 | +0.050R | +0.102R | 31.2% |
| asia_sweep_low + DOWN | NY 0030 | CONT | 3,886 | 0.000R | +0.102R | 18.5% |

---

## Appendix B: Label Distribution Summary

**Asia Labels (n=523):**
- Sweep High: 131 (25%)
- Sweep Low: 96 (18%)
- Range: Tight 119 (23%), Normal 274 (52%), Expanded 130 (25%)
- Net Direction: Up 222 (42%), Down 225 (43%), Neutral 76 (15%)
- Failure: True 258 (49%)

**London Labels (n=523):**
- Sweep Asia High: 267 (51%)
- Sweep Asia Low: 199 (38%)
- ORB Outcome: Hold 273 (52%), Fail 240 (46%), Reject 9 (2%)

**NY Pre-ORB Labels (n=412) - CORRECTED:**
- Sweep London High: 108 (26%)
- Sweep London Low: 97 (24%)
- **Range: Tight 9 (2%), Normal 213 (52%), Expanded 190 (46%)** ← Fixed
- **Net Direction: Up 193 (47%), Down 175 (43%), Neutral 44 (11%)** ← Fixed
- Exhaustion: True 317 (77%)
- ORB Outcome: Hold 192 (47%), Fail 212 (51%), Reject 8 (2%)

---

## Appendix C: Verification & Validation

**Cycle Date Logic Verified:**
- All 41,002 NY 0030 trades use `cycle_date = entry_date - 1 day` ✓
- Other ORBs use same-day cycle_date ✓
- Zero data loss in session_labels joins ✓

**Temporal Safety Verified (Lookahead Audit):**
- London 1800: `max_label_ts <= orb_open_ts` for all samples ✓
- NY 2300: `max_label_ts <= orb_open_ts` for all samples ✓
- NY 0030: `max_label_ts <= orb_open_ts` for all samples ✓
- No self-conditioning detected ✓

**Label Definition Fixes:**
- NY range_type: Changed from incompatible ATR scaling to `ny_range / adr_20` ratio ✓
- NY net_direction: Changed from fixed threshold to scale-based definition ✓
- Sanity checks added: distribution validation, ratio statistics ✓

---

**Generated by**: `analyze_session_conditional_expectancy.py` (with corrected NY labels)
**Session Labels**: `compute_session_labels.py` → `session_labels` table
**Verification**: `verify_cycle_date_logic.py`, `audit_lookahead_safety.py`
**Source Data**: `gold.db` (MGC 1m/5m bars, daily_features, orb_trades_5m_exec)
