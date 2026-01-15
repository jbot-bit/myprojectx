# Trading Hub App - Cloud Deployment Ready

**Micro Gold (MGC) & Micro Nasdaq (NQ) Trading Assistant with AI**

## Quick Start (Streamlit Cloud)

This app is ready for Streamlit Community Cloud deployment!

### Deploy Path
- **Main file:** `trading_app/app_trading_hub.py`
- **Repository:** https://github.com/jbot-bit/myprojectx

### Required Secrets (in Streamlit Cloud)

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
DATABENTO_API_KEY = "db-..."
DUCKDB_PATH = "trading_app.db"
SYMBOL = "MGC"
TZ_LOCAL = "Australia/Brisbane"
```

### Features

- **5 Tabs:**
  - 🔴 LIVE - Real-time strategy engine
  - 📊 LEVELS - Session levels & ORBs
  - 📋 TRADE PLAN - Position calculator
  - 📓 JOURNAL - Trading history
  - 🤖 AI CHAT - Claude assistant with memory

- **5 Strategies:**
  - CASCADE (+1.95R, S+ tier) - Multi-liquidity sweep pattern
  - SINGLE_LIQUIDITY (+1.44R, S tier) - Single level sweep
  - NIGHT_ORB - 23:00 & 00:30
  - DAY_ORB - 09:00, 10:00, 11:00, 18:00
  - Correlation filters for session dependencies

- **AI Assistant:**
  - Claude Sonnet 4.5
  - Persistent memory (DuckDB)
  - Live context awareness
  - Strategy explanations
  - Trade calculations

### Cloud Mode

The app detects cloud deployment and works in demo mode if no database exists:
- AI chat works immediately
- Add `DATABENTO_API_KEY` to backfill data from cloud
- Or use demo mode for testing

### Local Development

```bash
cd trading_app
pip install -r requirements.txt
streamlit run app_trading_hub.py
```

### Documentation

See `DEPLOY_TO_STREAMLIT_CLOUD.md` in root for full deployment guide.
