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
