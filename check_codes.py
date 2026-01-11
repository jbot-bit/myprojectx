import duckdb


CREATE_VIEW_SQL = """
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
"""


def main() -> None:
  con = duckdb.connect("gold.db")
  con.execute(CREATE_VIEW_SQL)

  row_count = con.execute("SELECT COUNT(*) AS rows FROM v_orb_trades").fetchone()[0]
  print(f"v_orb_trades row count: {row_count}")

  con.close()


if __name__ == "__main__":
  main()
