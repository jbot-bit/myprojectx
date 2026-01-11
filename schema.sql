-- DuckDB schema (v5) - synchronized with build_daily_features.py
-- Added: ATR_20, session types, ORB outcomes (WIN/LOSS/NO_TRADE + R-multiple + MAE/MFE)

CREATE TABLE IF NOT EXISTS bars_1m (
  ts_utc        TIMESTAMPTZ NOT NULL,
  symbol        TEXT NOT NULL,          -- logical symbol, e.g. 'MGC'
  source_symbol TEXT,                   -- actual contract stream, e.g. 'MGCG6'
  open          DOUBLE NOT NULL,
  high          DOUBLE NOT NULL,
  low           DOUBLE NOT NULL,
  close         DOUBLE NOT NULL,
  volume        BIGINT NOT NULL,
  PRIMARY KEY (symbol, ts_utc)
);

CREATE TABLE IF NOT EXISTS bars_5m (
  ts_utc        TIMESTAMPTZ NOT NULL,
  symbol        TEXT NOT NULL,
  source_symbol TEXT,
  open          DOUBLE NOT NULL,
  high          DOUBLE NOT NULL,
  low           DOUBLE NOT NULL,
  close         DOUBLE NOT NULL,
  volume        BIGINT NOT NULL,
  PRIMARY KEY (symbol, ts_utc)
);

CREATE TABLE IF NOT EXISTS daily_features (
  date_local     DATE,
  instrument     TEXT,

  -- Session high/low
  asia_high      DOUBLE,
  asia_low       DOUBLE,
  asia_range     DOUBLE,
  london_high    DOUBLE,
  london_low     DOUBLE,
  ny_high        DOUBLE,
  ny_low         DOUBLE,

  -- Pre-move travel
  pre_ny_travel  DOUBLE,
  pre_orb_travel DOUBLE,

  -- ATR and session types
  atr_20         DOUBLE,
  asia_type      TEXT,
  london_type    TEXT,
  ny_type        TEXT,

  -- ORB 09:00
  orb_0900_high        DOUBLE,
  orb_0900_low         DOUBLE,
  orb_0900_size        DOUBLE,
  orb_0900_break_dir   TEXT,
  orb_0900_outcome     TEXT,
  orb_0900_r_multiple  DOUBLE,
  orb_0900_mae         DOUBLE,
  orb_0900_mfe         DOUBLE,

  -- ORB 10:00
  orb_1000_high        DOUBLE,
  orb_1000_low         DOUBLE,
  orb_1000_size        DOUBLE,
  orb_1000_break_dir   TEXT,
  orb_1000_outcome     TEXT,
  orb_1000_r_multiple  DOUBLE,
  orb_1000_mae         DOUBLE,
  orb_1000_mfe         DOUBLE,

  -- ORB 11:00
  orb_1100_high        DOUBLE,
  orb_1100_low         DOUBLE,
  orb_1100_size        DOUBLE,
  orb_1100_break_dir   TEXT,
  orb_1100_outcome     TEXT,
  orb_1100_r_multiple  DOUBLE,
  orb_1100_mae         DOUBLE,
  orb_1100_mfe         DOUBLE,

  -- ORB 18:00
  orb_1800_high        DOUBLE,
  orb_1800_low         DOUBLE,
  orb_1800_size        DOUBLE,
  orb_1800_break_dir   TEXT,
  orb_1800_outcome     TEXT,
  orb_1800_r_multiple  DOUBLE,
  orb_1800_mae         DOUBLE,
  orb_1800_mfe         DOUBLE,

  -- ORB 23:00
  orb_2300_high        DOUBLE,
  orb_2300_low         DOUBLE,
  orb_2300_size        DOUBLE,
  orb_2300_break_dir   TEXT,
  orb_2300_outcome     TEXT,
  orb_2300_r_multiple  DOUBLE,
  orb_2300_mae         DOUBLE,
  orb_2300_mfe         DOUBLE,

  -- ORB 00:30 (with RSI)
  orb_0030_high        DOUBLE,
  orb_0030_low         DOUBLE,
  orb_0030_size        DOUBLE,
  orb_0030_break_dir   TEXT,
  orb_0030_outcome     TEXT,
  orb_0030_r_multiple  DOUBLE,
  orb_0030_mae         DOUBLE,
  orb_0030_mfe         DOUBLE,
  rsi_at_orb           DOUBLE,

  PRIMARY KEY (date_local, instrument)
);

-- Zero-lookahead features (V2)
CREATE TABLE IF NOT EXISTS daily_features_v2 (
  date_local DATE NOT NULL,
  instrument VARCHAR NOT NULL,

  pre_asia_high DOUBLE,
  pre_asia_low DOUBLE,
  pre_asia_range DOUBLE,
  pre_london_high DOUBLE,
  pre_london_low DOUBLE,
  pre_london_range DOUBLE,
  pre_ny_high DOUBLE,
  pre_ny_low DOUBLE,
  pre_ny_range DOUBLE,

  asia_high DOUBLE,
  asia_low DOUBLE,
  asia_range DOUBLE,
  london_high DOUBLE,
  london_low DOUBLE,
  london_range DOUBLE,
  ny_high DOUBLE,
  ny_low DOUBLE,
  ny_range DOUBLE,
  asia_type_code VARCHAR,
  london_type_code VARCHAR,
  pre_ny_type_code VARCHAR,

  orb_0900_high DOUBLE,
  orb_0900_low DOUBLE,
  orb_0900_size DOUBLE,
  orb_0900_break_dir VARCHAR,
  orb_0900_outcome VARCHAR,
  orb_0900_r_multiple DOUBLE,

  orb_1000_high DOUBLE,
  orb_1000_low DOUBLE,
  orb_1000_size DOUBLE,
  orb_1000_break_dir VARCHAR,
  orb_1000_outcome VARCHAR,
  orb_1000_r_multiple DOUBLE,

  orb_1100_high DOUBLE,
  orb_1100_low DOUBLE,
  orb_1100_size DOUBLE,
  orb_1100_break_dir VARCHAR,
  orb_1100_outcome VARCHAR,
  orb_1100_r_multiple DOUBLE,

  orb_1800_high DOUBLE,
  orb_1800_low DOUBLE,
  orb_1800_size DOUBLE,
  orb_1800_break_dir VARCHAR,
  orb_1800_outcome VARCHAR,
  orb_1800_r_multiple DOUBLE,

  orb_2300_high DOUBLE,
  orb_2300_low DOUBLE,
  orb_2300_size DOUBLE,
  orb_2300_break_dir VARCHAR,
  orb_2300_outcome VARCHAR,
  orb_2300_r_multiple DOUBLE,

  orb_0030_high DOUBLE,
  orb_0030_low DOUBLE,
  orb_0030_size DOUBLE,
  orb_0030_break_dir VARCHAR,
  orb_0030_outcome VARCHAR,
  orb_0030_r_multiple DOUBLE,

  rsi_at_0030 DOUBLE,
  atr_20 DOUBLE,

  PRIMARY KEY (date_local, instrument)
);

-- Flatten ORB outcomes into one row per ORB per day for analytics
CREATE OR REPLACE VIEW v_orb_trades AS
SELECT
  date_local,
  instrument,
  '0900' AS orb_time,
  orb_0900_break_dir AS break_dir,
  orb_0900_outcome AS outcome,
  orb_0900_r_multiple AS r_multiple,
  asia_type_code,
  london_type_code,
  pre_ny_type_code,
  asia_range,
  london_range,
  pre_ny_range,
  atr_20
FROM daily_features_v2
UNION ALL
SELECT
  date_local,
  instrument,
  '1000' AS orb_time,
  orb_1000_break_dir AS break_dir,
  orb_1000_outcome AS outcome,
  orb_1000_r_multiple AS r_multiple,
  asia_type_code,
  london_type_code,
  pre_ny_type_code,
  asia_range,
  london_range,
  pre_ny_range,
  atr_20
FROM daily_features_v2
UNION ALL
SELECT
  date_local,
  instrument,
  '1100' AS orb_time,
  orb_1100_break_dir AS break_dir,
  orb_1100_outcome AS outcome,
  orb_1100_r_multiple AS r_multiple,
  asia_type_code,
  london_type_code,
  pre_ny_type_code,
  asia_range,
  london_range,
  pre_ny_range,
  atr_20
FROM daily_features_v2
UNION ALL
SELECT
  date_local,
  instrument,
  '1800' AS orb_time,
  orb_1800_break_dir AS break_dir,
  orb_1800_outcome AS outcome,
  orb_1800_r_multiple AS r_multiple,
  asia_type_code,
  london_type_code,
  pre_ny_type_code,
  asia_range,
  london_range,
  pre_ny_range,
  atr_20
FROM daily_features_v2
UNION ALL
SELECT
  date_local,
  instrument,
  '2300' AS orb_time,
  orb_2300_break_dir AS break_dir,
  orb_2300_outcome AS outcome,
  orb_2300_r_multiple AS r_multiple,
  asia_type_code,
  london_type_code,
  pre_ny_type_code,
  asia_range,
  london_range,
  pre_ny_range,
  atr_20
FROM daily_features_v2
UNION ALL
SELECT
  date_local,
  instrument,
  '0030' AS orb_time,
  orb_0030_break_dir AS break_dir,
  orb_0030_outcome AS outcome,
  orb_0030_r_multiple AS r_multiple,
  asia_type_code,
  london_type_code,
  pre_ny_type_code,
  asia_range,
  london_range,
  pre_ny_range,
  atr_20
FROM daily_features_v2;

-- 1m execution backtest outputs
CREATE TABLE IF NOT EXISTS orb_trades_1m_exec (
  date_local DATE NOT NULL,
  orb VARCHAR NOT NULL,
  close_confirmations INTEGER NOT NULL,

  direction VARCHAR,
  entry_ts TIMESTAMP,
  entry_price DOUBLE,
  stop_price DOUBLE,
  target_price DOUBLE,
  stop_ticks DOUBLE,

  outcome VARCHAR,
  r_multiple DOUBLE,
  entry_delay_min INTEGER,

  PRIMARY KEY (date_local, orb, close_confirmations)
);

-- Manual/variant execution logs
CREATE TABLE IF NOT EXISTS orb_exec_results (
  date_local DATE NOT NULL,
  instrument VARCHAR NOT NULL,
  orb_time VARCHAR NOT NULL,        -- '0900','1000','1100','1800','2300','0030'
  variant VARCHAR NOT NULL,         -- e.g. '1m_close_1', '1m_close_2', '1m_close_3'
  dir VARCHAR,                      -- 'UP'/'DOWN' (NULL if no trade)

  entry_ts TIMESTAMP WITH TIME ZONE,
  entry_price DOUBLE,
  stop_price DOUBLE,
  target_price DOUBLE,

  risk_ticks DOUBLE,
  target_ticks DOUBLE,

  outcome VARCHAR,                  -- 'WIN','LOSS','NO_TRADE','SKIP'
  r_multiple DOUBLE,

  notes VARCHAR,

  PRIMARY KEY (date_local, instrument, orb_time, variant, dir)
);
