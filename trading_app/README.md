# Live Trading Decision Support App

Real-time trading decision engine for systematic strategy execution. Continuously evaluates all validated strategies and tells you EXACTLY what to do at any moment.

## Features

- **Real-time Data Integration**: ProjectX API for live 1-minute bars
- **Strategy Hierarchy**: Automatic prioritization of validated edges
- **Decision Panel**: Clear, actionable instructions (no analysis paralysis)
- **Live Charting**: Session levels, VWAP, and price action visualization
- **Position Calculator**: Automatic risk-based position sizing
- **Trade Journal**: Automatic logging of all strategy evaluations

## Validated Strategies (Priority Order)

### Tier 1: Multi-Liquidity Cascades
- **Edge**: +1.95R avg, 9.3% frequency
- **Pattern**: Double sweep (Asia→London→NY) + acceptance failure
- **Risk**: 0.10-0.25% per trade
- **Max Hold**: 90 minutes

### Tier 2: Night ORBs
- **00:30 ORB**: +1.54R avg, 56% frequency (BEST ORB)
- **23:00 ORB**: +1.08R avg, 63% frequency
- **Risk**: 0.25-0.50% per trade

### Tier 3: Single Liquidity Reaction
- **Edge**: +1.44R avg, 16% frequency
- **Pattern**: London level swept at 23:00, fails to hold
- **Risk**: 0.25% per trade

### Tier 4: Day ORBs (Fallback)
- **09:00, 10:00, 11:00 ORBs**
- **Edge**: +0.27-0.39R avg, 64-66% frequency
- **Risk**: 0.10-0.25% per trade

## Installation

### Prerequisites

```bash
# Python 3.10+
python --version

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the project root (NOT in trading_app folder):

```
# ProjectX API (for live data)
PROJECTX_USERNAME=your_email@example.com
PROJECTX_API_KEY=your_api_key_here
PROJECTX_BASE_URL=https://api.topstepx.com
PROJECTX_LIVE=false

# Database
DUCKDB_PATH=gold.db
SYMBOL=MGC
TZ_LOCAL=Australia/Brisbane
```

**IMPORTANT**: The app reads from `../.env` (parent directory), not from the trading_app folder.

## Running the App

### Option 1: From Project Root

```bash
cd C:\Users\sydne\OneDrive\myprojectx
streamlit run trading_app/app_trading_hub.py
```

### Option 2: From trading_app folder

```bash
cd C:\Users\sydne\OneDrive\myprojectx\trading_app
streamlit run app_trading_hub.py
```

The app will open in your browser at `http://localhost:8501`

## Using the App

### Initial Setup

1. **Select Instrument**: Use sidebar to choose MNQ (Micro NQ) or MGC (Micro Gold)
2. **Set Account Size**: Enter your account value for position sizing
3. **Initialize Data**: Click "Initialize/Refresh Data" button in sidebar

### Live Tab (Main Interface)

The **LIVE** tab shows:

- **Status**: Current strategy state (STAND_DOWN, PREPARE, ENTER, MANAGE, EXIT)
- **Strategy**: Which strategy is active (CASCADE, NIGHT_ORB, SINGLE_LIQUIDITY, DAY_ORB)
- **Why**: Up to 3 bullet points explaining current conditions
- **Next Action**: ONE explicit instruction (what to do NOW)
- **Live Chart**: 1-minute candlesticks with session levels and VWAP
- **Trade Details**: Entry/stop/target prices when signal is active

### Levels Tab

Shows:
- Asia session (09:00-17:00 local) high/low/range
- London session (18:00-23:00 local) high/low/range
- Gap analysis for cascade detection

### Trade Plan Tab

Active when an ENTER signal is present. Shows:
- Risk points and dollar risk
- Calculated position size (contracts)
- Complete trade summary with management rules

### Journal Tab

Automatic log of all strategy evaluations including:
- Timestamp
- Strategy name
- State and action
- Reasons for decision
- Entry/stop/target prices
- Summary statistics and strategy breakdown

## Decision Logic

The app evaluates strategies in strict priority order:

1. **Cascades** (A+ tier): If preparing/active, all lower tiers STAND_DOWN
2. **Night ORBs** (B tier): Only active if cascades invalid
3. **Single Liquidity** (B-backup): Only active if cascades and ORBs invalid
4. **Day ORBs** (C tier): Fallback when nothing better available

**Only ONE strategy can be active at a time**. The highest priority actionable strategy wins.

## Auto-Refresh

- Enable "Auto-refresh" in sidebar (default: ON)
- Refreshes every 5 seconds (configurable in config.py)
- Data fetched from ProjectX API or database fallback

## Troubleshooting

### "ProjectX initialization failed"

- Check .env file exists in parent directory (not in trading_app folder)
- Verify PROJECTX_USERNAME and PROJECTX_API_KEY are correct
- App will fall back to database mode if API unavailable

### "No bars found"

- Click "Initialize/Refresh Data" to backfill from gold.db
- Ensure gold.db exists in parent directory with recent data
- Check that symbol (MNQ/MGC) has data in database

### "Missing session data"

- Some strategies require complete session data (Asia, London, NY)
- Wait for sessions to complete (9am, 5pm, 11pm local time)
- Check that bars are being ingested for current day

### Import Errors

```bash
# Install missing dependencies
pip install streamlit pandas plotly duckdb python-dotenv httpx
```

## Configuration

Edit `config.py` to customize:

- Session times (if not using Australia/Brisbane timezone)
- Risk limits per strategy
- Chart settings (height, lookback bars)
- Refresh interval
- ORB parameters (duration, configs)
- Cascade parameters (gap size, failure bars)

## Database

The app uses two databases:

1. **gold.db** (parent directory): Historical data for backtesting and backfill
2. **trading_app.db** (app folder): Live bars and journal entries

Tables created automatically:
- `live_bars`: Rolling window of 1-minute bars
- `live_journal`: Strategy evaluation log

## Performance Notes

- Data window: 48 hours rolling (configurable)
- Chart lookback: 200 bars default
- ProjectX API timeout: 60 seconds
- Journal limit: 50 most recent entries

## Safety Features

- No automatic order execution (decision support only)
- Hierarchy prevents conflicting signals
- Risk limits enforced per strategy tier
- Acceptance failure required for liquidity strategies
- Max hold time limits (90 minutes for cascades)

## Support

For issues or questions:
1. Check logs in `trading_app.log`
2. Review journal tab for strategy evaluation history
3. Verify .env configuration
4. Ensure gold.db has recent data

## License

Proprietary - For authorized use only
