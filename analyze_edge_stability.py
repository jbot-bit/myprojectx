# analyze_edge_stability.py
# Purpose:
# - Monthly stability by ORB (and optional direction)
# - Max drawdown in R
# - Regime test (UP/DOWN/FLAT) using daily closes (auto-detected)
#
# Works with:
# - daily_features table in gold.db
# - optionally a 1m bars table containing ts + close (or similar)
#
# Usage:
#   python analyze_edge_stability.py --orb 1100
#   python analyze_edge_stability.py --orb 1100 --dir UP
#   python analyze_edge_stability.py --orb 0030 --dir UP
#
import argparse
import duckdb
from typing import Optional, Tuple, List


# ----------------------------
# Helpers: schema introspection
# ----------------------------
def table_exists(con: duckdb.DuckDBPyConnection, table: str) -> bool:
    q = """
    SELECT COUNT(*) > 0
    FROM information_schema.tables
    WHERE lower(table_name) = lower(?)
    """
    return bool(con.execute(q, [table]).fetchone()[0])


def list_columns(con: duckdb.DuckDBPyConnection, table: str) -> List[str]:
    q = """
    SELECT column_name
    FROM information_schema.columns
    WHERE lower(table_name) = lower(?)
    ORDER BY ordinal_position
    """
    return [r[0] for r in con.execute(q, [table]).fetchall()]


def find_first_existing_column(cols: List[str], candidates: List[str]) -> Optional[str]:
    cols_lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None


def find_bars_table(con: duckdb.DuckDBPyConnection) -> Optional[str]:
    # Common candidates (add yours here if needed)
    candidates = [
        "bars_1m", "ohlcv_1m", "mgc_1m", "mgc_bars_1m", "bars",
        "ohlcv", "raw_bars_1m", "ingested_bars_1m"
    ]
    for t in candidates:
        if table_exists(con, t):
            return t

    # If not found, try "best guess" by scanning for a table that has a ts_utc + close column
    tables = con.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
    """).fetchall()
    for (t,) in tables:
        cols = list_columns(con, t)
        ts_col = find_first_existing_column(cols, ["ts", "ts_utc", "timestamp", "time", "datetime"])
        close_col = find_first_existing_column(cols, ["close", "c", "last", "price"])
        if ts_col and close_col:
            return t
    return None


def detect_ts_and_close(con: duckdb.DuckDBPyConnection, table: str) -> Tuple[Optional[str], Optional[str]]:
    cols = list_columns(con, table)
    ts_col = find_first_existing_column(cols, ["ts", "ts_utc", "timestamp", "time", "datetime", "date_time"])
    close_col = find_first_existing_column(cols, ["close", "c", "last", "price"])
    return ts_col, close_col


def detect_daily_close_column(con: duckdb.DuckDBPyConnection) -> Optional[str]:
    if not table_exists(con, "daily_features_compat") and not table_exists(con, "daily_features"):
        return None
    cols = list_columns(con, "daily_features_compat" if table_exists(con, "daily_features_compat") else "daily_features")
    return find_first_existing_column(cols, ["day_close", "daily_close", "close", "close_price"])


def create_features_view(con: duckdb.DuckDBPyConnection) -> str:
    """
    Prefer daily_features_v2; expose a compatibility view with legacy columns.
    """
    if table_exists(con, "daily_features_v2"):
        con.execute("""
            CREATE OR REPLACE TEMP VIEW daily_features_compat AS
            SELECT
                date_local,
                instrument,
                asia_high, asia_low, asia_range,
                london_high, london_low, london_range,
                ny_high, ny_low, ny_range,
                atr_20,
                COALESCE(
                    CASE asia_type_code
                        WHEN 'A1_TIGHT' THEN 'TIGHT'
                        WHEN 'A2_EXPANDED' THEN 'EXPANDED'
                        WHEN 'A0_NORMAL' THEN 'NORMAL'
                        ELSE NULL
                    END,
                    CASE
                        WHEN asia_range IS NULL OR atr_20 IS NULL OR atr_20 = 0 THEN 'NO_DATA'
                        WHEN asia_range / atr_20 < 0.3 THEN 'TIGHT'
                        WHEN asia_range / atr_20 > 0.8 THEN 'EXPANDED'
                        ELSE 'NORMAL'
                    END
                ) AS asia_type,
                COALESCE(
                    CASE london_type_code
                        WHEN 'L1_SWEEP_HIGH' THEN 'SWEEP_HIGH'
                        WHEN 'L2_SWEEP_LOW' THEN 'SWEEP_LOW'
                        WHEN 'L3_EXPANSION' THEN 'EXPANSION'
                        WHEN 'L4_CONSOLIDATION' THEN 'CONSOLIDATION'
                        ELSE NULL
                    END,
                    CASE
                        WHEN london_high IS NULL OR london_low IS NULL OR asia_high IS NULL OR asia_low IS NULL THEN 'NO_DATA'
                        WHEN london_high > asia_high AND london_low < asia_low THEN 'EXPANSION'
                        WHEN london_high > asia_high THEN 'SWEEP_HIGH'
                        WHEN london_low < asia_low THEN 'SWEEP_LOW'
                        ELSE 'CONSOLIDATION'
                    END
                ) AS london_type,
                COALESCE(
                    CASE pre_ny_type_code
                        WHEN 'N1_SWEEP_HIGH' THEN 'SWEEP_HIGH'
                        WHEN 'N2_SWEEP_LOW' THEN 'SWEEP_LOW'
                        WHEN 'N3_CONSOLIDATION' THEN 'CONSOLIDATION'
                        WHEN 'N4_EXPANSION' THEN 'EXPANSION'
                        WHEN 'N0_NORMAL' THEN 'NORMAL'
                        ELSE NULL
                    END,
                    CASE
                        WHEN ny_high IS NULL OR ny_low IS NULL OR london_high IS NULL OR london_low IS NULL THEN 'NO_DATA'
                        WHEN ny_high > london_high AND ny_low < london_low THEN 'EXPANSION'
                        WHEN ny_high > london_high THEN 'SWEEP_HIGH'
                        WHEN ny_low < london_low THEN 'SWEEP_LOW'
                        ELSE 'CONSOLIDATION'
                    END
                ) AS ny_type,
                orb_0900_break_dir, orb_0900_outcome, orb_0900_r_multiple,
                orb_1000_break_dir, orb_1000_outcome, orb_1000_r_multiple,
                orb_1100_break_dir, orb_1100_outcome, orb_1100_r_multiple,
                orb_1800_break_dir, orb_1800_outcome, orb_1800_r_multiple,
                orb_2300_break_dir, orb_2300_outcome, orb_2300_r_multiple,
                orb_0030_break_dir, orb_0030_outcome, orb_0030_r_multiple
            FROM daily_features_v2
        """)
        return "daily_features_compat"

    if table_exists(con, "daily_features"):
        con.execute("CREATE OR REPLACE TEMP VIEW daily_features_compat AS SELECT * FROM daily_features")
        return "daily_features_compat"

    raise SystemExit("ERROR: No daily_features or daily_features_v2 table found.")


# ----------------------------
# Main analysis
# ----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="gold.db")
    ap.add_argument("--orb", required=True, help="0900|1000|1100|1800|2300|0030")
    ap.add_argument("--dir", default=None, help="UP|DOWN (optional)")
    ap.add_argument("--min_trades", type=int, default=15, help="min trades per month to display")
    ap.add_argument("--trend_lookback", type=int, default=60, help="days for SMA regime test")
    args = ap.parse_args()

    orb = args.orb.strip()
    direction = args.dir.upper().strip() if args.dir else None

    con = duckdb.connect(args.db, read_only=True)
    table_name = create_features_view(con)

    # ---- Validate required columns exist ----
    df_cols = list_columns(con, table_name)
    required = [
        "date_local",
        f"orb_{orb}_outcome",
        f"orb_{orb}_r_multiple",
        f"orb_{orb}_break_dir",
    ]
    missing = [c for c in required if c.lower() not in {x.lower() for x in df_cols}]
    if missing:
        raise SystemExit(f"ERROR: Missing columns in {table_name}: {missing}")

    # ---- Build trade view for selected ORB ----
    where = [f"orb_{orb}_outcome IN ('WIN','LOSS')"]
    if direction:
        where.append(f"orb_{orb}_break_dir = '{direction}'")
    where_clause = " AND ".join(where)

    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW v_trades AS
        SELECT
            date_local::DATE AS d,
            orb_{orb}_break_dir AS dir,
            orb_{orb}_outcome AS outcome,
            orb_{orb}_r_multiple::DOUBLE AS r
        FROM {table_name}
        WHERE {where_clause}
    """)

    # ---- Monthly breakdown ----
    monthly = con.execute("""
        SELECT
            strftime(d, '%Y-%m') AS month,
            COUNT(*) AS trades,
            SUM(CASE WHEN outcome='WIN' THEN 1 ELSE 0 END) AS wins,
            SUM(r) AS total_r,
            AVG(r) AS avg_r
        FROM v_trades
        GROUP BY 1
        HAVING COUNT(*) >= ?
        ORDER BY 1
    """, [args.min_trades]).fetchall()

    print("\n====================")
    label = f"MONTHLY STABILITY | ORB={orb}" + (f" {direction}" if direction else " (ALL DIRS)")
    print(label)
    print("====================")
    for m, trades, wins, total_r, avg_r in monthly:
        wr = wins / trades if trades else 0.0
        print(f"{m}: Trades={trades:4d} | WR={wr:5.1%} | TotalR={total_r:+7.1f} | AvgR={avg_r:+.2f}")

    # ---- Max drawdown (equity in R) ----
    dd = con.execute("""
        WITH ordered AS (
            SELECT
                d, r,
                ROW_NUMBER() OVER (ORDER BY d) AS n
            FROM v_trades
        ),
        eq AS (
            SELECT
                d, n,
                SUM(r) OVER (ORDER BY n ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS equity_r
            FROM ordered
        ),
        peak AS (
            SELECT
                d, n, equity_r,
                MAX(equity_r) OVER (ORDER BY n ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS peak_r
            FROM eq
        )
        SELECT
            MIN(equity_r - peak_r) AS max_drawdown_r
        FROM peak
    """).fetchone()

    print("\n====================")
    print("MAX DRAWDOWN (R)")
    print("====================")
    print(f"Max drawdown (R): {dd[0]:.2f}")

    # ---- Regime test: needs daily closes ----
    print("\n====================")
    print(f"REGIME TEST (close vs {args.trend_lookback}D SMA)")
    print("====================")

    daily_close_col = detect_daily_close_column(con)

    if daily_close_col:
        # Use daily_features close
        con.execute(f"""
            CREATE OR REPLACE TEMP VIEW v_close AS
            SELECT
                date_local::DATE AS d,
                {daily_close_col}::DOUBLE AS close
            FROM {table_name}
            WHERE {daily_close_col} IS NOT NULL
        """)
    else:
        # Try to derive from a bars table (auto-detect ts column)
        bars_table = find_bars_table(con)
        if not bars_table:
            print(f"Skipped: No daily close field found in {table_name} AND no bars table with (ts + close) detected.")
            print("Fix options:")
            print("  1) Add day_close to daily_features (or rebuild v2 with that column), OR")
            print("  2) Tell me your raw 1m bars table name, OR")
            print("  3) Rename your timestamp column to ts_utc (keep close as close)")
            return

        ts_col, close_col = detect_ts_and_close(con, bars_table)
        if not ts_col or not close_col:
            print(f"Skipped: Found bars table '{bars_table}' but couldn't detect ts/close columns.")
            print(f"Columns are: {list_columns(con, bars_table)}")
            return

        # Build daily close from bars: last close per day
        con.execute(f"""
            CREATE OR REPLACE TEMP VIEW v_close AS
            SELECT
                DATE({ts_col}) AS d,
                arg_max({close_col}, {ts_col})::DOUBLE AS close
            FROM {bars_table}
            GROUP BY 1
        """)

    look = int(args.trend_lookback)
    regime = con.execute(f"""
        WITH c AS (
            SELECT
                d, close,
                AVG(close) OVER (ORDER BY d ROWS BETWEEN {look-1} PRECEDING AND CURRENT ROW) AS sma
            FROM v_close
        ),
        reg AS (
            SELECT
                d,
                CASE
                    WHEN sma IS NULL THEN 'UNKNOWN'
                    WHEN close > sma * 1.001 THEN 'UP'
                    WHEN close < sma * 0.999 THEN 'DOWN'
                    ELSE 'FLAT'
                END AS regime
            FROM c
        )
        SELECT
            r.regime,
            COUNT(*) AS trades,
            SUM(CASE WHEN t.outcome='WIN' THEN 1 ELSE 0 END) AS wins,
            SUM(t.r) AS total_r,
            AVG(t.r) AS avg_r
        FROM v_trades t
        JOIN reg r USING (d)
        WHERE r.regime <> 'UNKNOWN'
        GROUP BY 1
        ORDER BY 1
    """).fetchall()

    if not regime:
        print("No regime results (likely missing closes for trade dates).")
        return

    for reg, trades, wins, total_r, avg_r in regime:
        wr = wins / trades if trades else 0.0
        print(f"{reg:4s}: Trades={trades:4d} | WR={wr:5.1%} | TotalR={total_r:+7.1f} | AvgR={avg_r:+.2f}")


if __name__ == "__main__":
    main()
