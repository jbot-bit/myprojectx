# Gap Research Archive - January 2026

## About This Archive

This directory contains all experimental gap research files conducted in January 2026. These files have been moved from the root directory to keep the project organized.

**Consolidated Guide:** All findings are summarized in the root directory file `GAP_RESEARCH_COMPLETE.md`. Use that as your primary reference.

---

## Directory Structure

```
_archive/gap_research_jan2026/
├── scripts/          # Python analysis scripts (12 files)
├── data/             # CSV output files (4 files)
├── reports/          # Individual markdown reports (5 files + original prompt)
└── README.md         # This file
```

---

## Scripts (12 files)

### Gap Fade Analysis
1. `analyze_gap_fill_behavior.py` - Initial gap fill detection
2. `analyze_gap_fill_timing.py` - Timing distribution analysis
3. `analyze_gap_adverse_excursion.py` - Risk/adverse excursion analysis
4. `gap_fade_win_rate_analysis.py` - Win rate calculations by strategy
5. `check_weekend_gap.py` - Weekend gap specific analysis

### Gap Continuation Analysis
6. `gap_research_fast.py` - Baseline 2R strategy research
7. `gap_research_variations.py` - Robustness testing (9 variations)
8. `gap_analysis_simple.py` - Simplified analysis
9. `gap_analysis_visualize.py` - Detailed statistics and visualization
10. `export_for_gap_research.py` - Data export utility
11. `research_gap_continuation.py` - Initial exploration (v1)
12. `research_gap_continuation_v2.py` - Enhanced analysis (v2)

---

## Data (4 files)

1. `gap_fill_analysis.csv` - 448 gaps analyzed (424 filled, 24 unfilled)
2. `gap_fast_research_trades.csv` - 500 continuation trades with P&L
3. `gap_trades_detailed.csv` - Trades with cumulative R and drawdown
4. `gap_equity_curve.csv` - Equity curve data for visualization

---

## Reports (5 markdown + 1 prompt)

1. `GAP_RESEARCH_EXECUTIVE_SUMMARY.md` - Executive summary of both strategies
2. `GAP_FADE_FINAL_SUMMARY.md` - Comprehensive fade strategy guide
3. `GAP_FADE_QUICK_REFERENCE.md` - One-page fade trading card
4. `GAP_FILL_TIMING_GUIDE.md` - When to fade vs when to wait
5. `GAP_CONTINUATION_RESEARCH_REPORT.md` - Full continuation research report
6. `gaptest.txt` - Original research prompt from user

**All 5 reports have been consolidated into `/GAP_RESEARCH_COMPLETE.md` in the root directory.**

---

## Key Findings Summary

### Gap Fade Strategy
- **Win Rate:** 74% (for gaps 0.0-1.0 ticks)
- **Sample:** 424 filled gaps tested
- **Edge:** +14% above breakeven
- **Method:** Trade opposite to small gaps immediately
- **Status:** APPROVED for trading

### Gap Continuation Strategy  
- **Win Rate:** 25% (for 5R configuration)
- **Expectancy:** +0.52R per trade
- **Sample:** 500 trades, IS/OOS validated
- **Method:** Trade with gap direction, 5R targets
- **Status:** APPROVED for trading

---

## How to Use These Files

### To Reproduce Research
```bash
# Gap fade analysis
cd _archive/gap_research_jan2026/scripts
python analyze_gap_fill_timing.py
python analyze_gap_adverse_excursion.py
python gap_fade_win_rate_analysis.py

# Gap continuation analysis
python gap_research_fast.py
python gap_research_variations.py
python gap_analysis_visualize.py
```

### To Update with Fresh Data
1. Update gold.db with new bars (see main CLAUDE.md)
2. Re-run analysis scripts from this directory
3. Compare new results to original findings
4. Update GAP_RESEARCH_COMPLETE.md if findings change

---

## Why Files Were Archived

On January 19, 2026, the project root directory was cluttered with 22 gap research files. To maintain clean project structure (see PROJECT_STRUCTURE.md), all experimental/research files were consolidated and archived:

- **Before:** 22 scattered files in root (5 markdown, 12 Python, 4 CSV, 1 txt)
- **After:** 1 consolidated guide in root (GAP_RESEARCH_COMPLETE.md), all others archived here

This follows the project guideline: "Root directory contains only production-ready code and documentation."

---

## Archive Date

**Created:** January 19, 2026
**Research Period:** January 2026 (dates TBD based on file timestamps)
**Consolidated By:** Claude Sonnet 4.5

---

## Questions?

Refer to `/GAP_RESEARCH_COMPLETE.md` for the complete consolidated guide.

For implementation details, see the main trading strategy files in `/trading_app/`.
