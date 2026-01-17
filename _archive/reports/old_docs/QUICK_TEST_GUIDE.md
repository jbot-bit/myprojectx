# Quick Test Guide - Enhanced Trading App

**Purpose**: Fast validation of all new professional-grade features
**Time Required**: 10-15 minutes

---

## 🚀 Launch App

```bash
cd C:\Users\sydne\OneDrive\myprojectx\trading_app
streamlit run app_trading_hub.py
```

---

## ✅ 5-MINUTE SMOKE TEST

### 1. App Loads (30 seconds)
- [ ] App opens without errors
- [ ] 6 tabs visible: LIVE, SCANNER, LEVELS, TRADE PLAN, JOURNAL, AI CHAT
- [ ] Sidebar loads with settings
- [ ] No error messages in console

### 2. Alert System (1 minute)
**Location**: Sidebar → "🔔 Alert Settings"

- [ ] See "🔊 Audio Alerts" checkbox
- [ ] See "🔔 Desktop Notifications" checkbox
- [ ] Click "Enable Notifications" button
- [ ] Browser asks for notification permission → Allow
- [ ] See "Alert Types" expander

### 3. Setup Scanner (2 minutes)
**Location**: 🔍 SCANNER tab

- [ ] Click SCANNER tab
- [ ] See 3 price input sections (MGC, NQ, MPL)
- [ ] See filter controls (Elite Only, Active/Ready Only, Hide SKIP)
- [ ] See summary metrics (Triggered, Active, Ready, Waiting, Elite)
- [ ] See table with setups (should show all 17 if Hide SKIP is off)
- [ ] Table columns: Instrument, ORB, Status, Time, Tier, Win%, Exp, Filter, Price
- [ ] Click "Elite Only" → table filters to S+/S tier only
- [ ] Select setup from dropdown → see detailed info

### 4. Enhanced Charting (1.5 minutes)
**Location**: 🔴 LIVE tab (after initializing data)

**First, load data**:
- [ ] Click "Initialize/Refresh Data" in sidebar
- [ ] Wait for data load

**Then test chart**:
- [ ] Scroll down to "📈 Live Chart" section
- [ ] See 4 controls: Timeframe, EMA, VWAP, ORB Overlays
- [ ] Change timeframe from "1m" to "5m" → chart updates
- [ ] Check "EMA (9, 20)" → blue/purple lines appear
- [ ] Check "VWAP" → orange dashed line appears
- [ ] See session levels (Asia High/Low, London High/Low)

### 5. Integration Check (30 seconds)
- [ ] Click through all 6 tabs → no errors
- [ ] Auto-refresh checkbox in sidebar works
- [ ] No Python errors in terminal
- [ ] No browser console errors (F12)

**If all checked**: ✅ **SMOKE TEST PASSED!**

---

## 🔬 DETAILED TESTING (Optional)

### Alert System - Deep Test

**Audio Alerts**:
1. Uncheck "🔊 Audio Alerts"
2. Check "🔊 Audio Alerts"
3. Note: Audio will play when ORB opens or setup triggers

**Desktop Notifications**:
1. Ensure notifications enabled
2. Note: Will appear when ORB opens (test during actual ORB window)

**Price Alerts** (in expander "💰 Price Alerts"):
1. Enter alert name: "Test High Alert"
2. Enter price: 2700.0
3. Select condition: "above"
4. Click "Add Alert"
5. See alert in "Active Alerts" list
6. Click "×" to remove

### Setup Scanner - Deep Test

**Filter Testing**:
1. Default view: ~17 setups (6 MGC + 5 NQ + 6 MPL)
2. Check "Elite Only (S+/S)": ~4-6 setups
3. Check "Active/Ready Only": Only active/ready/triggered setups
4. Check "Hide SKIP": Removes NQ 2300 (marked SKIP)
5. Instrument dropdown: Select "MGC" → only 6 MGC setups

**Status Colors**:
- **Green** (Triggered): Price broke ORB
- **Yellow** (Active): ORB window open right now
- **Blue** (Ready): ORB formed, filter passed, waiting for break
- **Gray** (Waiting): ORB hasn't opened yet
- **Red** (Expired): ORB window passed, no break or failed filter

**Details View**:
1. Select any setup from dropdown
2. Left panel: Status, Tier, Time, Performance stats
3. Right panel: Current market data, ORB levels, filter status, notes

### Enhanced Charting - Deep Test

**Timeframe Switching**:
1. Start at 1m → see 200 bars
2. Switch to 5m → see ~40 bars (5x less)
3. Switch to 15m → see ~13 bars (15x less)
4. Switch to 1h → see ~3 bars (60x less)
5. Switch back to 1m

**Indicator Testing**:
1. **EMA**: Check box → two lines (blue=EMA9, purple=EMA20)
2. **VWAP**: Check box → orange dashed line
3. **ORB Overlays**: Check box → rectangles appear (if ORB data available)
4. Uncheck all → clean candlestick chart

**Session Levels**:
- Asia High/Low: Green dashed lines
- London High/Low: Blue dotted lines
- Should have labels on right side

**Interactivity**:
1. Hover over candle → see OHLC tooltip
2. Zoom in: Click and drag on chart
3. Zoom out: Double-click chart
4. Pan: Click and drag while zoomed
5. Reset: Double-click

---

## 🐛 TROUBLESHOOTING

### Import Errors
**Error**: `ModuleNotFoundError: No module named 'alert_system'`

**Fix**:
```bash
cd C:\Users\sydne\OneDrive\myprojectx
# Verify files exist:
dir trading_app\alert_system.py
dir trading_app\setup_scanner.py
dir trading_app\enhanced_charting.py
```

### Database Errors
**Error**: `Database file not found: gold.db`

**Fix**:
```bash
# Ensure gold.db is in trading_app parent directory:
cd C:\Users\sydne\OneDrive\myprojectx
dir gold.db
```

### Chart Empty
**Issue**: Chart shows "No bar data available"

**Fix**:
1. Click "Initialize/Refresh Data" in sidebar
2. Wait for data to load (5-10 seconds)
3. If still empty, check gold.db has data:
   ```bash
   python check_db.py
   ```

### Scanner Shows No Setups
**Issue**: Scanner table is empty

**Fix**:
1. Check gold.db has validated_setups table
2. Run: `python populate_validated_setups.py`
3. Refresh app

---

## 📊 EXPECTED RESULTS

### Setup Scanner Table (Example)

| Instrument | ORB  | Status  | Time    | Tier | Win%  | Exp     | Filter |
|------------|------|---------|---------|------|-------|---------|--------|
| MGC        | 2300 | READY   | +15m    | S+   | 56.1% | +0.40R  | PASS   |
| MGC        | 1000 | WAITING | -2h30m  | S+   | 15.3% | +0.38R  | None   |
| MGC        | 0030 | EXPIRED | +8h     | S    | 31.3% | +0.25R  | PASS   |
| NQ         | 1100 | ACTIVE  | -2m     | A    | 45.2% | +0.26R  | PASS   |
| MPL        | 1100 | READY   | +30m    | A    | 67.1% | +0.30R  | None   |

### Summary Metrics (Example)

```
🎯 Triggered: 0
🔥 Active: 1
✅ Ready: 3
⏳ Waiting: 10
⭐ Elite: 4
```

---

## 🎯 SUCCESS CRITERIA

**Minimum Requirements** (Must Pass):
- ✅ App launches without errors
- ✅ All 6 tabs load
- ✅ Alert settings visible in sidebar
- ✅ Scanner shows 17 setups (when Hide SKIP unchecked)
- ✅ Chart displays with timeframe selector
- ✅ Indicators can be toggled

**Full Success** (Should Pass):
- ✅ Desktop notifications work
- ✅ Scanner filters work correctly
- ✅ All timeframes display properly
- ✅ EMA/VWAP indicators visible
- ✅ Session levels show on chart
- ✅ No console errors
- ✅ Auto-refresh works

**Excellent** (Nice to Have):
- ✅ ORB overlays display (requires ORB data)
- ✅ Price alerts trigger correctly
- ✅ Audio alerts play
- ✅ Responsive on different screen sizes

---

## 📝 TEST RESULTS

**Date Tested**: _____________

**Tester**: _____________

**Browser**: _____________

**Results**:
- [ ] Smoke Test Passed
- [ ] Deep Test Passed
- [ ] All Features Working
- [ ] Issues Found: ____________________________

**Notes**:
```
[Your notes here]
```

---

## ✅ SIGN-OFF

**Status**: [ ] PASSED / [ ] FAILED / [ ] NEEDS FIXES

**Ready for Production**: [ ] YES / [ ] NO

**Signature**: _______________ **Date**: _______________

---

**Need Help?**
- Check `ENHANCEMENTS_COMPLETE.md` for full feature documentation
- Check `ENHANCED_APP_INTEGRATION.md` for integration details
- Check `TRADING_APP_ENHANCEMENT_PLAN.md` for original plan
