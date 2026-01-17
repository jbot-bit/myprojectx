# Trading Hub Mobile - User Guide

**Mobile-First Trading Interface** • Card-Based Navigation • Dark Mode • Touch Optimized

---

## 🎯 Quick Start

### Desktop Testing
```bash
START_MOBILE_APP.bat
```
- Opens on `http://localhost:8501`
- Use Chrome DevTools (F12) → Device Mode to test mobile view
- Select iPhone/Android device from dropdown

### Mobile Access
1. Find your PC IP address: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. On your phone, open browser and go to: `http://YOUR_PC_IP:8501`
3. Make sure phone and PC are on same Wi-Fi network

---

## 📱 Interface Overview

### Card-Based Navigation
The app has **5 swipeable cards** (like Tinder):

```
[◄] ● ○ ○ ○ ○ [►]
     Dashboard (1/5)
```

**Swipe left/right** or tap arrows to navigate:
1. 📊 **Dashboard** - Quick glance (price, ATR, countdown, status)
2. 📈 **Chart** - Collapsible chart with ORB levels
3. 🎯 **Trade** - Entry calculator
4. 💼 **Positions** - Active trades monitoring
5. 🤖 **AI Chat** - Assistant + calculations

---

## 🎴 Card 1: Dashboard

**PURPOSE**: Most important info at a glance

### What You See:
```
┌────────────────────────┐
│  🔴 LIVE Dashboard     │
├────────────────────────┤
│                        │
│     $2,650.42          │  ← Large price
│     MGC Price          │
│     19:05:23           │
│                        │
├────────────────────────┤
│  ATR: 42.15  │  ✅ OK  │  ← 2-column
├────────────────────────┤
│                        │
│   ⏰ NEXT: 2300 ORB    │
│   02:54:37             │  ← Countdown
│   Until Window Opens   │
│                        │
├────────────────────────┤
│ STATUS: 🎯 PREPARE     │
│ • 2300 ORB approaching │
│ • Filter PASSED        │
│ • Get ready            │
│                        │
│ NEXT ACTION:           │
│ Watch 2300-2305 range  │
└────────────────────────┘
```

### Features:
- **Live Price**: 48px font, updates every 10s
- **ATR Display**: Daily ATR (20-period)
- **Filter Status**: ✅ Pass or ⏭️ Skip
- **Next ORB Countdown**: Live timer (HH:MM:SS)
- **Status Card**: Current action + 3 reasons + next instruction

### Use Case:
Open app → Instant understanding of market state without scrolling

---

## 🎴 Card 2: Chart

**PURPOSE**: Visual price action + ORB levels

### Default State (Collapsed):
```
┌────────────────────────┐
│ 📈 Chart & Levels      │
│ [▼ Show Chart]         │  ← Tap to expand
└────────────────────────┘
```

### Expanded State:
```
┌────────────────────────┐
│ 📈 Chart & Levels      │
│ [▲ Hide Chart]         │
├────────────────────────┤
│                        │
│   [Live Chart 350px]   │  ← Plotly chart
│   - Green: ORB high    │
│   - Red: ORB low       │
│   - Pinch to zoom      │
│                        │
├────────────────────────┤
│ ORB High: $2,655.20    │
│ ORB Low:  $2,652.40    │
│ Size:     2.80pts ✅   │
└────────────────────────┘
```

### Features:
- **Collapsible**: Hidden by default to save space
- **Mobile-Optimized**: 350px height, thinner candlesticks
- **Touch Gestures**: Pinch-zoom, pan
- **ORB Overlay**: Green high, red low lines
- **Summary Below**: High/low/size metrics

### Use Case:
Quick price check without cluttering main dashboard

---

## 🎴 Card 3: Trade Entry Calculator

**PURPOSE**: Calculate stop/target for ORB breakout

### Interface:
```
┌────────────────────────┐
│ 🎯 Trade Calculator    │
├────────────────────────┤
│ Direction:             │
│  [🚀 LONG] [🔻 SHORT]  │  ← Toggle
├────────────────────────┤
│ ORB Levels:            │
│ ORB High: [2655.20]    │  ← Input
│ ORB Low:  [2652.40]    │
│                        │
│ Risk/Reward: [4.0]     │
│ SL Mode: [FULL ▼]      │
├────────────────────────┤
│ [📊 Calculate Trade]   │  ← Button
├────────────────────────┤
│ 📍 Results:            │
│ Entry:  $2,655.20      │
│ Stop:   $2,652.40      │
│ Target: $2,666.60 (4R) │
│ Risk:   $250 (0.25%)   │
├────────────────────────┤
│ [📋 Copy Levels]       │
└────────────────────────┘
```

### How to Use:
1. **Select Direction**: Tap LONG or SHORT
2. **Enter ORB Levels**: Type high/low prices
3. **Set RR**: Adjust risk/reward ratio (1-10R)
4. **Choose SL Mode**: FULL (opposite side) or HALF (midpoint)
5. **Calculate**: Tap button
6. **Copy**: Tap to copy levels to clipboard

### Features:
- **Large Input Fields**: 48px height (easy to tap)
- **Real-Time Calculation**: Updates as you type
- **Position Sizing**: Shows risk in dollars
- **Copy Function**: Quick copy to broker

### Use Case:
ORB just formed → Input levels → Get instant stop/target

---

## 🎴 Card 4: Positions

**PURPOSE**: Monitor active trades

### With Position:
```
┌────────────────────────┐
│ 📊 Active Positions(1) │
├────────────────────────┤
│ 🚀 LONG MGC            │
│ Entry: $2,655.20       │
│ Current: $2,658.40     │
│ (+3.20pts)             │
│                        │
│ +$320 (+1.28R) 💚      │  ← P&L
│                        │
│ Stop: $2,652.40        │
│ Target: $2,666.60      │
│ ▓▓▓▓░░░░ 28%          │  ← Progress
│                        │
│ [🚪 Close Position]    │
└────────────────────────┘
```

### Empty State:
```
┌────────────────────────┐
│ 📊 Active Positions(0) │
│                        │
│        📭              │
│   No Positions Open    │
│   Wait for next setup  │
│                        │
└────────────────────────┘
```

### Features:
- **Live P&L**: Updates with current price
- **Progress Bar**: Visual target progress
- **Color-Coded**: Green (profit), Red (loss)
- **R-Multiple**: Shows gains in R units
- **Close Button**: Exit position (simulated)

### Use Case:
In trade → Swipe to Positions → Check P&L → Monitor progress

---

## 🎴 Card 5: AI Chat

**PURPOSE**: Ask strategy questions, get trade calculations

### Interface:
```
┌────────────────────────┐
│ 🤖 AI Assistant        │
│ ✅ Claude Sonnet ready!│
├────────────────────────┤
│ 💬 Conversation:       │
│                        │
│ You: ORB is 2700-2706, │
│      LONG, calc stop?  │
│                        │
│ AI: Entry at 2706,     │
│     Stop 2700, Target  │
│     2730 (4R). Risk    │
│     $250 at 0.25%.     │
│                        │
├────────────────────────┤
│ Ask a Question:        │
│ [Type here...]         │
│ [📤 Send] [🗑️ Clear]   │
├────────────────────────┤
│ 💡 Quick Actions:      │
│ [📊 Calculate] [❓ Why]│
└────────────────────────┘
```

### How to Use:
1. **Type Question**: Tap input field
2. **Send**: Tap Send button
3. **Quick Actions**: Tap preset buttons for common questions

### Example Questions:
- "ORB is 2700-2706, direction LONG, calculate my stop and target"
- "Why is 00:30 ORB good?"
- "What's my risk in dollars for $10k account?"
- "Should I trade 09:00 or 10:00 ORB?"

### Features:
- **Persistent Memory**: Saves conversation to database
- **Last 10 Messages**: Shows recent history
- **Quick Actions**: Preset buttons for common tasks
- **Trade Context**: AI knows current ORBs and market state

### Use Case:
Need quick calculation → Ask AI → Get instant answer

---

## ⚙️ Settings

**Access**: Scroll to bottom → Tap "⚙️ Settings"

### Available Settings:
```
┌────────────────────────┐
│ ⚙️ Settings            │
├────────────────────────┤
│ Account Size: $100,000 │
│ Auto-refresh: ☑ On     │
│ Interval: 10s          │
│                        │
│ [🔄 Refresh Data Now]  │
│ [🔄 Reset App]         │
└────────────────────────┘
```

- **Account Size**: Set your account for position sizing
- **Auto-Refresh**: Toggle live updates (10s market hours, 30s off-hours)
- **Manual Refresh**: Force data reload
- **Reset App**: Clear cache and restart

---

## 📐 Design Philosophy

### Mobile-First Principles:
1. **Quick Glance Priority**: Most important info (price, ATR, countdown) on Card 1
2. **Collapsible Chart**: Hidden by default (use when needed)
3. **Large Touch Targets**: All buttons 48px+ (iOS/Android standard)
4. **Dark Mode**: OLED-friendly (#0a0b0d black background)
5. **Minimal Scrolling**: Each card fits in viewport
6. **Swipe Navigation**: Natural gesture-based movement

### Color System:
- **Background**: #0a0b0d (OLED black)
- **Cards**: #1a1d26 (dark gray)
- **Green**: #10b981 (bullish/profit)
- **Red**: #ef4444 (bearish/loss)
- **Indigo**: #6366f1 (neutral/accent)
- **Text**: #f9fafb (primary), #9ca3af (secondary)

---

## 🚀 Performance

### Optimization Features:
- **Lazy Loading**: Charts only render when card visible
- **Compact Chart**: 350px vs 600px desktop
- **Debounced Inputs**: Smooth typing in calculator
- **Cached Data**: Reuses data between cards
- **Auto-Refresh**: 10s (market hours) or 30s (off-hours)

### Target Metrics:
- First Contentful Paint: < 1.5s
- Time to Interactive: < 3s
- Lighthouse Mobile Score: > 90

---

## 📱 PWA Installation (Optional)

### iOS (Safari):
1. Open app in Safari
2. Tap Share button
3. Tap "Add to Home Screen"
4. Name: "Trading Hub"
5. Tap "Add"

### Android (Chrome):
1. Open app in Chrome
2. Tap menu (3 dots)
3. Tap "Add to Home Screen"
4. Confirm

### Benefits:
- ✅ Full-screen (no browser chrome)
- ✅ App icon on home screen
- ✅ Faster loading (cached assets)
- ✅ Offline fallback (basic functionality)

---

## 🔧 Troubleshooting

### App Won't Load:
1. Check Python is installed: `python --version`
2. Install dependencies: `pip install -r trading_app/requirements.txt`
3. Check database exists: `gold.db` in project root
4. Run: `START_MOBILE_APP.bat`

### Can't Access from Phone:
1. Check both devices on same Wi-Fi
2. Check PC firewall allows port 8501
3. Use correct IP: `ipconfig` → IPv4 Address
4. Try: `http://YOUR_IP:8501`

### Chart Not Showing:
1. Expand chart (tap "Show Chart")
2. Check data loaded (go to Settings → Refresh Data)
3. Check browser console for errors (F12)

### AI Not Working:
1. Check `.env` file has `ANTHROPIC_API_KEY=sk-ant-...`
2. Verify API key is valid at https://console.anthropic.com/
3. Check error message in app

---

## 🎓 Tips & Best Practices

### Efficient Workflow:
1. **Morning**: Open Dashboard → Check ATR + next ORB
2. **Pre-ORB**: Swipe to Chart → Expand → Watch formation
3. **ORB Forms**: Swipe to Trade → Calculate levels
4. **Enter Trade**: Swipe to Positions → Monitor P&L
5. **Questions**: Swipe to AI → Ask for clarification

### Screen Real Estate:
- **Dashboard**: Keep visible most of time
- **Chart**: Expand when price action matters
- **Trade Calc**: Use when ORB forms
- **Positions**: Check occasionally during trade
- **AI Chat**: Use for learning/questions

### Battery Saving:
- Disable auto-refresh when not actively trading
- Reduce refresh interval to 30s
- Close app when not in use

---

## 📊 Comparison: Desktop vs Mobile

| Feature | Desktop App | Mobile App |
|---------|-------------|------------|
| Layout | Wide, multi-column | Card-based, swipeable |
| Sidebar | Yes (settings/filters) | No (bottom settings) |
| Chart | Always visible (600px) | Collapsible (350px) |
| Navigation | Scroll + tabs | Swipe + dots |
| Touch Targets | 32px | 48px |
| Font Sizes | 14-28px | 16-48px |
| Use Case | Deep analysis, backtesting | Quick glance, trade entry |

---

## 🛠️ Technical Details

### Files Added:
```
trading_app/
├── app_mobile.py              # Mobile app entry point
├── mobile_ui.py               # Card components + CSS
├── app_manifest.json          # PWA manifest
└── service-worker.js          # Offline support

trading_app/live_chart_builder.py  # Added build_mobile_chart()
trading_app/config.py               # Added MOBILE_* settings

START_MOBILE_APP.bat           # Launcher
```

### Dependencies:
- Same as desktop app (no new packages)
- Uses existing: Streamlit, Plotly, Anthropic SDK

### Browser Support:
- ✅ Chrome (Android/Desktop)
- ✅ Safari (iOS)
- ✅ Firefox (Android/Desktop)
- ⚠️ Edge (Desktop only - limited mobile)

---

## 🔮 Future Enhancements

### Planned Features:
- [ ] Gesture controls (swipe down to refresh)
- [ ] Haptic feedback on important events
- [ ] Notification system (ORB alerts)
- [ ] Offline mode (cached data)
- [ ] Voice input for AI chat
- [ ] Widget support (iOS 14+)
- [ ] Apple Watch companion

---

## 📞 Support

### Issues:
- Report bugs: GitHub Issues
- Feature requests: GitHub Discussions

### Resources:
- Desktop app: `START_TRADING_APP.bat`
- Mobile app: `START_MOBILE_APP.bat`
- Documentation: `CLAUDE.md`
- Project structure: `PROJECT_STRUCTURE.md`

---

**Trading Hub Mobile v2.0** • Built with Streamlit • Powered by Claude AI
