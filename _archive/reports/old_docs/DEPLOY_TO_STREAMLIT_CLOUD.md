# Deploy Trading App to Streamlit Community Cloud

**Access your trading app on mobile from anywhere!**

This guide shows you how to deploy `trading_app/app_trading_hub.py` to Streamlit Community Cloud.

---

## 🎯 What You'll Get

- **Stable URL:** `https://yourapp.streamlit.app`
- **Mobile Access:** Open on phone from anywhere
- **Always Online:** 24/7 availability
- **Free Hosting:** Streamlit Community Cloud is free
- **Auto-Updates:** Push to GitHub = auto-deploy

---

## 📋 Prerequisites

1. **GitHub Account** (https://github.com)
2. **Streamlit Cloud Account** (https://share.streamlit.io - sign in with GitHub)
3. **This Repository** (already at https://github.com/jbot-bit/myprojectx)

---

## 🚀 Step-by-Step Deployment

### Step 1: Push Latest Code to GitHub

```bash
# Make sure all changes are committed
git status

# If you have uncommitted changes, commit them
git add -A
git commit -m "Prepare for Streamlit Cloud deployment"

# Push to GitHub
git push origin main
```

**Verify:** Go to https://github.com/jbot-bit/myprojectx and confirm latest code is there.

---

### Step 2: Sign Up for Streamlit Community Cloud

1. Go to https://share.streamlit.io
2. Click "Sign in with GitHub"
3. Authorize Streamlit to access your GitHub repos
4. Complete signup

---

### Step 3: Deploy the App

1. **Click "New app"** in Streamlit Cloud dashboard

2. **Fill in deployment details:**
   - **Repository:** `jbot-bit/myprojectx`
   - **Branch:** `main`
   - **Main file path:** `trading_app/app_trading_hub.py`
   - **App URL:** Choose a custom subdomain (e.g., `mytrading-hub`)

3. **Click "Advanced settings"** (IMPORTANT!)

4. **Add Secrets** (click "Secrets" section):
   ```toml
   # Copy these from your local .env file
   ANTHROPIC_API_KEY = "sk-ant-api03-YOUR-KEY-HERE"
   DATABENTO_API_KEY = "db-YOUR-KEY-HERE"
   DATABENTO_DATASET = "GLBX.MDP3"
   DATABENTO_SCHEMA = "ohlcv-1m"
   DATABENTO_SYMBOLS = "MGC.FUT"
   DUCKDB_PATH = "trading_app.db"
   SYMBOL = "MGC"
   TZ_LOCAL = "Australia/Brisbane"
   PROJECTX_USERNAME = "joshdlees@gmail.com"
   PROJECTX_API_KEY = "YOUR-PROJECTX-KEY"
   PROJECTX_BASE_URL = "https://api.topstepx.com"
   PROJECTX_LIVE = "false"
   ```

   **⚠️ CRITICAL:** Never commit these to GitHub! Only add them in Streamlit Cloud secrets.

5. **Set Python version** (if needed):
   - Python version: `3.10` or `3.11` (recommended)

6. **Click "Deploy"**

---

### Step 4: Wait for Deployment

- **Initial deployment:** 2-5 minutes
- Streamlit will install all dependencies from `requirements.txt`
- Watch the logs in the deployment console
- Look for: "You can now view your Streamlit app in your browser"

---

### Step 5: Test Your App

1. **Open the URL:** `https://yourapp.streamlit.app`
2. **Test features:**
   - ✅ App loads without errors
   - ✅ AI Chat tab works (test with a question)
   - ✅ No database yet (expected - see Step 6)

---

### Step 6: Initialize Data (Optional)

Your app works immediately for AI chat, but to get live data:

**Option A: Demo Mode (No Setup Required)**
- AI chat works immediately
- Perfect for testing on mobile
- Ask strategy questions, get calculations
- No live data or backtesting

**Option B: Backfill Data in Cloud**
1. Ensure `DATABENTO_API_KEY` is in secrets
2. Open app → Click "Initialize/Refresh Data" in sidebar
3. App will download last 7 days of data from Databento
4. Data stored in cloud (persists until app restarts)

**Option C: Use Local Data**
- Not recommended for cloud deployment
- gold.db would need to be committed (large file, contains data)

---

## 📱 Access on Mobile

1. **Open your browser** on phone (Safari, Chrome, etc.)
2. **Navigate to:** `https://yourapp.streamlit.app`
3. **Add to Home Screen** (optional but recommended):
   - **iOS:** Share button → "Add to Home Screen"
   - **Android:** Menu → "Add to Home Screen"
4. **Use like a native app!**

---

## 🔄 Updating Your App

**Every time you push to GitHub, app auto-updates:**

```bash
# Make changes locally
git add -A
git commit -m "Update AI assistant prompt"
git push origin main

# Streamlit Cloud detects push and redeploys automatically
# Wait 1-2 minutes, refresh browser
```

---

## ⚙️ App Settings in Streamlit Cloud

**Manage your deployed app:**

1. Go to https://share.streamlit.io
2. Find your app in the dashboard
3. Click **⋮** (three dots) → "Settings"

**Available options:**
- **Secrets:** Add/update API keys (never in code!)
- **Reboot:** Restart app if it's stuck
- **Delete:** Remove deployment
- **Logs:** View error logs
- **Analytics:** See usage stats

---

## 🐛 Troubleshooting

### "App is not loading"
- Check deployment logs in Streamlit Cloud
- Verify all dependencies in `requirements.txt`
- Ensure `trading_app/app_trading_hub.py` path is correct

### "ModuleNotFoundError"
- Missing dependency in `requirements.txt`
- Add it and push to GitHub
- App will auto-redeploy

### "AI Assistant not available"
- Check `ANTHROPIC_API_KEY` in Streamlit Cloud secrets
- Verify key is correct (starts with `sk-ant-`)
- Reboot app after adding secrets

### "No data in LIVE tab"
- Expected on first deploy (no database)
- Click "Initialize/Refresh Data" to backfill
- Or use Demo Mode (AI chat only)

### "App keeps crashing"
- Check logs in Streamlit Cloud dashboard
- Look for Python errors
- Verify all API keys are valid

---

## 🔒 Security Notes

**✅ DO:**
- Store API keys in Streamlit Cloud secrets only
- Use `.gitignore` to exclude `.env` and `*.db` files
- Keep repository private if it contains sensitive logic

**❌ DON'T:**
- Commit `.env` file to GitHub
- Commit `gold.db` or `trading_app.db` to GitHub
- Share your deployed URL publicly (if using real API keys)

---

## 💰 Cost

**Streamlit Community Cloud:**
- **Free forever** for public repos
- **Free** for private repos (with limits)
- **Unlimited viewers**
- **1 GB RAM per app**
- **1 GB storage per app**

**API Costs:**
- **Claude Sonnet 4.5:** ~$3-6/month (typical usage)
- **Databento:** Depends on data downloads
- **ProjectX:** Depends on your plan

---

## 📊 Performance

**Expected Performance:**
- **Cold start:** 5-10 seconds (first load after idle)
- **Warm start:** <1 second (subsequent loads)
- **AI responses:** 2-3 seconds
- **Data refresh:** 10-30 seconds (depending on data volume)

**Streamlit Cloud automatically:**
- Caches data to speed up page loads
- Sleeps after 7 days of inactivity (wakes on first visit)
- Restarts daily (fresh state, no memory leaks)

---

## 🎉 You're Done!

Your trading app is now deployed and accessible from anywhere!

**Next Steps:**
1. Bookmark your app URL
2. Add to phone home screen
3. Test AI chat features
4. Backfill data (optional)
5. Share URL with yourself via email/text

**Your App URL:** `https://[your-subdomain].streamlit.app`

---

## 📞 Support

**Streamlit Cloud Issues:**
- Docs: https://docs.streamlit.io/deploy/streamlit-community-cloud
- Forum: https://discuss.streamlit.io
- Status: https://streamlit.statuspage.io

**App Issues:**
- Check GitHub repository issues
- Review deployment logs in Streamlit Cloud

---

**Deployment Date:** January 15, 2026
**Status:** Ready to deploy
**Estimated Setup Time:** 15-20 minutes
