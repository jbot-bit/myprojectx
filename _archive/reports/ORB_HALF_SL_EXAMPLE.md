# ORB HALF SL - TARGET CALCULATION EXPLAINED

## Example: MGC 11:00 ORB

### ORB Levels
```
ORB High:    2050.00
ORB Low:     2049.00
ORB Size:    1.00 (100 ticks)
ORB Midpoint: 2049.50
```

---

## LONG SETUP (Price breaks above High)

### Step 1: Entry
- **Entry Price:** 2050.00 (at ORB High - DO NOT CHASE)

### Step 2: Stop Placement (HALF SL)
- **Stop Loss:** 2049.50 (ORB Midpoint)
- This is HALF the ORB size away from entry

### Step 3: Calculate Risk (1R)
```
Risk (1R) = Entry - Stop
         = 2050.00 - 2049.50
         = 0.50 points
         = 50 ticks
         = $5.00 per contract (MGC)
```

### Step 4: Calculate Target (2R for MGC day ORBs)
```
Target Distance = Risk × RR Multiplier
                = 0.50 × 2.0
                = 1.00 points

Target Price = Entry + Target Distance
             = 2050.00 + 1.00
             = 2051.00
```

### Visual Diagram
```
2051.00  ← TARGET (2R) ★ +$10/contract profit
   ↑
   | 1.00 pts (2R reward)
   |
2050.00  ← ENTRY (ORB High) ◄── YOU ENTER HERE
   |
   | 0.50 pts (1R risk)
   ↓
2049.50  ← STOP LOSS (Midpoint) ✗ -$5/contract loss
   |
   | (other half of ORB)
   |
2049.00  ← ORB Low
```

---

## SHORT SETUP (Price breaks below Low)

### Step 1: Entry
- **Entry Price:** 2049.00 (at ORB Low - DO NOT CHASE)

### Step 2: Stop Placement (HALF SL)
- **Stop Loss:** 2049.50 (ORB Midpoint)
- This is HALF the ORB size away from entry

### Step 3: Calculate Risk (1R)
```
Risk (1R) = Stop - Entry
         = 2049.50 - 2049.00
         = 0.50 points
         = 50 ticks
         = $5.00 per contract
```

### Step 4: Calculate Target (2R)
```
Target Distance = Risk × RR Multiplier
                = 0.50 × 2.0
                = 1.00 points

Target Price = Entry - Target Distance
             = 2049.00 - 1.00
             = 2048.00
```

### Visual Diagram
```
2050.00  ← ORB High
   |
   | (other half of ORB)
   |
2049.50  ← STOP LOSS (Midpoint) ✗ -$5/contract loss
   ↑
   | 0.50 pts (1R risk)
   |
2049.00  ← ENTRY (ORB Low) ◄── YOU ENTER HERE
   |
   | 1.00 pts (2R reward)
   ↓
2048.00  ← TARGET (2R) ★ +$10/contract profit
```

---

## KEY POINTS

✅ **Risk = HALF of ORB size** (entry to midpoint)
✅ **Reward = 2× Risk = FULL ORB size** (entry to target)
✅ **Risk/Reward Ratio = 1:2** (risk $5 to make $10)
✅ **Target is ORB-ANCHORED** - measured from entry, not from where price is now

---

## WHY IT WORKS

With HALF SL mode:
- You **risk 0.5 ORB** (50 ticks)
- You **target 1.0 ORB** (100 ticks)
- Your **reward is 2× your risk**
- Your **stop is tighter** (better risk management)
- You're targeting the **same distance** as the ORB's natural range

---

## EXAMPLE WITH REAL NUMBERS

If ORB is 100 ticks:
- Risk: 50 ticks = $5/contract (MGC)
- Reward: 100 ticks = $10/contract
- Trade 3 contracts risking $150 total
- Win: Make $300 (+2R)
- Lose: Lose $150 (-1R)

**Win Rate needed:** 33.3% to break even (you're getting 2:1)

**Your actual win rate:** 31.8% - 36.0% depending on session

**Expected profit:** Positive because some winners go beyond 2R!

---

## MGC ORB CONFIGS SUMMARY

| ORB | RR | Stop | Your Risk | Your Target |
|-----|----|----|----------|-------------|
| 0900 (Tier B) | 2.0 | HALF | 0.5× ORB | 1.0× ORB |
| 1000 | 2.0 | HALF | 0.5× ORB | 1.0× ORB |
| **1100** | **2.0** | **HALF** | **0.5× ORB** | **1.0× ORB** ← YOU'RE HERE |
| 1800 | 2.0 | HALF | 0.5× ORB | 1.0× ORB |

All MGC day/London ORBs use the same setup!

---

**Ready for your 1100 ORB trade? Mark your ORB levels on the chart and wait for the 1-minute breakout!** 🎯
