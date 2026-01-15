"""
Build features for COMPLETE EXECUTION GRID

Tests ALL execution variants:
- ORB sizes: 5min, 10min, 15min
- Entry: close, next-open, 2-bar-confirm, with 0.5-tick buffer
- Stops: full-SL, half-SL, 75%-SL, fixed-ticks
- R:R: 1.0, 1.5, 2.0
- Confirmation: 1-bar, 2-bar, 3-bar

This creates HUNDREDS of feature combinations for comprehensive testing.
"""

import duckdb
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Tuple, List
from itertools import product

TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")

SYMBOL = "MGC"
DB_PATH = "gold.db"
TICK_SIZE = 0.1


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


class ExecutionGridBuilder:
    def __init__(self, db_path: str = DB_PATH):
        self.con = duckdb.connect(db_path)

    def _fetch_1m_bars(self, start_local: datetime, end_local: datetime) -> List[Tuple]:
        start_utc = start_local.astimezone(TZ_UTC)
        end_utc = end_local.astimezone(TZ_UTC)

        return self.con.execute(
            """
            SELECT ts_utc, open, high, low, close
            FROM bars_1m
            WHERE symbol = ?
              AND ts_utc >= ? AND ts_utc < ?
            ORDER BY ts_utc
            """,
            [SYMBOL, start_utc, end_utc],
        ).fetchall()

    def calculate_orb_variant(
        self,
        orb_start_local: datetime,
        scan_end_local: datetime,
        orb_minutes: int = 5,
        entry_method: str = "next_open",  # "close", "next_open", "2bar_confirm"
        buffer_ticks: float = 0.0,
        sl_mode: str = "full",  # "full", "half", "75pct", "fixed_20"
        close_confirmations: int = 1,
        rr: float = 1.0
    ) -> Optional[Dict]:
        """
        Calculate ORB with specified execution variant.
        """
        orb_end_local = orb_start_local + timedelta(minutes=orb_minutes)

        # 1. Build ORB
        orb_bars = self._fetch_1m_bars(orb_start_local, orb_end_local)
        if not orb_bars:
            return None

        orb_high = max(h for _, _, h, _, _ in orb_bars)
        orb_low = min(l for _, _, _, l, _ in orb_bars)
        orb_size = orb_high - orb_low
        orb_mid = (orb_high + orb_low) / 2.0

        # 2. Scan for trigger
        scan_bars = self._fetch_1m_bars(orb_end_local, scan_end_local)
        if not scan_bars:
            return {
                "high": orb_high, "low": orb_low, "size": orb_size,
                "break_dir": "NONE", "outcome": "NO_TRADE", "r_multiple": None,
                "entry_price": None, "stop_price": None, "target_price": None,
                "risk_ticks": None
            }

        buffer = buffer_ticks * TICK_SIZE

        # 3. Find trigger (N consecutive closes outside ORB)
        consec = 0
        direction = None
        trigger_idx = None
        trigger_close = None

        for i, (ts_utc, o, h, l, c) in enumerate(scan_bars):
            if c > orb_high + buffer:
                if direction != "UP":
                    direction = "UP"
                    consec = 0
                consec += 1
            elif c < orb_low - buffer:
                if direction != "DOWN":
                    direction = "DOWN"
                    consec = 0
                consec += 1
            else:
                direction = None
                consec = 0

            if consec >= close_confirmations:
                trigger_idx = i
                trigger_close = c
                break

        if direction is None:
            return {
                "high": orb_high, "low": orb_low, "size": orb_size,
                "break_dir": "NONE", "outcome": "NO_TRADE", "r_multiple": None,
                "entry_price": None, "stop_price": None, "target_price": None,
                "risk_ticks": None
            }

        # 4. Entry price (depends on entry_method)
        if entry_method == "close":
            # Entry at trigger close
            entry_price = float(trigger_close)
            entry_idx = trigger_idx
        elif entry_method == "next_open":
            # Entry at next bar open
            if trigger_idx + 1 >= len(scan_bars):
                return {
                    "high": orb_high, "low": orb_low, "size": orb_size,
                    "break_dir": direction, "outcome": "NO_TRADE", "r_multiple": None,
                    "entry_price": None, "stop_price": None, "target_price": None,
                    "risk_ticks": None
                }
            entry_bar = scan_bars[trigger_idx + 1]
            entry_price = float(entry_bar[1])  # open
            entry_idx = trigger_idx + 1
        elif entry_method == "2bar_confirm":
            # Wait for 2nd bar to close outside as well (more conservative)
            if trigger_idx + 1 >= len(scan_bars):
                return {
                    "high": orb_high, "low": orb_low, "size": orb_size,
                    "break_dir": direction, "outcome": "NO_TRADE", "r_multiple": None,
                    "entry_price": None, "stop_price": None, "target_price": None,
                    "risk_ticks": None
                }
            # Check if next bar also closes outside
            next_bar = scan_bars[trigger_idx + 1]
            next_close = float(next_bar[4])

            if direction == "UP" and next_close <= orb_high:
                # Failed 2nd confirmation
                return {
                    "high": orb_high, "low": orb_low, "size": orb_size,
                    "break_dir": "NONE", "outcome": "NO_TRADE", "r_multiple": None,
                    "entry_price": None, "stop_price": None, "target_price": None,
                    "risk_ticks": None
                }
            elif direction == "DOWN" and next_close >= orb_low:
                return {
                    "high": orb_high, "low": orb_low, "size": orb_size,
                    "break_dir": "NONE", "outcome": "NO_TRADE", "r_multiple": None,
                    "entry_price": None, "stop_price": None, "target_price": None,
                    "risk_ticks": None
                }

            # 2nd bar confirmed, enter at 3rd bar open
            if trigger_idx + 2 >= len(scan_bars):
                return {
                    "high": orb_high, "low": orb_low, "size": orb_size,
                    "break_dir": direction, "outcome": "NO_TRADE", "r_multiple": None,
                    "entry_price": None, "stop_price": None, "target_price": None,
                    "risk_ticks": None
                }
            entry_bar = scan_bars[trigger_idx + 2]
            entry_price = float(entry_bar[1])  # open
            entry_idx = trigger_idx + 2
        else:
            raise ValueError(f"Unknown entry_method: {entry_method}")

        # 5. Stop price (depends on sl_mode)
        if sl_mode == "full":
            stop_price = orb_low if direction == "UP" else orb_high
        elif sl_mode == "half":
            stop_price = orb_mid
        elif sl_mode == "75pct":
            # 75% of ORB (between mid and opposite edge)
            if direction == "UP":
                stop_price = orb_low + 0.25 * orb_size
            else:
                stop_price = orb_high - 0.25 * orb_size
        elif sl_mode.startswith("fixed_"):
            # Fixed ticks (e.g., "fixed_20" = 20 ticks = 2.0 points)
            fixed_ticks = float(sl_mode.split("_")[1])
            fixed_distance = fixed_ticks * TICK_SIZE
            if direction == "UP":
                stop_price = entry_price - fixed_distance
            else:
                stop_price = entry_price + fixed_distance
        else:
            raise ValueError(f"Unknown sl_mode: {sl_mode}")

        # 6. ENTRY-ANCHORED RISK (CRITICAL)
        risk = abs(entry_price - stop_price)
        risk_ticks = risk / TICK_SIZE

        if risk <= 0:
            return {
                "high": orb_high, "low": orb_low, "size": orb_size,
                "break_dir": direction, "outcome": "NO_TRADE", "r_multiple": None,
                "entry_price": entry_price, "stop_price": stop_price, "target_price": None,
                "risk_ticks": 0.0
            }

        # 7. Target (entry-anchored)
        if direction == "UP":
            target_price = entry_price + rr * risk
        else:
            target_price = entry_price - rr * risk

        # 8. Outcome scan (conservative: same-bar TP+SL = LOSS)
        outcome = "NO_TRADE"
        r_mult = None

        for ts_utc, o, h, l, c in scan_bars[entry_idx:]:
            h = float(h)
            l = float(l)

            if direction == "UP":
                hit_stop = l <= stop_price
                hit_target = h >= target_price

                if hit_stop and hit_target:
                    outcome = "LOSS"
                    r_mult = -1.0
                    break
                if hit_target:
                    outcome = "WIN"
                    r_mult = float(rr)
                    break
                if hit_stop:
                    outcome = "LOSS"
                    r_mult = -1.0
                    break
            else:
                hit_stop = h >= stop_price
                hit_target = l <= target_price

                if hit_stop and hit_target:
                    outcome = "LOSS"
                    r_mult = -1.0
                    break
                if hit_target:
                    outcome = "WIN"
                    r_mult = float(rr)
                    break
                if hit_stop:
                    outcome = "LOSS"
                    r_mult = -1.0
                    break

        return {
            "high": orb_high,
            "low": orb_low,
            "size": orb_size,
            "break_dir": direction,
            "outcome": outcome,
            "r_multiple": r_mult,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "target_price": target_price,
            "risk_ticks": risk_ticks
        }

    def build_execution_grid(self, trade_date: date, config_id: int, config: dict):
        """Build features for a single execution configuration."""

        # Default empty result for days with no data
        empty_result = {
            "high": None, "low": None, "size": None,
            "break_dir": None, "outcome": None, "r_multiple": None,
            "entry_price": None, "stop_price": None, "target_price": None,
            "risk_ticks": None
        }

        orb_0900 = self.calculate_orb_variant(
            _dt_local(trade_date, 9, 0),
            _dt_local(trade_date, 17, 0),
            **config
        ) or empty_result

        orb_1000 = self.calculate_orb_variant(
            _dt_local(trade_date, 10, 0),
            _dt_local(trade_date, 17, 0),
            **config
        ) or empty_result

        orb_1100 = self.calculate_orb_variant(
            _dt_local(trade_date, 11, 0),
            _dt_local(trade_date, 17, 0),
            **config
        ) or empty_result

        orb_1800 = self.calculate_orb_variant(
            _dt_local(trade_date, 18, 0),
            _dt_local(trade_date, 23, 0),
            **config
        ) or empty_result

        orb_2300 = self.calculate_orb_variant(
            _dt_local(trade_date, 23, 0),
            _dt_local(trade_date + timedelta(days=1), 0, 30),
            **config
        ) or empty_result

        orb_0030 = self.calculate_orb_variant(
            _dt_local(trade_date + timedelta(days=1), 0, 30),
            _dt_local(trade_date + timedelta(days=1), 2, 0),
            **config
        ) or empty_result

        # Insert into grid table
        self.con.execute(
            """
            INSERT OR REPLACE INTO execution_grid_results (
                date_local, config_id,
                orb_0900_break_dir, orb_0900_outcome, orb_0900_r_multiple, orb_0900_risk_ticks,
                orb_1000_break_dir, orb_1000_outcome, orb_1000_r_multiple, orb_1000_risk_ticks,
                orb_1100_break_dir, orb_1100_outcome, orb_1100_r_multiple, orb_1100_risk_ticks,
                orb_1800_break_dir, orb_1800_outcome, orb_1800_r_multiple, orb_1800_risk_ticks,
                orb_2300_break_dir, orb_2300_outcome, orb_2300_r_multiple, orb_2300_risk_ticks,
                orb_0030_break_dir, orb_0030_outcome, orb_0030_r_multiple, orb_0030_risk_ticks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                trade_date, config_id,
                orb_0900.get("break_dir"), orb_0900.get("outcome"), orb_0900.get("r_multiple"), orb_0900.get("risk_ticks"),
                orb_1000.get("break_dir"), orb_1000.get("outcome"), orb_1000.get("r_multiple"), orb_1000.get("risk_ticks"),
                orb_1100.get("break_dir"), orb_1100.get("outcome"), orb_1100.get("r_multiple"), orb_1100.get("risk_ticks"),
                orb_1800.get("break_dir"), orb_1800.get("outcome"), orb_1800.get("r_multiple"), orb_1800.get("risk_ticks"),
                orb_2300.get("break_dir"), orb_2300.get("outcome"), orb_2300.get("r_multiple"), orb_2300.get("risk_ticks"),
                orb_0030.get("break_dir"), orb_0030.get("outcome"), orb_0030.get("r_multiple"), orb_0030.get("risk_ticks"),
            ],
        )

    def init_schema(self):
        """Create table for grid results."""
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS execution_grid_configs (
                config_id INTEGER PRIMARY KEY,
                orb_minutes INTEGER,
                entry_method VARCHAR,
                buffer_ticks DOUBLE,
                sl_mode VARCHAR,
                close_confirmations INTEGER,
                rr DOUBLE
            )
        """)

        self.con.execute("""
            CREATE TABLE IF NOT EXISTS execution_grid_results (
                date_local DATE NOT NULL,
                config_id INTEGER NOT NULL,

                orb_0900_break_dir VARCHAR,
                orb_0900_outcome VARCHAR,
                orb_0900_r_multiple DOUBLE,
                orb_0900_risk_ticks DOUBLE,

                orb_1000_break_dir VARCHAR,
                orb_1000_outcome VARCHAR,
                orb_1000_r_multiple DOUBLE,
                orb_1000_risk_ticks DOUBLE,

                orb_1100_break_dir VARCHAR,
                orb_1100_outcome VARCHAR,
                orb_1100_r_multiple DOUBLE,
                orb_1100_risk_ticks DOUBLE,

                orb_1800_break_dir VARCHAR,
                orb_1800_outcome VARCHAR,
                orb_1800_r_multiple DOUBLE,
                orb_1800_risk_ticks DOUBLE,

                orb_2300_break_dir VARCHAR,
                orb_2300_outcome VARCHAR,
                orb_2300_r_multiple DOUBLE,
                orb_2300_risk_ticks DOUBLE,

                orb_0030_break_dir VARCHAR,
                orb_0030_outcome VARCHAR,
                orb_0030_r_multiple DOUBLE,
                orb_0030_risk_ticks DOUBLE,

                PRIMARY KEY (date_local, config_id)
            )
        """)
        self.con.commit()

    def close(self):
        self.con.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build execution grid features")
    parser.add_argument("start_date", type=str)
    parser.add_argument("end_date", type=str, nargs="?", default=None)
    args = parser.parse_args()

    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date) if args.end_date else start_date

    # Define execution grid
    orb_sizes = [5, 10, 15]
    entry_methods = ["close", "next_open", "2bar_confirm"]
    buffer_options = [0.0, 0.5]
    sl_modes = ["full", "half", "75pct"]
    confirmations = [1, 2]
    rr_values = [1.0, 1.5, 2.0]

    configs = []
    config_id = 0

    for orb_min, entry, buf, sl, confirm, rr in product(
        orb_sizes, entry_methods, buffer_options, sl_modes, confirmations, rr_values
    ):
        configs.append({
            "config_id": config_id,
            "orb_minutes": orb_min,
            "entry_method": entry,
            "buffer_ticks": buf,
            "sl_mode": sl,
            "close_confirmations": confirm,
            "rr": rr
        })
        config_id += 1

    print("="*80)
    print("EXECUTION GRID BUILDER")
    print("="*80)
    print(f"Date range: {start_date} to {end_date}")
    print(f"Total configs: {len(configs)}")
    print(f"Total days: {(end_date - start_date).days + 1}")
    print(f"Total backtest runs: {len(configs) * ((end_date - start_date).days + 1)}")
    print()
    print("This will take HOURS. Progress will be shown every 10 days.")
    print()

    builder = ExecutionGridBuilder()
    builder.init_schema()

    # Store configs
    for cfg in configs:
        builder.con.execute("""
            INSERT OR REPLACE INTO execution_grid_configs VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [cfg["config_id"], cfg["orb_minutes"], cfg["entry_method"], cfg["buffer_ticks"],
              cfg["sl_mode"], cfg["close_confirmations"], cfg["rr"]])
    builder.con.commit()

    # Build features for each date and config with CHECKPOINT/RESUME
    cur = start_date
    day_count = 0

    # Find last processed date (RESUME capability)
    last_processed = builder.con.execute("""
        SELECT MAX(date_local) FROM execution_grid_results
    """).fetchone()[0]

    if last_processed:
        last_date = date.fromisoformat(str(last_processed))
        if last_date >= start_date:
            cur = last_date + timedelta(days=1)
            day_count = (cur - start_date).days
            print(f"RESUMING from {cur} (last processed: {last_date})")
            print()

    while cur <= end_date:
        try:
            for cfg in configs:
                builder.build_execution_grid(cur, cfg["config_id"], {
                    "orb_minutes": cfg["orb_minutes"],
                    "entry_method": cfg["entry_method"],
                    "buffer_ticks": cfg["buffer_ticks"],
                    "sl_mode": cfg["sl_mode"],
                    "close_confirmations": cfg["close_confirmations"],
                    "rr": cfg["rr"]
                })

            day_count += 1
            if day_count % 10 == 0:
                builder.con.commit()
                print(f"[{day_count} days processed] {cur}")

        except Exception as e:
            print(f"ERROR on {cur}: {e}")
            print("Committing progress and continuing...")
            builder.con.commit()

        cur += timedelta(days=1)

    builder.con.commit()
    builder.close()

    print()
    print(f"COMPLETED: {len(configs)} configs x {day_count} days = {len(configs) * day_count} backtest runs")


if __name__ == "__main__":
    main()
