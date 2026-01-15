# TRADING APP VISUAL GUIDE

**Quick Reference for Live Trading Hub**
**Date**: 2026-01-13

---

## APP OVERVIEW

Two apps are available:

### 1. ORB Analysis Dashboard (`app_trading_hub.py` - root)
- **Purpose**: Research, backtest analysis, AI assistant
- **Use**: Historical data exploration, pattern discovery
- **Launch**: `streamlit run app_trading_hub.py`

### 2. Live Trading Hub (`trading_app/app_trading_hub.py`)
- **Purpose**: Real-time strategy evaluation and trade execution
- **Use**: Live monitoring, alerts, position management
- **Launch**: `cd trading_app && streamlit run app_trading_hub.py`

---

## LIVE TRADING HUB - QUICK START

### Launch the App
```bash
cd trading_app
streamlit run app_trading_hub.py
```

### Initial Setup

1. **Sidebar Settings**:
   - Select instrument (MGC default)
   - Set account size ($100k default)
   - Click "Initialize/Refresh Data"

2. **Data Status**:
   - Shows last bar timestamp
   - Shows last price
   - Auto-refresh every 5 seconds (toggle on/off)

3. **Main Tabs**:
   - 🔴 LIVE: Current strategy evaluation
   - 📊 LEVELS: Session high/low levels
   - 📋 TRADE PLAN: Active setups
   - 📓 JOURNAL: Trade log

---

## 🔴 LIVE TAB - STRATEGY EVALUATION

### What You See

**Strategy Status Card** (Top):
```
╔════════════════════════════════════════════════════╗
║ 🎯 CASCADE                          Priority: 1   ║
║ State: PREPARING                                   ║
║ Action: PREPARE                                    ║
║                                                    ║
║ Reasons:                                          ║
║ • London swept Asia high (gap 12.3pts)           ║
║ • Gap > 9.5pts (LARGE GAP)                       ║
║ • Watching for second sweep at 23:00             ║
║                                                    ║
║ Next Instruction:                                 ║
║ Watch for close > 2156.5 (London high)           ║
║                                                    ║
║ Entry: $2156.50 | Stop: $2150.25                 ║
║ Risk: 0.25% of account                            ║
╚════════════════════════════════════════════════════╝
```

### Strategy States

| State | Meaning | What To Do |
|-------|---------|------------|
| **INVALID** | Strategy not applicable | Wait for different conditions |
| **PREPARING** | Structure forming | Monitor, get ready |
| **READY** | All conditions met | **ENTER TRADE** |
| **ACTIVE** | Position open | Manage position |
| **EXITED** | Trade closed | Review outcome |

### Actions

| Action | Icon | Meaning |
|--------|------|---------|
| STAND_DOWN | ⏸️ | Do nothing, no setup |
| PREPARE | 👀 | Watch, setup forming |
| **ENTER** | 🎯 | **Execute trade now** |
| MANAGE | 📊 | Manage open position |
| EXIT | ❌ | Close position |

---

## STRATEGY HIERARCHY (Priority Order)

### 1. CASCADE (Priority 1) - PRIMARY
**Edge**: +1.95R avg, 9.3% days

**Setup**:
1. London swept Asia level (first sweep)
2. Gap > 9.5pts (LARGE GAP filter)
3. At 23:00, NY sweeps London level (second sweep)
4. Acceptance failure (close back inside within 3 bars)

**Entry**: On retrace to London level
**Stop**: Below second sweep
**Target**: 2R
**Risk**: 0.25% of account

**Visual Indicators**:
- Green line: Asia high/low
- Blue line: London high/low
- Red line: NY open
- Gap annotation: "GAP: 12.3pts"

### 2. PROXIMITY PRESSURE (Priority 2) - DISABLED
**Edge**: FAILED (-0.50R avg)

**Status**: Disabled by default
**Reason**: No validated edge
**Action**: Skip (use higher/lower tier strategies)

### 3. NIGHT ORB (Priority 3) - TERTIARY
**Edge**: +0.387R (23:00), +0.231R (00:30)

**Setup**:
- 23:00 ORB: 23:00-23:05 range
- 00:30 ORB: 00:30-00:35 range

**Entry**: First 1-minute close outside ORB
**Stop**: HALF (ORB midpoint)
**Target**: Entry + 1.0R
**Risk**: 0.10-0.25% of account

**Configuration** (from config.py):
```python
"2300": {"rr": 1.0, "sl_mode": "HALF", "tier": "NIGHT"},
"0030": {"rr": 1.0, "sl_mode": "HALF", "tier": "NIGHT"},
```

**Visual Indicators**:
- ORB box: Yellow rectangle (23:00-23:05)
- ORB high/low: Dashed lines
- Entry trigger: Green arrow (first close outside)

### 4. SINGLE LIQUIDITY (Priority 4) - BACKUP
**Edge**: +1.44R avg, 16% days

**Setup**:
- London high swept at 23:00
- NO Asia-London cascade structure
- Acceptance failure within 3 bars
- Entry on retrace to London level

**Risk**: 0.25% of account

### 5. DAY ORB (Priority 5) - BASELINE
**Edge**: +0.27R to +0.34R depending on ORB

**Setup**:
- 09:00 ORB: +0.431R avg (RR=1.0)
- 10:00 ORB: +0.342R avg (RR=3.0)
- 11:00 ORB: +0.449R avg (RR=1.0)

**Entry**: First close outside ORB
**Configuration**:
```python
"0900": {"rr": 1.0, "sl_mode": "FULL", "tier": "DAY"},
"1000": {"rr": 3.0, "sl_mode": "FULL", "tier": "DAY"},
"1100": {"rr": 1.0, "sl_mode": "FULL", "tier": "DAY"},
```

---

## 📊 LEVELS TAB

Shows current session levels:

```
╔════════════════════════════════════════════════════╗
║ SESSION LEVELS                                     ║
╠════════════════════════════════════════════════════╣
║ ASIA (09:00-17:00)                                ║
║   High: $2158.50                                  ║
║   Low:  $2148.20                                  ║
║   Range: 10.3 pts                                 ║
╠════════════════════════════════════════════════════╣
║ LONDON (18:00-23:00)                              ║
║   High: $2165.80  ⬆️ +7.3pts from Asia           ║
║   Low:  $2151.40                                  ║
║   Range: 14.4 pts                                 ║
╠════════════════════════════════════════════════════╣
║ NY (23:00-02:00)                                  ║
║   High: $2168.20  ⬆️ +2.4pts from London         ║
║   Low:  $2160.10                                  ║
║   Range: 8.1 pts                                  ║
╚════════════════════════════════════════════════════╝
```

**Sweep Indicators**:
- ⬆️ Upside sweep (high > previous session high)
- ⬇️ Downside sweep (low < previous session low)
- Gap value shown

---

## 📋 TRADE PLAN TAB

Active setups and watchlist:

```
╔════════════════════════════════════════════════════╗
║ ACTIVE SETUPS                                      ║
╠════════════════════════════════════════════════════╣
║ ✅ CASCADE - READY                                 ║
║   Entry: $2165.80                                 ║
║   Stop: $2159.55                                  ║
║   Target: $2178.30                                ║
║   Risk: $250 (0.25% of $100k)                     ║
║   Contracts: 4 (MGC @ $10/pt)                     ║
╠════════════════════════════════════════════════════╣
║ 👀 23:00 ORB - PREPARING                          ║
║   ORB: $2165.80 - $2161.20 (4.6pts)              ║
║   Entry UP: > $2165.80 (on close)                ║
║   Entry DOWN: < $2161.20 (on close)              ║
║   Watching for breakout...                        ║
╚════════════════════════════════════════════════════╝
```

---

## 📓 JOURNAL TAB

Trade log and execution history:

| Time | Strategy | Action | Price | Status | Notes |
|------|----------|--------|-------|--------|-------|
| 23:05 | CASCADE | ENTER | $2165.80 | FILLED | Long 4 MGC |
| 23:12 | CASCADE | MANAGE | $2168.20 | OPEN | +$96 unrealized |
| 23:28 | CASCADE | EXIT | $2178.50 | FILLED | +2.1R, $508 profit |

**Export Options**:
- Download CSV
- Copy to clipboard
- View stats summary

---

## CORRECT ORB CALCULATIONS (CANONICAL)

### Entry Method (NON-NEGOTIABLE)
```
✅ CORRECT: Entry = first 1-minute CLOSE outside ORB
❌ WRONG:   Entry = ORB high/low (ORB edge entry - INVALID)
```

### Example ORB Trade:

**23:00 ORB**:
- ORB window: 23:00-23:05
- ORB high: $2165.80
- ORB low: $2161.20
- ORB midpoint: $2163.50

**Scenario**: Upside breakout at 23:06
- First 1-minute close: $2166.30 (0.50pts above ORB high)
- Entry price: **$2166.30** ← At CLOSE, not ORB high
- Stop (HALF mode): $2163.50 (ORB midpoint)
- Risk: $2166.30 - $2163.50 = **$2.80**
- Target (RR=1.0): $2166.30 + $2.80 = **$2169.10**

**Position Sizing**:
- Account: $100,000
- Risk: 0.25% = $250
- Risk per contract: $2.80 × $10/pt = $28
- Contracts: $250 / $28 = **8 contracts**

### Visual Representation:

```
Price
 │
 │   Target: $2169.10 ────────────────────────  ← Entry + 1.0R
 │                            ┌─────┐
 │   Entry: $2166.30 ─────────┘     │          ← First CLOSE outside ORB
 │                                   │
 │   ORB High: $2165.80 ──────────  │  ORB     ← NOT the entry!
 │                                ▲  │
 │                                │  │
 │                                │  │
 │   Stop: $2163.50 ──────────────── │          ← ORB midpoint (HALF SL)
 │                                │  │
 │                                │  │
 │   ORB Low: $2161.20 ───────────  │  ORB
 │                                   │
 │                            └─────┘
 │
 └──────────────────────────────────────────> Time
    23:00  23:05        23:06
           ORB ends     Entry triggered
```

---

## RISK MANAGEMENT

### Position Size Calculator

**Formula**:
```
Contracts = (Account × Risk%) / (Stop Distance × Point Value)
```

**Example** (23:00 ORB):
- Account: $100,000
- Risk: 0.25% = $250
- Stop distance: $2.80
- Point value: $10 (MGC)
- Contracts: $250 / ($2.80 × $10) = **8 contracts**

### Risk Limits by Strategy:

| Strategy | Min | Max | Default |
|----------|-----|-----|---------|
| CASCADE | 0.10% | 0.25% | 0.25% |
| PROXIMITY | 0.10% | 0.50% | 0.25% |
| NIGHT_ORB | 0.25% | 0.50% | 0.50% |
| SINGLE_LIQ | 0.25% | 0.50% | 0.25% |
| DAY_ORB | 0.10% | 0.25% | 0.10% |

**Rule**: Never risk more than max limit per strategy
**Protection**: App enforces limits automatically

---

## CHART INTERPRETATION

### Price Chart Annotations:

**Session Boxes**:
- 🟩 Green: Asia session (09:00-17:00)
- 🟦 Blue: London session (18:00-23:00)
- 🟥 Red: NY session (23:00-02:00 next day)

**Levels**:
- Solid line: Current session high/low
- Dashed line: ORB high/low
- Dot-dashed: Previous session levels

**Sweep Indicators**:
- ⬆️ Upside sweep: Price exceeded previous high
- ⬇️ Downside sweep: Price broke previous low
- Gap annotation: Distance between levels

**Entry Signals**:
- 🟢 Green arrow: Long entry (close above ORB)
- 🔴 Red arrow: Short entry (close below ORB)
- 🟡 Yellow box: ORB formation window

---

## ALERTS & NOTIFICATIONS

### Strategy State Changes:

| From | To | Alert |
|------|-----|-------|
| INVALID | PREPARING | 🟡 "Setup forming - watch" |
| PREPARING | READY | 🟢 "Entry conditions met - TRADE" |
| READY | ACTIVE | ✅ "Position opened" |
| ACTIVE | EXITED | 🔵 "Trade closed" |

### Priority Conflicts:

When higher-priority strategy activates:
```
⚠️ CASCADE (Priority 1) active
   → Night ORB (Priority 3) DISABLED

Do NOT trade lower-priority strategies
when higher priority is active!
```

---

## DATA REFRESH

### Auto-Refresh (Recommended):
- Interval: 5 seconds
- Updates: Price, levels, strategy state
- Performance: Low impact

### Manual Refresh:
- Button: "Initialize/Refresh Data" (sidebar)
- Use when: Data connection lost or stale
- Reloads: Last 48 hours of data

---

## TROUBLESHOOTING

### "No data available"
**Solution**: Click "Initialize/Refresh Data" in sidebar

### "Strategy evaluation error"
**Solution**: Check data connection, refresh data

### "ORB not forming"
**Solution**: Wait for ORB window to complete (5 minutes)

### "Entry price at ORB edge" error
**Solution**: This is a bug - report immediately! Entry must be at CLOSE, not ORB edge.

### Position size = 0
**Solution**: Increase risk % or check stop distance

---

## KEYBOARD SHORTCUTS

| Key | Action |
|-----|--------|
| R | Refresh data |
| E | Toggle auto-refresh |
| J | Jump to journal |
| L | Jump to levels |
| T | Jump to trade plan |

---

## BEST PRACTICES

### 1. Pre-Market Setup (Before 09:00):
- Launch app
- Initialize data
- Check yesterday's journal
- Review session levels

### 2. Session Monitoring:
- 09:00-17:00: Watch Day ORBs (09:00, 10:00, 11:00)
- 18:00-23:00: Watch for Asia→London sweep (cascade setup)
- 23:00-02:00: Watch Night ORBs (23:00, 00:30) and cascade confirmation

### 3. Trade Execution:
- Wait for **READY** state
- Verify entry price is NOT at ORB edge
- Check position size calculation
- Enter trade on next bar
- Log in journal immediately

### 4. Position Management:
- Monitor unrealized P&L
- Check if stop/target hit
- Update journal on exit
- Review trade outcome

### 5. End of Day:
- Export journal to CSV
- Review win rate and R-multiples
- Note any pattern changes
- Plan next day

---

## CONFIGURATION

All settings in `trading_app/config.py`:

### Update ORB Parameters:
```python
ORB_CONFIGS = {
    "2300": {"rr": 1.0, "sl_mode": "HALF", "tier": "NIGHT"},
    # ... edit values here
}
```

### Update Risk Limits:
```python
RISK_LIMITS = {
    "CASCADE": {"min": 0.10, "max": 0.25, "default": 0.25},
    # ... edit percentages here
}
```

### Update Refresh Rate:
```python
DATA_REFRESH_SECONDS = 5  # Change to 10 for slower updates
```

---

## SUPPORT & DOCUMENTATION

### Files:
- Strategy logic: `trading_app/strategy_engine.py`
- Data loading: `trading_app/data_loader.py`
- Calculations: `trading_app/utils.py`
- Main app: `trading_app/app_trading_hub.py`

### Reports:
- ORB parameters: `canonical_session_parameters.csv`
- Strategy hierarchy: `STRATEGY_HIERARCHY_FINAL.md`
- Trading playbook: `TRADING_PLAYBOOK_COMPLETE.md`
- Execution engine: `execution_engine.py`

### Validation:
- Entry method: `execution_engine.py` (LINE 291-292)
- Canonical engine: `build_daily_features_v2.py` (LINE 186-189)

---

## QUICK REFERENCE CARD

```
╔═══════════════════════════════════════════════════════╗
║              LIVE TRADING QUICK REFERENCE              ║
╠═══════════════════════════════════════════════════════╣
║ PRIORITY HIERARCHY:                                    ║
║  1. CASCADE (+1.95R) - ALWAYS CHECK FIRST             ║
║  2. Proximity (DISABLED)                              ║
║  3. Night ORB (+0.39R / +0.23R)                       ║
║  4. Single Liquidity (+1.44R)                         ║
║  5. Day ORB (+0.27R to +0.44R)                        ║
╠═══════════════════════════════════════════════════════╣
║ ENTRY METHOD (NON-NEGOTIABLE):                        ║
║  ✅ First 1-minute CLOSE outside ORB                  ║
║  ❌ ORB high/low (INVALID)                            ║
╠═══════════════════════════════════════════════════════╣
║ ORB CONFIGURATIONS:                                   ║
║  23:00: RR=1.0, HALF SL (+0.387R)                    ║
║  00:30: RR=1.0, HALF SL (+0.231R)                    ║
║  09:00: RR=1.0, FULL SL (+0.431R)                    ║
║  10:00: RR=3.0, FULL SL (+0.342R)                    ║
║  11:00: RR=1.0, FULL SL (+0.449R)                    ║
╠═══════════════════════════════════════════════════════╣
║ POSITION SIZING:                                      ║
║  Contracts = (Account × Risk%) / (Stop $ × $10)       ║
╠═══════════════════════════════════════════════════════╣
║ ACTIONS:                                              ║
║  STAND_DOWN → Wait                                    ║
║  PREPARE → Watch                                      ║
║  ENTER → Execute trade NOW                            ║
║  MANAGE → Monitor position                            ║
║  EXIT → Close position                                ║
╚═══════════════════════════════════════════════════════╝
```

---

**APP STATUS**: Updated 2026-01-13
**CANONICAL ENGINE**: Active
**GUARDRAILS**: Enforced
**DATA SOURCE**: v_orb_trades_half (validated)

---

## 23. ORB SIZE FILTERS (NEW)

### What Are ORB Size Filters?

**Filters that skip trades when the ORB is too large relative to recent volatility (ATR).**

### Why Filter Large ORBs?

**Pattern discovered:** Large ORB + Breakout = Exhaustion (chasing)
- Small ORB = Compression = Real breakout energy
- Large ORB = Expansion = Already moved, false breakout likely

### Which ORBs Have Filters?

| ORB | Filter | What It Means |
|-----|--------|---------------|
| 23:00 | Skip if ORB > 15.5% of ATR | Only trade compressed ORBs |
| 00:30 | Skip if ORB > 11.2% of ATR | Only trade compressed ORBs |
| 11:00 | Skip if ORB > 9.5% of ATR | Only trade compressed ORBs |
| 10:00 | Skip if ORB > 8.8% of ATR | Only trade compressed ORBs |
| 09:00 | No filter | Trade all ORBs |
| 18:00 | No filter (yet) | Trade all ORBs |

### Visual Example: 23:00 ORB Filter

**SCENARIO 1: SMALL ORB (PASS FILTER)**
```
ATR(20) = 10.0 points
ORB size = 1.2 points
ORB size / ATR = 1.2 / 10.0 = 0.12 (12%)

Filter threshold = 0.155 (15.5%)
Result: 12% < 15.5% → PASS → TRADE THIS ORB

Why: Compressed range, genuine breakout likely
```

**SCENARIO 2: LARGE ORB (REJECT)**
```
ATR(20) = 10.0 points
ORB size = 2.5 points
ORB size / ATR = 2.5 / 10.0 = 0.25 (25%)

Filter threshold = 0.155 (15.5%)
Result: 25% > 15.5% → REJECT → SKIP THIS ORB

Why: Already expanded, chasing, false breakout likely
```

### What You'll See in the App

**When filter is ACTIVE:**
- Status: "ORB TOO LARGE - FILTER REJECTED"
- Reason: "ORB size 2.5pts (25% of ATR) > threshold 15.5%"
- Action: "Stand down - wait for next ORB"

**When filter PASSES:**
- Normal ORB strategy display
- Breakout signals work as usual
- Filter operates silently in background

### Impact on Trading

**Trade Frequency:**
- 23:00: 36% of trades kept (64% filtered out)
- 00:30: 13% of trades kept (87% filtered out)
- 11:00: 11% of trades kept (89% filtered out)
- 10:00: 42% of trades kept (58% filtered out)

**Expected Monthly Trades:**
- **Before filters:** ~90 trades/month (all ORBs)
- **After filters:** ~25 trades/month (filtered ORBs)
- **Reduction:** 71.5% fewer trades

**Performance Improvement:**
- **Before filters:** +0.352R average per trade
- **After filters:** +0.510R average per trade
- **Improvement:** +0.158R per trade (+44.9%)

### Key Points

1. **Automatic:** Filters apply automatically in live trading
2. **No lookahead:** Filter uses only historical data (ATR) and ORB size known before entry
3. **Verified:** Manual calculation confirms all improvements
4. **Robust:** Works across different threshold values (not curve-fit)
5. **Trade-off:** Fewer trades but higher quality

### When to Override Filters (NEVER)

**Do NOT manually override filters.** They are based on 500+ trades of verified data.

If you think a filtered trade "looks good", remember:
- The filter exists because large ORBs statistically underperform
- Your discretion cannot outperform statistical edge
- Trust the system

### Monitoring Filters

**Track these metrics:**
1. Filter rejection rate (expect 58-89% depending on ORB)
2. Performance of trades that pass filter
3. Performance of trades that fail filter (if tracked separately)

**Monthly review:**
- Are rejection rates as expected?
- Is filtered performance maintaining edge?
- Any regime changes requiring threshold adjustment?

