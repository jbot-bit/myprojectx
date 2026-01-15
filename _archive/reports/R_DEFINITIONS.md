# R Definitions - Project Standards

**Date:** 2026-01-12

---

## Two Definitions of R

This project uses **TWO different definitions** of R, depending on context:

---

### 1. Entry-Anchored R (Legacy Backtests)

**Definition:**
```
1R = |entry_price - stop_price|
```

**Used in:**
- Legacy backtest scripts (`backtest_orb_exec_*.py`)
- Historical performance analysis
- `orb_trades_1m_exec` table
- `orb_trades_5m_exec` table

**Characteristics:**
- **Varies per trade** based on entry timing
- Averages **1.3-1.6x ORB size** (see `ACTUAL_1R_ANALYSIS.md`)
- Represents **actual risk** taken when entering a trade
- Entry can be far from ORB edge (slippage, confirmations, etc.)

**Formula for TP:**
```
TP = entry_price ± RR × 1R
TP = entry_price ± RR × |entry_price - stop_price|
```

**Used when:** Calculating historical backtest results or actual trade risk.

---

### 2. ORB-Anchored R (Structural Model)

**Definition:**
```
1R = |ORB_edge - stop_price|

Where ORB_edge = ORB_high (for UP break) or ORB_low (for DOWN break)
```

**Used in:**
- All structural analysis going forward
- MAE/MFE calculations from ORB edge
- Target price (TP) calculations for structural models
- Future strategy implementations

**Characteristics:**
- **Fixed per ORB setup** (independent of entry timing)
- **1R = ORB size** for Full SL mode (stop at opposite edge)
- **1R = 0.5 × ORB size** for Half SL mode (stop at midpoint)
- Represents **structural risk** from ORB boundary

**Formula for TP:**
```
For UP break:
  TP = ORB_high + RR × |ORB_high - stop_price|

For DOWN break:
  TP = ORB_low - RR × |ORB_low - stop_price|
```

**Formula for MAE/MFE:**
```
For UP break:
  MAE = max(0, ORB_high - min_price_after_break) / tick_size
  MFE = max(0, max_price_after_break - ORB_high) / tick_size

For DOWN break:
  MAE = max(0, max_price_after_break - ORB_low) / tick_size
  MFE = max(0, ORB_low - min_price_after_break) / tick_size
```

**Used when:** Analyzing structural behavior, measuring move quality, or computing theoretical outcomes.

---

## Comparison Table

| Aspect | Entry-Anchored R | ORB-Anchored R |
|--------|------------------|----------------|
| **Anchor Point** | Entry price | ORB edge (high/low) |
| **Variability** | Varies per trade | Fixed per setup |
| **Average Size** | 1.3-1.6x ORB | 1.0x ORB (Full SL)<br>0.5x ORB (Half SL) |
| **Use Case** | Historical backtests | Structural analysis |
| **TP Calculation** | From entry price | From ORB edge |
| **MAE/MFE** | From entry price | From ORB edge |
| **Tables** | `orb_trades_*_exec` | Future structural tables |

---

## Important Notes

### ❌ DO NOT say "1R ≠ ORB size" without specifying which definition

**Correct statements:**
- ✅ "Entry-anchored 1R averages 1.5x ORB size"
- ✅ "ORB-anchored 1R equals ORB size for Full SL"
- ✅ "Legacy backtests used entry-anchored R"
- ✅ "Structural model uses ORB-anchored R"

**Incorrect statements:**
- ❌ "1R ≠ ORB size" (ambiguous - which R?)
- ❌ "1R = ORB size" (ambiguous - which R?)

### ✅ Always specify which definition you're using

When writing code, comments, or documentation:
```python
# CORRECT:
# Using ORB-anchored R for structural analysis
r_orb = abs(orb_high - stop_price) / tick_size

# Using entry-anchored R for backtest results
r_entry = abs(entry_price - stop_price) / tick_size

# INCORRECT:
# Calculate 1R
r = abs(entry_price - stop_price) / tick_size  # Which R? Ambiguous!
```

---

## Code Examples

### Entry-Anchored R (Legacy):

```python
# From backtest_orb_exec_5mhalfsl.py
entry_price = close_price_of_break
stop_price = orb_low if direction == "UP" else orb_high

# Entry-anchored 1R
stop_ticks = abs(entry_price - stop_price) / TICK_SIZE

# Target from entry
target_price = entry_price + rr * risk if direction == "UP" else entry_price - rr * risk
```

### ORB-Anchored R (Structural):

```python
# For structural analysis
orb_edge = orb_high if direction == "UP" else orb_low
stop_price = orb_low if direction == "UP" else orb_high

# ORB-anchored 1R
r_orb = abs(orb_edge - stop_price) / TICK_SIZE

# Target from ORB edge
if direction == "UP":
    target_price = orb_edge + rr * r_orb * TICK_SIZE
else:
    target_price = orb_edge - rr * r_orb * TICK_SIZE

# ASSERTION: Ensure TP never references entry_price
assert 'entry_price' not in str(target_price), "TP must be calculated from ORB edge, not entry"
```

---

## MAE/MFE Measurement

### Entry-Anchored (Legacy - DO NOT USE GOING FORWARD):

```python
# From legacy code (orb_trades_*_exec tables)
if direction == "UP":
    mae = max(0, entry_price - min_price) / TICK_SIZE
    mfe = max(0, max_price - entry_price) / TICK_SIZE
else:
    mae = max(0, max_price - entry_price) / TICK_SIZE
    mfe = max(0, entry_price - min_price) / TICK_SIZE
```

### ORB-Anchored (Structural - USE THIS):

```python
# For structural analysis (daily_features_v2)
orb_edge = orb_high if direction == "UP" else orb_low

if direction == "UP":
    mae = max(0, orb_edge - min_price_after_break) / TICK_SIZE
    mfe = max(0, max_price_after_break - orb_edge) / TICK_SIZE
else:
    mae = max(0, max_price_after_break - orb_edge) / TICK_SIZE
    mfe = max(0, orb_edge - min_price_after_break) / TICK_SIZE
```

---

## Migration Guide

### For Existing Code:

1. **Identify which R definition the code uses:**
   - Check if calculations reference `entry_price` or `orb_edge`
   - Add comments specifying which definition

2. **Update structural analysis to use ORB-anchored R:**
   - Replace `entry_price` with `orb_edge` in TP calculations
   - Replace entry-based MAE/MFE with ORB-based MAE/MFE
   - Add assertions to prevent accidental use of entry_price

3. **Keep legacy backtests unchanged:**
   - They use entry-anchored R by design
   - Document this in comments
   - Results are valid for what they measure (actual historical trades)

### For New Code:

**Default to ORB-anchored R** unless explicitly backtesting historical entry performance.

---

## Summary

| When to use... | Entry-Anchored R | ORB-Anchored R |
|----------------|------------------|----------------|
| **Backtesting legacy strategies** | ✅ | ❌ |
| **Analyzing actual trade risk** | ✅ | ❌ |
| **Structural analysis** | ❌ | ✅ |
| **MAE/MFE from structure** | ❌ | ✅ |
| **Theoretical TP calculations** | ❌ | ✅ |
| **New strategy design** | ❌ | ✅ |

**Default for all future work: ORB-anchored R**

---

## Validation Checklist

When writing code that calculates TP or MAE/MFE:

- [ ] Clearly document which R definition is used
- [ ] ORB-anchored: TP calculated from `orb_edge`, never `entry_price`
- [ ] ORB-anchored: MAE/MFE measured from `orb_edge`, never `entry_price`
- [ ] Add assertion to verify TP doesn't reference entry_price
- [ ] Code comments distinguish "entry-anchored" vs "ORB-anchored"
- [ ] Variable names make it clear (e.g., `r_entry` vs `r_orb`)

---

## Final Note

**Both definitions are valid** - they measure different things:
- **Entry-anchored R** measures actual trade risk
- **ORB-anchored R** measures structural move quality

**Use the right one for the job.** Going forward, structural analysis uses ORB-anchored R.
