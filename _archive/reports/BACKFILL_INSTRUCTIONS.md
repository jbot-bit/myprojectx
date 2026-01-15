# Overnight Backfill Instructions

**Goal:** Backfill 2020-12-20 to 2023-12-31 data overnight

**Estimated time:** 4-8 hours (depending on Databento API speed)

---

## 📋 Pre-Flight Checklist

### 1. Check Databento API Key

```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', os.getenv('DATABENTO_API_KEY')[:20] + '...' if os.getenv('DATABENTO_API_KEY') else 'NOT FOUND')"
```

**Expected:** Should show first 20 chars of your API key

### 2. Test Databento Connection

```bash
python test_databento_mgc.py
```

**Expected:** Should fetch sample data without errors

### 3. Check Available Disk Space

```bash
# Windows
dir gold.db
```

**Current DB size:** ~few hundred MB
**After backfill:** ~1-2 GB (estimate)
**Ensure:** At least 5 GB free space

### 4. Backup Current Database (Optional but Recommended)

```bash
# Windows
copy gold.db gold_backup_2024_2026.db
```

This preserves your current 2024-2026 data in case anything goes wrong.

---

## 🚀 Run the Backfill

### Option A: Simple (Let it run unattended)

```bash
python backfill_overnight_2020_2023.py
```

This will:
- Backfill in 90-day chunks
- Save progress after each chunk
- Log everything to `backfill_overnight_progress.log`
- Can be resumed if interrupted

### Option B: Manual Chunks (More control)

If you want to run it in stages:

```bash
# Year 2020 (partial)
python backfill_databento_continuous.py 2020-12-20 2020-12-31

# Year 2021
python backfill_databento_continuous.py 2021-01-01 2021-12-31

# Year 2022
python backfill_databento_continuous.py 2022-01-01 2022-12-31

# Year 2023
python backfill_databento_continuous.py 2023-01-01 2023-12-31
```

---

## 📊 Monitoring Progress

### Check the log file:

```bash
# Windows - see last 20 lines
powershell "Get-Content backfill_overnight_progress.log -Tail 20"

# Or open in notepad
notepad backfill_overnight_progress.log
```

### Check database size:

```bash
dir gold.db
```

Should grow over time as data is added.

### Check row counts:

```bash
python -c "import duckdb; con = duckdb.connect('gold.db'); print('bars_1m:', con.execute('SELECT COUNT(*) FROM bars_1m').fetchone()[0]); print('daily_features_v2:', con.execute('SELECT COUNT(*) FROM daily_features_v2').fetchone()[0])"
```

---

## ⚠️ If Something Goes Wrong

### If backfill crashes:

1. **Check the log:** `backfill_overnight_progress.log`
2. **Check the checkpoint:** `backfill_overnight_checkpoint.txt` (shows last completed date)
3. **Resume:** Just run the script again - it will resume from checkpoint

### If Databento API errors:

Common issues:
- **Rate limit:** Databento may throttle. Script will pause between chunks.
- **Invalid date range:** Check `backfill_databento_continuous.py` for `AVAILABLE_END_UTC`
- **API key:** Verify in `.env` file

### If database locks:

- Close any other programs accessing `gold.db`
- Make sure no other Python scripts are running

### If you want to abort:

- Press `Ctrl+C` to stop
- Script will save checkpoint
- Can resume later

---

## ✅ After Backfill Completes

### 1. Verify the data:

```bash
python check_db.py
```

**Expected:**
- bars_1m: ~3-4 million rows
- daily_features_v2: ~1800 rows (2020-12-20 to 2026-01-10)

### 2. Check date range:

```bash
python -c "import duckdb; con = duckdb.connect('gold.db'); result = con.execute('SELECT MIN(date_local), MAX(date_local), COUNT(*) FROM daily_features_v2').fetchone(); print(f'Date range: {result[0]} to {result[1]} ({result[2]} days)')"
```

**Expected:** 2020-12-20 to 2026-01-10 (~1800 days)

### 3. Run Asia ORB backtest:

```bash
python backtest_asia_orbs_comprehensive.py
```

This will generate updated results for TRADING_RULESET.md with full 5-year dataset.

---

## 📝 Notes

### Chunk Strategy:

The script backfills in 90-day chunks because:
- Easier to resume if interrupted
- Saves progress incrementally
- Avoids API timeouts on large requests

### Build Features:

The backfill script (`backfill_databento_continuous.py`) automatically calls `build_daily_features_v2.py` after each chunk, so you don't need to run it separately.

### Databento Costs:

Approximate cost (depends on your plan):
- 3 years of 1-minute OHLCV data
- Check Databento pricing for exact cost
- Typically a few dollars for historical data

---

## 🎯 Expected Timeline

| Phase | Duration | Progress Indicator |
|-------|----------|-------------------|
| 2020 (11 days) | ~15 min | Log shows dates in Dec 2020 |
| 2021 (365 days) | ~2-3 hours | Log shows 2021 dates |
| 2022 (365 days) | ~2-3 hours | Log shows 2022 dates |
| 2023 (365 days) | ~2-3 hours | Log shows 2023 dates |
| **Total** | **~4-8 hours** | Log shows "COMPLETE" |

### Overnight Run:

Start at: 10 PM
Expected done by: 6 AM (with buffer)

---

## 🔧 Troubleshooting Commands

### Kill stuck backfill:

```bash
# Windows - if script hangs
Ctrl+C
```

### Reset and start over:

```bash
# Remove checkpoint
del backfill_overnight_checkpoint.txt

# Run again
python backfill_overnight_2020_2023.py
```

### Manual date range backfill:

If script fails on a specific date range:

```bash
python backfill_databento_continuous.py 2022-06-01 2022-06-30
```

---

## ✅ Success Criteria

After backfill, you should have:

- ✅ bars_1m: 2020-12-20 to 2026-01-10 (~3-4M rows)
- ✅ bars_5m: 2020-12-20 to 2026-01-10 (~700K rows)
- ✅ daily_features_v2: 2020-12-20 to 2026-01-10 (~1800 rows)
- ✅ All 6 ORBs calculated for each day
- ✅ Log file shows "BACKFILL COMPLETE!"

---

## 🚀 Ready to Run?

```bash
# Start the overnight backfill
python backfill_overnight_2020_2023.py
```

Then go to bed. Check results in the morning!
