"""
EXAMPLE: How to Use the Canonical Execution Engine

This demonstrates the correct pattern for creating backtest scripts:
1. Import the execution engine
2. Call simulate_orb_trade() for each test
3. Store results in your table
4. NEVER reimplement entry/stop/target/outcome logic

This replaces the pattern in backtest_orb_exec_*.py scripts.
"""

import duckdb
import argparse
from datetime import date
from execution_engine import simulate_orb_trade, ORB_TIMES

DB_PATH = "gold.db"

def ensure_schema(con: duckdb.DuckDBPyConnection, table_name: str):
    """Create results table"""
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            date_local DATE NOT NULL,
            orb VARCHAR NOT NULL,
            mode VARCHAR NOT NULL,
            confirm_bars INTEGER NOT NULL,
            rr DOUBLE NOT NULL,
            sl_mode VARCHAR NOT NULL,
            buffer_ticks DOUBLE NOT NULL,

            outcome VARCHAR,
            direction VARCHAR,
            entry_ts TIMESTAMP,
            entry_price DOUBLE,
            stop_price DOUBLE,
            target_price DOUBLE,
            stop_ticks DOUBLE,
            r_multiple DOUBLE,
            entry_delay_bars INTEGER,
            mae_r DOUBLE,
            mfe_r DOUBLE,

            execution_mode VARCHAR,
            execution_params VARCHAR,  -- JSON string

            PRIMARY KEY (date_local, orb, mode, confirm_bars, rr, sl_mode, buffer_ticks)
        )
    """)

def run_backtest(
    table_name: str = "orb_trades_example",
    mode: str = "1m",
    confirm_bars: int = 1,
    rr: float = 2.0,
    sl_mode: str = "full",
    buffer_ticks: float = 0,
    max_stop_ticks: float = 100,
    asia_tp_cap_ticks: float = 150,
):
    """
    Run backtest using the CANONICAL EXECUTION ENGINE.

    NO execution logic is implemented here.
    This script ONLY:
    1. Iterates over dates/ORBs
    2. Calls simulate_orb_trade()
    3. Stores results
    """
    con = duckdb.connect(DB_PATH)
    ensure_schema(con, table_name)

    # Get trading dates
    days = con.execute("""
        SELECT date_local
        FROM daily_features_v2
        ORDER BY date_local
    """).fetchall()

    total_days = len(days)
    inserted = 0
    skipped = {
        'SKIPPED_NO_ORB': 0,
        'SKIPPED_NO_BARS': 0,
        'SKIPPED_NO_ENTRY': 0,
        'SKIPPED_BIG_STOP': 0,
    }

    print(f"\nRUN: mode={mode} | confirm={confirm_bars} | RR={rr} | SL={sl_mode}")
    print(f"Days: {total_days} | ORBs per day: {len(ORB_TIMES)}\n")

    for idx, (d,) in enumerate(days, start=1):
        for orb in ORB_TIMES.keys():
            # CALL CANONICAL ENGINE (do not reimplement execution logic)
            result = simulate_orb_trade(
                con=con,
                date_local=d,
                orb=orb,
                mode=mode,
                confirm_bars=confirm_bars,
                rr=rr,
                sl_mode=sl_mode,
                buffer_ticks=buffer_ticks,
                max_stop_ticks=max_stop_ticks,
                asia_tp_cap_ticks=asia_tp_cap_ticks,
            )

            # Track skips
            if result.outcome.startswith('SKIPPED'):
                skipped[result.outcome] = skipped.get(result.outcome, 0) + 1
                continue

            # Store result
            import json
            con.execute(f"""
                INSERT OR REPLACE INTO {table_name}
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                d, orb, mode, confirm_bars, rr, sl_mode, buffer_ticks,
                result.outcome,
                result.direction,
                result.entry_ts,
                result.entry_price,
                result.stop_price,
                result.target_price,
                result.stop_ticks,
                result.r_multiple,
                result.entry_delay_bars,
                result.mae_r,
                result.mfe_r,
                result.execution_mode,
                json.dumps(result.execution_params),
            ])
            inserted += 1

        if idx % 10 == 0:
            con.commit()
            print(f"[{idx:>4}/{total_days}] inserted={inserted} | skipped={sum(skipped.values())}")

    con.commit()
    print(f"\nDONE: inserted={inserted}")
    for skip_type, count in skipped.items():
        print(f"  {skip_type}: {count}")

    con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Example backtest using canonical execution engine"
    )
    parser.add_argument("--table", default="orb_trades_example", help="Output table name")
    parser.add_argument("--mode", default="1m", choices=["1m", "5m"], help="Bar timeframe")
    parser.add_argument("--confirm", type=int, default=1, help="Close confirmations required")
    parser.add_argument("--rr", type=float, default=2.0, help="Risk:reward ratio")
    parser.add_argument("--sl-mode", default="full", choices=["full", "half"], help="Stop loss mode")
    parser.add_argument("--buffer", type=float, default=0, help="Entry buffer in ticks")

    args = parser.parse_args()

    run_backtest(
        table_name=args.table,
        mode=args.mode,
        confirm_bars=args.confirm,
        rr=args.rr,
        sl_mode=args.sl_mode,
        buffer_ticks=args.buffer,
    )
