-- ============================================================================
-- Schema Verification: Check Migration Completed Successfully
-- ============================================================================
-- This script verifies:
--   1. RSI column naming is correct
--   2. MAE/MFE columns exist in daily_features_v2
--   3. v_orb_trades view has correct columns
--   4. instrument column exists in orb_trades_1m_exec
-- ============================================================================

SELECT '========================================' AS separator;
SELECT 'SCHEMA VERIFICATION REPORT' AS title;
SELECT '========================================' AS separator;


-- ============================================================================
-- CHECK 1: RSI Column Naming in daily_features_v2
-- ============================================================================

SELECT '1. RSI Column Status' AS check_name;

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'daily_features_v2'
  AND column_name IN ('rsi_at_orb', 'rsi_at_0030')
ORDER BY column_name;

-- Expected result:
-- rsi_at_0030 | DOUBLE (old, kept for compatibility)
-- rsi_at_orb  | DOUBLE (new, standardized name)


-- ============================================================================
-- CHECK 2: MAE/MFE Columns in daily_features_v2
-- ============================================================================

SELECT '2. MAE/MFE Column Count' AS check_name;

SELECT COUNT(*) AS mae_mfe_column_count
FROM information_schema.columns
WHERE table_name = 'daily_features_v2'
  AND (column_name LIKE 'orb_%_mae' OR column_name LIKE 'orb_%_mfe');

-- Expected result: 12 (6 ORBs × 2 columns each)

SELECT 'MAE/MFE Column List:' AS detail;

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'daily_features_v2'
  AND (column_name LIKE 'orb_%_mae' OR column_name LIKE 'orb_%_mfe')
ORDER BY column_name;

-- Expected columns:
-- orb_0030_mae, orb_0030_mfe
-- orb_0900_mae, orb_0900_mfe
-- orb_1000_mae, orb_1000_mfe
-- orb_1100_mae, orb_1100_mfe
-- orb_1800_mae, orb_1800_mfe
-- orb_2300_mae, orb_2300_mfe


-- ============================================================================
-- CHECK 3: v_orb_trades View Columns
-- ============================================================================

SELECT '3. v_orb_trades View Status' AS check_name;

SELECT COUNT(*) AS view_exists
FROM information_schema.views
WHERE table_name = 'v_orb_trades';

-- Expected result: 1 (view exists)

SELECT 'v_orb_trades Columns:' AS detail;

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'v_orb_trades'
  AND column_name IN ('mae', 'mfe', 'rsi_at_orb')
ORDER BY column_name;

-- Expected result:
-- mae         | DOUBLE
-- mfe         | DOUBLE
-- rsi_at_orb  | DOUBLE


-- ============================================================================
-- CHECK 4: instrument Column in orb_trades_1m_exec
-- ============================================================================

SELECT '4. orb_trades_1m_exec Instrument Column' AS check_name;

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'orb_trades_1m_exec'
  AND column_name = 'instrument';

-- Expected result:
-- instrument | VARCHAR


-- ============================================================================
-- CHECK 5: Sample Data Verification
-- ============================================================================

SELECT '5. Sample Data Check' AS check_name;

-- Check RSI backfill
SELECT
    COUNT(*) AS total_rows,
    COUNT(rsi_at_orb) AS rsi_at_orb_populated,
    COUNT(rsi_at_0030) AS rsi_at_0030_populated
FROM daily_features_v2;

-- Expected: rsi_at_orb_populated = rsi_at_0030_populated (successful backfill)

-- Check MAE/MFE data (will be NULL until backfill script runs)
SELECT
    COUNT(*) AS total_rows,
    COUNT(orb_0900_mae) AS orb_0900_mae_populated,
    COUNT(orb_0900_mfe) AS orb_0900_mfe_populated
FROM daily_features_v2;

-- Expected: 0 populated initially (columns exist but not backfilled yet)


-- ============================================================================
-- CHECK 6: View Query Test
-- ============================================================================

SELECT '6. View Query Test' AS check_name;

-- Test that view can be queried
SELECT COUNT(*) AS view_row_count
FROM v_orb_trades;

-- Expected: Should return total rows (6 × number of trading days)

-- Test MAE/MFE columns are accessible
SELECT
    orb_time,
    COUNT(*) AS rows,
    COUNT(mae) AS mae_count,
    COUNT(mfe) AS mfe_count,
    COUNT(rsi_at_orb) AS rsi_count
FROM v_orb_trades
GROUP BY orb_time
ORDER BY orb_time;

-- Expected:
-- - mae_count = 0 (not backfilled yet)
-- - mfe_count = 0 (not backfilled yet)
-- - rsi_count = 0 for 0900/1000/1100/1800/2300 (NULL by design)
-- - rsi_count = N for 0030 (where N = backfilled RSI values)


-- ============================================================================
-- VERIFICATION SUMMARY
-- ============================================================================

SELECT '========================================' AS separator;
SELECT 'VERIFICATION COMPLETE' AS summary;
SELECT '========================================' AS separator;

SELECT 'Expected results:' AS note;
SELECT '  1. Both rsi_at_orb and rsi_at_0030 exist in daily_features_v2' AS check1;
SELECT '  2. 12 MAE/MFE columns exist (not yet backfilled)' AS check2;
SELECT '  3. v_orb_trades has mae, mfe, rsi_at_orb columns' AS check3;
SELECT '  4. orb_trades_1m_exec has instrument column' AS check4;
SELECT '  5. RSI data successfully backfilled to rsi_at_orb' AS check5;
SELECT '  6. View queries successfully (even with NULL MAE/MFE)' AS check6;
