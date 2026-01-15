# MODEL B REBUILD - OVERNIGHT BATCH JOB

## Problem Discovered

Your current `daily_features_v2_half` table uses **ORB-anchored risk** instead of **entry-anchored risk**.

This creates **fake edges** on tiny ORBs (like 0900 with 1.7 tick median) because:
- Entry slippage often reaches target instantly → inflated win rate
- Real risk is 2-3x larger than backtest shows → terrible real R:R

**Example from 0900:**
- Backtest shows: +0.431R on 740 trades
- Reality: Entry slippage makes real risk 2-3x larger, making this edge unprofitable

## Solution: Model B Execution (LOCKED)

**Model B** is the correct execution model:

1. **ORB**: 5 minutes (e.g., 00:30-00:35 Brisbane)
2. **Trigger**: Wait for 1m close outside ORB (with optional buffer)
3. **Entry**: Next 1m bar OPEN (not the close)
4. **Risk**: |entry - stop| (ENTRY-ANCHORED, not ORB-edge-to-stop)
5. **Target**: entry ± (R × RR)
6. **Same-bar rule**: If TP and SL both hit in same bar → LOSS

## How to Rebuild (Overnight)

### Step 1: Run the batch script

Open CMD and run:
```cmd
cd C:\Users\sydne\OneDrive\myprojectx
OVERNIGHT_REBUILD_MODELB.bat
```

This will:
1. Rebuild `daily_features_v3_modelb` (full-SL, entry-anchored)
2. Rebuild `daily_features_v3_modelb_half` (half-SL, entry-anchored)
3. Create convenience views (`v_orb_trades_v3_modelb`, `v_orb_trades_v3_modelb_half`)
4. Verify results are correct

**Estimated time:** 30-60 minutes (depending on CPU)

### Step 2: After rebuild completes

Check the verification output to ensure:
- Risk is entry-anchored (not ORB-anchored)
- Results are likely worse than old table (expected - old table was inflated)

### Step 3: Re-run edge discovery

Use the NEW tables for all analysis:
- **DO USE**: `v_orb_trades_v3_modelb_half` (correct, entry-anchored)
- **DO NOT USE**: `v_orb_trades_half` (WRONG, ORB-anchored, fake edges)

Example query:
```python
# Correct way (Model B)
results = con.execute("""
    SELECT
        orb_time,
        COUNT(*) as n_trades,
        AVG(r_multiple) as avg_r
    FROM v_orb_trades_v3_modelb_half
    WHERE break_dir IN ('UP', 'DOWN')
        AND outcome IN ('WIN', 'LOSS')
    GROUP BY orb_time
""").df()
```

## Files Created

- `build_daily_features_v3_modelb.py` - Feature builder with Model B execution
- `OVERNIGHT_REBUILD_MODELB.bat` - Batch script to rebuild everything
- `create_v3_modelb_views.py` - Creates convenience views
- `verify_modelb_results.py` - Verifies results are correct

## Expected Results

**0900 ORB with half-SL:**
- OLD (ORB-anchored): ~+0.43R on 740 trades (FAKE EDGE)
- NEW (entry-anchored): Likely negative or near zero (REALITY)

This is GOOD - it means you're not trading fake edges caused by incorrect math.

## Next Steps After Rebuild

1. Re-run 0900/1000/1100 analysis with new tables
2. Check if any real edges exist with correct execution
3. Focus on larger ORBs (1800, 0030) where entry slippage is less problematic
4. Consider testing with buffer_ticks to reduce entry slippage

## Why This Matters

**Old calculation (WRONG):**
```
ORB = 1.7 ticks
Risk = ORB_mid to ORB_edge = 0.85 ticks (WRONG)
Entry slippage = 1-2 ticks
Real risk = 1.85-2.85 ticks = 2-3x backtest risk!
```

**New calculation (CORRECT):**
```
ORB = 1.7 ticks
Entry = Next bar open after trigger
Risk = |entry - stop| = actual distance (CORRECT)
No inflation, no fake edges
```

---

## Questions?

If rebuild fails or results look wrong, check:
1. Do you have bars_1m data for 2024-01-01 to 2026-01-10?
2. Did the script complete without errors?
3. Does verification show entry-anchored risk?

Run `verify_modelb_results.py` to diagnose issues.
