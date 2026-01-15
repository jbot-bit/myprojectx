-- ============================================================================
-- Schema Migration: Fix daily_features_v2 + v_orb_trades Inconsistencies
-- ============================================================================
-- Goal: Make schema internally consistent for structural analysis
-- Changes:
--   1. Standardize RSI naming (rsi_at_0030 → rsi_at_orb)
--   2. Add MAE/MFE columns to daily_features_v2
--   3. Update v_orb_trades view to include MAE/MFE + RSI
--   4. Add instrument column to orb_trades_1m_exec (optional)
-- ============================================================================

-- ============================================================================
-- STEP 1: Add RSI column with new naming to daily_features_v2
-- ============================================================================

-- Add new column
ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS rsi_at_orb DOUBLE;

-- Backfill from old column
UPDATE daily_features_v2
SET rsi_at_orb = rsi_at_0030
WHERE rsi_at_0030 IS NOT NULL;

-- Note: We keep rsi_at_0030 for backward compatibility (don't drop it)
-- Analytics should use rsi_at_orb going forward

SELECT 'Step 1 complete: RSI column added/backfilled' AS status;


-- ============================================================================
-- STEP 2: Add MAE/MFE columns to daily_features_v2
-- ============================================================================

-- Add MAE columns for all ORBs
ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS orb_0900_mae DOUBLE;
ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS orb_1000_mae DOUBLE;
ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS orb_1100_mae DOUBLE;
ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS orb_1800_mae DOUBLE;
ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS orb_2300_mae DOUBLE;
ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS orb_0030_mae DOUBLE;

-- Add MFE columns for all ORBs
ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS orb_0900_mfe DOUBLE;
ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS orb_1000_mfe DOUBLE;
ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS orb_1100_mfe DOUBLE;
ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS orb_1800_mfe DOUBLE;
ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS orb_2300_mfe DOUBLE;
ALTER TABLE daily_features_v2 ADD COLUMN IF NOT EXISTS orb_0030_mfe DOUBLE;

-- Note: These columns are added but not backfilled yet
-- Backfill will happen in build_daily_features.py when it's updated

SELECT 'Step 2 complete: MAE/MFE columns added' AS status;


-- ============================================================================
-- STEP 3: Recreate v_orb_trades view with MAE/MFE + RSI
-- ============================================================================

DROP VIEW IF EXISTS v_orb_trades;

CREATE VIEW v_orb_trades AS
-- 0900 ORB
SELECT
    date_local,
    instrument,
    '0900' AS orb_time,
    orb_0900_high AS orb_high,
    orb_0900_low AS orb_low,
    orb_0900_size AS orb_size,
    orb_0900_break_dir AS break_dir,
    orb_0900_mae AS mae,
    orb_0900_mfe AS mfe,
    NULL::DOUBLE AS rsi_at_orb,
    pre_orb_travel,
    pre_ny_travel,
    asia_session_high,
    asia_session_low,
    london_session_high,
    london_session_low,
    ny_session_high,
    ny_session_low
FROM daily_features_v2

UNION ALL

-- 1000 ORB
SELECT
    date_local,
    instrument,
    '1000' AS orb_time,
    orb_1000_high AS orb_high,
    orb_1000_low AS orb_low,
    orb_1000_size AS orb_size,
    orb_1000_break_dir AS break_dir,
    orb_1000_mae AS mae,
    orb_1000_mfe AS mfe,
    NULL::DOUBLE AS rsi_at_orb,
    pre_orb_travel,
    pre_ny_travel,
    asia_session_high,
    asia_session_low,
    london_session_high,
    london_session_low,
    ny_session_high,
    ny_session_low
FROM daily_features_v2

UNION ALL

-- 1100 ORB
SELECT
    date_local,
    instrument,
    '1100' AS orb_time,
    orb_1100_high AS orb_high,
    orb_1100_low AS orb_low,
    orb_1100_size AS orb_size,
    orb_1100_break_dir AS break_dir,
    orb_1100_mae AS mae,
    orb_1100_mfe AS mfe,
    NULL::DOUBLE AS rsi_at_orb,
    pre_orb_travel,
    pre_ny_travel,
    asia_session_high,
    asia_session_low,
    london_session_high,
    london_session_low,
    ny_session_high,
    ny_session_low
FROM daily_features_v2

UNION ALL

-- 1800 ORB
SELECT
    date_local,
    instrument,
    '1800' AS orb_time,
    orb_1800_high AS orb_high,
    orb_1800_low AS orb_low,
    orb_1800_size AS orb_size,
    orb_1800_break_dir AS break_dir,
    orb_1800_mae AS mae,
    orb_1800_mfe AS mfe,
    NULL::DOUBLE AS rsi_at_orb,
    pre_orb_travel,
    pre_ny_travel,
    asia_session_high,
    asia_session_low,
    london_session_high,
    london_session_low,
    ny_session_high,
    ny_session_low
FROM daily_features_v2

UNION ALL

-- 2300 ORB
SELECT
    date_local,
    instrument,
    '2300' AS orb_time,
    orb_2300_high AS orb_high,
    orb_2300_low AS orb_low,
    orb_2300_size AS orb_size,
    orb_2300_break_dir AS break_dir,
    orb_2300_mae AS mae,
    orb_2300_mfe AS mfe,
    NULL::DOUBLE AS rsi_at_orb,
    pre_orb_travel,
    pre_ny_travel,
    asia_session_high,
    asia_session_low,
    london_session_high,
    london_session_low,
    ny_session_high,
    ny_session_low
FROM daily_features_v2

UNION ALL

-- 0030 ORB (includes RSI)
SELECT
    date_local,
    instrument,
    '0030' AS orb_time,
    orb_0030_high AS orb_high,
    orb_0030_low AS orb_low,
    orb_0030_size AS orb_size,
    orb_0030_break_dir AS break_dir,
    orb_0030_mae AS mae,
    orb_0030_mfe AS mfe,
    rsi_at_orb AS rsi_at_orb,
    pre_orb_travel,
    pre_ny_travel,
    asia_session_high,
    asia_session_low,
    london_session_high,
    london_session_low,
    ny_session_high,
    ny_session_low
FROM daily_features_v2;

SELECT 'Step 3 complete: v_orb_trades view recreated with MAE/MFE/RSI' AS status;


-- ============================================================================
-- STEP 4 (OPTIONAL): Add instrument column to orb_trades_1m_exec
-- ============================================================================

-- Add instrument column
ALTER TABLE orb_trades_1m_exec ADD COLUMN IF NOT EXISTS instrument VARCHAR DEFAULT 'MGC';

-- Backfill existing rows
UPDATE orb_trades_1m_exec
SET instrument = 'MGC'
WHERE instrument IS NULL;

-- Make it NOT NULL after backfill
-- Note: DuckDB doesn't support ALTER COLUMN SET NOT NULL directly
-- We'll handle this in init_db.py when creating new tables

SELECT 'Step 4 complete: instrument column added to orb_trades_1m_exec' AS status;


-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

SELECT 'Schema migration complete!' AS status;
