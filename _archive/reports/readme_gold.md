

Gold (MGC) Data Pipeline — README
Purpose

This project builds a clean, replayable local dataset for Micro Gold futures (MGC / MGC1!) to support:

ORB-based discretionary trading

Systematic backtesting

Session statistics (Asia / London / NY)

Long-range historical analysis without CSVs

Primary focus:

09:00, 10:00, 11:00 ORBs

Secondary: 18:00, 23:00, 00:30

High-Level Architecture

Source → Normalize → Store → Aggregate → Feature Build

Data sources:

Databento (GLBX.MDP3) → used for all historical backfill

ProjectX → optional / not used for deep history

Storage:

Local DuckDB file (gold.db)

Granularity:

Raw: 1-minute bars

Derived: 5-minute bars

Daily: session + ORB features

All steps are idempotent (safe to re-run).

Time & Calendar Model (IMPORTANT)
Trading Day Definition

Local timezone: Australia/Brisbane (UTC+10)

Trading day window:
00:00 local → next 00:00 local

This is intentional and consistent across:

Backfills

Aggregations

Feature building

Expected 1-Minute Counts

Full weekday: ~1440 rows

Partial holidays / roll days: fewer

Weekends: 0 rows (expected)

Futures & Contracts (Why you see MGCG4, MGCM4, etc.)

You trade MGC1! (continuous front month).

Databento provides individual contracts:

MGCG4, MGCM4, MGCV4, MGCG6, etc.

What the pipeline does

Automatically selects the front / most liquid contract per day

Stitches them into a continuous series

Stores everything under:

symbol = 'MGC'
source_symbol = actual contract (MGCG4, MGCM4, …)


This is correct and required for proper historical backtesting.

Database Schema
bars_1m

Primary raw data.

column	type
ts_utc	TIMESTAMPTZ
symbol	TEXT (MGC)
source_symbol	TEXT (actual contract)
open	DOUBLE
high	DOUBLE
low	DOUBLE
close	DOUBLE
volume	BIGINT

Primary key:

(symbol, ts_utc)


No duplicates possible.

bars_5m

Deterministic aggregation from bars_1m.

Bucket = floor(epoch(ts)/300)

open = first

close = last

high/low = extremes

volume = sum

Fully rebuildable at any time.

daily_features

One row per local trading day.

Stored features:

Session High / Low

Asia (09:00–17:00)

London (18:00–23:00)

NY Futures (23:00–02:00)

Pre-Move Travel

pre_ny_travel (18:00–23:00)

pre_orb_travel (23:00–00:30)

ORBs (ALL STORED)

Each ORB has high, low, size, break direction.

ORB	Stored
09:00	✅
10:00	✅
11:00	✅
18:00	✅
23:00	✅
00:30	✅

Break rule:

CLOSE outside range

Direction = UP, DOWN, or NONE

Missing ORBs (weekends / holidays) are stored as NULL — no crashes.

Scripts (What to Use)
Backfilling (Databento – main path)

Continuous, front-month, rollover-safe

python backfill_databento_continuous.py START_DATE END_DATE


Can run forward or backward

Safe to interrupt

Re-running replaces existing rows cleanly

Example:

python backfill_databento_continuous.py 2024-01-01 2026-01-10

Feature Building (per day)
python build_daily_features.py YYYY-MM-DD


Called automatically by backfill scripts.

Wiping Data

Use wipe_mgc.py to fully reset:

bars_1m

bars_5m

daily_features

No partial state left behind.

Reliability Guarantees

✅ No duplicate rows

✅ Rebuildable aggregates

✅ Safe restarts

✅ Contract roll handled automatically

✅ Weekend / holiday aware

✅ Matches how you actually trade

What This Project Is NOT

Not a live trading engine

Not tick-perfect microstructure research

Not dependent on ProjectX history limits

Not CSV-based