# Logic Audit Findings

## Issue Summary

The robustness test script (`run_robustness_batch_OPTIMIZED.py`) has **INCORRECT buffer logic** compared to the original filtered backtest.

---

## Filter Behavior (Correct in Robustness Script)

### 1. MAX_STOP Filter
**Original:**
```python
if stop_ticks > MAX_STOP_TICKS:
    skipped_big_stop += 1
    continue  # SKIP TRADE ENTIRELY
```

**Robustness (with MAX_STOP=999999):**
```python
if stop_ticks > 999999:  # Never true
    continue
```

**✓ CORRECT:** When we set MAX_STOP=999999, we're including trades that would have been skipped. This tests whether the edge exists on ALL trades, not just those with narrow stops.

### 2. ASIA_TP_CAP Filter
**Original:**
```python
if is_asia(orb):
    cap = ASIA_TP_CAP_TICKS * TICK_SIZE
    if direction == "UP":
        target_price = min(target_price, entry_price + cap)
    else:
        target_price = max(target_price, entry_price - cap)
    # Trade still happens with capped target
```

**Robustness (with ASIA_TP_CAP=999999):**
```python
if is_asia(orb_code):
    reward = min(reward, 999999 * TICK_SIZE)  # Never caps
```

**✓ CORRECT:** We're testing with uncapped targets to see if edge exists without the cap.

---

## Buffer Logic (INCORRECT in Robustness Script)

### Original Filtered Backtest Logic

```python
# Full SL mode
if sl_mode == "full":
    stop_price = orb_low if direction == "UP" else orb_high
    # NO BUFFER APPLIED - stop at exact ORB edge

# Half SL mode
elif sl_mode == "half":
    mid = (orb_high + orb_low) / 2.0
    buf = buffer_ticks * TICK_SIZE

    if direction == "UP":
        stop_price = max(orb_low, mid - buf)
        # mid - buf moves stop DOWN (tighter)
        # max() prevents going below orb_low
    else:
        stop_price = min(orb_high, mid + buf)
        # mid + buf moves stop UP (tighter)
        # min() prevents going above orb_high
```

**Key points:**
- **Full SL:** Buffer is IGNORED, stop is exactly at ORB edge
- **Half SL:** Buffer moves stop away from mid (making it tighter), clamped at ORB edge
- **Buffer = 0:** Stop at mid
- **Buffer = 5:** Stop 5 ticks away from mid (toward ORB edge)
- **Buffer = 20:** Stop 20 ticks from mid (possibly at ORB edge if clamped)

### Robustness Script Logic (WRONG!)

```python
# Half SL mode
if sl_mode == 'half':
    orb_mid = (orb_high + orb_low) / 2.0
    if direction == "UP":
        stop_price = orb_mid - buffer_ticks * TICK_SIZE
        # NO CLAMPING - stop can go below orb_low!
    else:
        stop_price = orb_mid + buffer_ticks * TICK_SIZE
        # NO CLAMPING - stop can go above orb_high!

# Full SL mode
else:  # full
    if direction == "UP":
        stop_price = orb_low - buffer_ticks * TICK_SIZE
        # Buffer APPLIED - moves stop WIDER!
    else:
        stop_price = orb_high + buffer_ticks * TICK_SIZE
        # Buffer APPLIED - moves stop WIDER!
```

**Key problems:**
1. **Full SL:** Buffer is applied (should be ignored!)
2. **Full SL:** Buffer makes stop WIDER instead of being ignored
3. **Half SL:** No clamping at ORB edge (can go beyond ORB range)
4. **Half SL:** Direction of buffer same, but no boundary check

---

## Impact Assessment

### How Bad Is This?

**VERY BAD.** The robustness test was testing DIFFERENT LOGIC than the filtered backtest.

### What Trades Were Affected?

1. **Full SL configs with buffer > 0:**
   - Original: Stop at ORB edge (buffer ignored)
   - Robustness: Stop BEYOND ORB edge (wider, worse risk/reward)
   - **Impact:** Makes configs look WORSE than they are

2. **Half SL configs with large buffer:**
   - Original: Stop clamped at ORB edge
   - Robustness: Stop can go beyond ORB edge
   - **Impact:** Makes configs look WORSE (wider stops)

3. **Half SL configs with buffer = 0:**
   - Both: Stop at mid
   - **Impact:** CORRECT ✓

### Example Calculation

**ORB:** High = 2500.0, Low = 2490.0, Mid = 2495.0, Range = 10.0 ticks
**Entry:** 2502.0 (UP break)
**Buffer:** 20 ticks (2.0 points)
**SL Mode:** Full

**Original Logic (CORRECT):**
```
stop_price = orb_low = 2490.0
stop_ticks = |2502.0 - 2490.0| / 0.1 = 120 ticks
```

**Robustness Logic (WRONG):**
```
stop_price = orb_low - buffer = 2490.0 - 2.0 = 2488.0
stop_ticks = |2502.0 - 2488.0| / 0.1 = 140 ticks
```

**Difference:** 20 ticks wider stop! This makes the config look worse and may trigger MAX_STOP filter differently.

---

## Configs Affected

From `candidate_configs.json`, count of configs by SL mode:
- **Full SL with buffer > 0:** ~30 configs (WRONG)
- **Full SL with buffer = 0:** ~6 configs (CORRECT)
- **Half SL with any buffer:** ~33 configs (PARTIALLY WRONG - no clamping)

**~63 of 69 configs tested with incorrect logic!**

---

## What This Means for Results

### Current Results Are INVALID

The finding "zero configs have positive expectancy" is based on incorrect stop loss calculations.

**Possible outcomes after fix:**
1. Results might be BETTER (stops were too wide)
2. Results might be WORSE (if clamping was helping)
3. Results might be SAME for buffer=0 configs

### We Need To:

1. ✅ Fix the buffer logic in robustness script
2. ✅ Re-run all 69 configs with correct logic
3. ✅ Compare results before/after fix
4. ✅ Re-analyze findings

---

## Root Cause

The original `run_robustness_batch.py` was likely copied from a different backtest script that had different buffer logic. Nobody verified that the buffer calculations matched the filtered backtest exactly.

**Lesson:** Always diff critical logic between scripts when copying.

---

## Next Steps

1. Create fixed version: `run_robustness_batch_FIXED.py`
2. Add validation to ensure logic matches exactly
3. Re-run all 69 configs
4. Compare old vs new results
5. Generate corrected analysis

---

## Validation Checklist

Before trusting ANY backtest results:

- [ ] Buffer logic matches between filtered and unfiltered versions
- [ ] Filter behavior matches (skip vs cap)
- [ ] Entry logic identical
- [ ] Outcome scanning identical
- [ ] Stop/target calculations identical
- [ ] R-multiple calculations identical
- [ ] Edge cases handled identically (both hit same bar, etc.)
