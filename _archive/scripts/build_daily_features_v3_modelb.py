"""
Daily Feature Builder V3 - MODEL B (Entry-Anchored, 10-min ORB, Next-Bar-Open Entry)
=====================================================================================

EXECUTION MODEL B (LOCKED):
---------------------------
1. ORB: 5 minutes (e.g., 00:30-00:35 Brisbane)
2. Trigger: Wait for 1m close outside ORB (with optional buffer)
3. Entry: Next 1m bar OPEN (the bar immediately after confirmation close)
4. Risk: |entry - stop| (ENTRY-ANCHORED, NOT ORB-edge-to-stop)
5. Target: entry +/- (R * RR)
6. Same-bar rule: If TP and SL both touched in same 1m bar -> LOSS

CRITICAL DIFFERENCES FROM V2:
- Entry at NEXT BAR OPEN (not close price)
- Risk calculated from ENTRY to STOP (not ORB edge to stop)
- ORB is 5 minutes (same as before)
- This eliminates fake edges from ORB-anchored math

Usage:
  python build_daily_features_v3_modelb.py 2024-01-01 2026-01-10
  python build_daily_features_v3_modelb.py 2024-01-01 2026-01-10 --sl-mode half
"""

import duckdb
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Tuple, List

TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")

SYMBOL = "MGC"
DB_PATH = "gold.db"
TICK_SIZE = 0.1

RR_DEFAULT = 1.0
SL_MODE = "full"  # Default: "full" = stop at opposite edge; "half" = stop at midpoint


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


class FeatureBuilderV3:
    def __init__(self, db_path: str = DB_PATH, sl_mode: str = "full", table_name: str = "daily_features_v3"):
        self.con = duckdb.connect(db_path)
        self.sl_mode = sl_mode
        self.table_name = table_name

    def _fetch_1m_bars(self, start_local: datetime, end_local: datetime) -> List[Tuple[datetime, float, float, float, float]]:
        """Fetch 1m bars with OHLC."""
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

    def calculate_orb_modelb(
        self,
        orb_start_local: datetime,
        scan_end_local: datetime,
        rr: float = RR_DEFAULT,
        sl_mode: str = SL_MODE,
        buffer_ticks: float = 0.0,
        orb_minutes: int = 5
    ) -> Optional[Dict]:
        """
        Calculate ORB with Model B execution.

        Args:
            orb_start_local: ORB start time (local)
            scan_end_local: Scan window end time (local)
            rr: Risk/reward ratio for target
            sl_mode: "full" = stop at opposite edge, "half" = stop at midpoint
            buffer_ticks: Buffer ticks outside ORB for trigger (e.g., 0.5 = 0.05 points)
            orb_minutes: ORB duration in minutes (default 5)

        Returns:
            Dict with keys: high, low, size, break_dir, outcome, r_multiple, entry_price,
                           stop_price, target_price, risk_ticks, reward_ticks
        """
        orb_end_local = orb_start_local + timedelta(minutes=orb_minutes)

        # 1. Build ORB from first N minutes
        orb_bars = self._fetch_1m_bars(orb_start_local, orb_end_local)
        if not orb_bars:
            return None

        orb_high = max(h for _, _, h, _, _ in orb_bars)
        orb_low = min(l for _, _, _, l, _ in orb_bars)
        orb_size = orb_high - orb_low
        orb_mid = (orb_high + orb_low) / 2.0

        # 2. Scan for trigger AFTER ORB completes
        scan_bars = self._fetch_1m_bars(orb_end_local, scan_end_local)
        if not scan_bars:
            return {
                "high": orb_high, "low": orb_low, "size": orb_size,
                "break_dir": "NONE", "outcome": "NO_TRADE", "r_multiple": None,
                "entry_price": None, "stop_price": None, "target_price": None,
                "risk_ticks": None, "reward_ticks": None
            }

        # Buffer
        buffer = buffer_ticks * TICK_SIZE

        # 3. Find FIRST 1m close outside ORB (with buffer)
        break_dir = None
        trigger_idx = None

        for i, (ts_utc, o, h, l, c) in enumerate(scan_bars):
            if c > orb_high + buffer:
                break_dir = "UP"
                trigger_idx = i
                break
            elif c < orb_low - buffer:
                break_dir = "DOWN"
                trigger_idx = i
                break

        if break_dir is None:
            return {
                "high": orb_high, "low": orb_low, "size": orb_size,
                "break_dir": "NONE", "outcome": "NO_TRADE", "r_multiple": None,
                "entry_price": None, "stop_price": None, "target_price": None,
                "risk_ticks": None, "reward_ticks": None
            }

        # 4. Entry = NEXT bar OPEN (the bar immediately after confirmation)
        if trigger_idx + 1 >= len(scan_bars):
            # No next bar available
            return {
                "high": orb_high, "low": orb_low, "size": orb_size,
                "break_dir": break_dir, "outcome": "NO_TRADE", "r_multiple": None,
                "entry_price": None, "stop_price": None, "target_price": None,
                "risk_ticks": None, "reward_ticks": None
            }

        entry_bar = scan_bars[trigger_idx + 1]
        entry_ts, entry_open, _, _, _ = entry_bar
        entry_price = float(entry_open)

        # 5. Calculate stop based on mode
        if sl_mode == "full":
            stop_price = orb_low if break_dir == "UP" else orb_high
        else:  # half
            stop_price = orb_mid

        # 6. ENTRY-ANCHORED RISK (CRITICAL: This is Model B)
        risk = abs(entry_price - stop_price)
        risk_ticks = risk / TICK_SIZE

        # Guard: risk must be > 0
        if risk <= 0:
            return {
                "high": orb_high, "low": orb_low, "size": orb_size,
                "break_dir": break_dir, "outcome": "NO_TRADE", "r_multiple": None,
                "entry_price": entry_price, "stop_price": stop_price, "target_price": None,
                "risk_ticks": 0.0, "reward_ticks": None
            }

        # 7. ENTRY-ANCHORED TARGET (Model B)
        if break_dir == "UP":
            target_price = entry_price + rr * risk
        else:
            target_price = entry_price - rr * risk

        reward = abs(target_price - entry_price)
        reward_ticks = reward / TICK_SIZE

        # 8. Scan outcome from ENTRY BAR onwards (start checking in same bar as entry)
        outcome = "NO_TRADE"
        r_mult = None

        for ts_utc, o, h, l, c in scan_bars[trigger_idx + 1:]:
            h = float(h)
            l = float(l)

            if break_dir == "UP":
                hit_stop = l <= stop_price
                hit_target = h >= target_price

                # Conservative: same bar TP+SL = LOSS
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
            else:  # DOWN
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
            "break_dir": break_dir,
            "outcome": outcome,
            "r_multiple": r_mult,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "target_price": target_price,
            "risk_ticks": risk_ticks,
            "reward_ticks": reward_ticks
        }

    def build_features(self, trade_date: date, buffer_ticks: float = 0.0) -> bool:
        """Build features for a single day."""
        print(f"Building Model B features for {trade_date}...")

        # Calculate all 6 ORBs with Model B execution
        orb_0900 = self.calculate_orb_modelb(
            _dt_local(trade_date, 9, 0),
            _dt_local(trade_date, 17, 0),
            sl_mode=self.sl_mode,
            buffer_ticks=buffer_ticks,
            orb_minutes=5
        )

        orb_1000 = self.calculate_orb_modelb(
            _dt_local(trade_date, 10, 0),
            _dt_local(trade_date, 17, 0),
            sl_mode=self.sl_mode,
            buffer_ticks=buffer_ticks,
            orb_minutes=5
        )

        orb_1100 = self.calculate_orb_modelb(
            _dt_local(trade_date, 11, 0),
            _dt_local(trade_date, 17, 0),
            sl_mode=self.sl_mode,
            buffer_ticks=buffer_ticks,
            orb_minutes=5
        )

        orb_1800 = self.calculate_orb_modelb(
            _dt_local(trade_date, 18, 0),
            _dt_local(trade_date, 23, 0),
            sl_mode=self.sl_mode,
            buffer_ticks=buffer_ticks,
            orb_minutes=5
        )

        orb_2300 = self.calculate_orb_modelb(
            _dt_local(trade_date, 23, 0),
            _dt_local(trade_date + timedelta(days=1), 0, 30),
            sl_mode=self.sl_mode,
            buffer_ticks=buffer_ticks,
            orb_minutes=5
        )

        orb_0030 = self.calculate_orb_modelb(
            _dt_local(trade_date + timedelta(days=1), 0, 30),
            _dt_local(trade_date + timedelta(days=1), 2, 0),
            sl_mode=self.sl_mode,
            buffer_ticks=buffer_ticks,
            orb_minutes=5
        )

        # Insert into table
        self.con.execute(
            f"""
            INSERT OR REPLACE INTO {self.table_name} (
                date_local, instrument,

                orb_0900_high, orb_0900_low, orb_0900_size, orb_0900_break_dir, orb_0900_outcome, orb_0900_r_multiple,
                orb_0900_entry_price, orb_0900_stop_price, orb_0900_target_price, orb_0900_risk_ticks, orb_0900_reward_ticks,

                orb_1000_high, orb_1000_low, orb_1000_size, orb_1000_break_dir, orb_1000_outcome, orb_1000_r_multiple,
                orb_1000_entry_price, orb_1000_stop_price, orb_1000_target_price, orb_1000_risk_ticks, orb_1000_reward_ticks,

                orb_1100_high, orb_1100_low, orb_1100_size, orb_1100_break_dir, orb_1100_outcome, orb_1100_r_multiple,
                orb_1100_entry_price, orb_1100_stop_price, orb_1100_target_price, orb_1100_risk_ticks, orb_1100_reward_ticks,

                orb_1800_high, orb_1800_low, orb_1800_size, orb_1800_break_dir, orb_1800_outcome, orb_1800_r_multiple,
                orb_1800_entry_price, orb_1800_stop_price, orb_1800_target_price, orb_1800_risk_ticks, orb_1800_reward_ticks,

                orb_2300_high, orb_2300_low, orb_2300_size, orb_2300_break_dir, orb_2300_outcome, orb_2300_r_multiple,
                orb_2300_entry_price, orb_2300_stop_price, orb_2300_target_price, orb_2300_risk_ticks, orb_2300_reward_ticks,

                orb_0030_high, orb_0030_low, orb_0030_size, orb_0030_break_dir, orb_0030_outcome, orb_0030_r_multiple,
                orb_0030_entry_price, orb_0030_stop_price, orb_0030_target_price, orb_0030_risk_ticks, orb_0030_reward_ticks
            ) VALUES (
                ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            [
                trade_date, "MGC",

                orb_0900["high"] if orb_0900 else None,
                orb_0900["low"] if orb_0900 else None,
                orb_0900["size"] if orb_0900 else None,
                orb_0900["break_dir"] if orb_0900 else None,
                orb_0900["outcome"] if orb_0900 else None,
                orb_0900["r_multiple"] if orb_0900 else None,
                orb_0900.get("entry_price") if orb_0900 else None,
                orb_0900.get("stop_price") if orb_0900 else None,
                orb_0900.get("target_price") if orb_0900 else None,
                orb_0900.get("risk_ticks") if orb_0900 else None,
                orb_0900.get("reward_ticks") if orb_0900 else None,

                orb_1000["high"] if orb_1000 else None,
                orb_1000["low"] if orb_1000 else None,
                orb_1000["size"] if orb_1000 else None,
                orb_1000["break_dir"] if orb_1000 else None,
                orb_1000["outcome"] if orb_1000 else None,
                orb_1000["r_multiple"] if orb_1000 else None,
                orb_1000.get("entry_price") if orb_1000 else None,
                orb_1000.get("stop_price") if orb_1000 else None,
                orb_1000.get("target_price") if orb_1000 else None,
                orb_1000.get("risk_ticks") if orb_1000 else None,
                orb_1000.get("reward_ticks") if orb_1000 else None,

                orb_1100["high"] if orb_1100 else None,
                orb_1100["low"] if orb_1100 else None,
                orb_1100["size"] if orb_1100 else None,
                orb_1100["break_dir"] if orb_1100 else None,
                orb_1100["outcome"] if orb_1100 else None,
                orb_1100["r_multiple"] if orb_1100 else None,
                orb_1100.get("entry_price") if orb_1100 else None,
                orb_1100.get("stop_price") if orb_1100 else None,
                orb_1100.get("target_price") if orb_1100 else None,
                orb_1100.get("risk_ticks") if orb_1100 else None,
                orb_1100.get("reward_ticks") if orb_1100 else None,

                orb_1800["high"] if orb_1800 else None,
                orb_1800["low"] if orb_1800 else None,
                orb_1800["size"] if orb_1800 else None,
                orb_1800["break_dir"] if orb_1800 else None,
                orb_1800["outcome"] if orb_1800 else None,
                orb_1800["r_multiple"] if orb_1800 else None,
                orb_1800.get("entry_price") if orb_1800 else None,
                orb_1800.get("stop_price") if orb_1800 else None,
                orb_1800.get("target_price") if orb_1800 else None,
                orb_1800.get("risk_ticks") if orb_1800 else None,
                orb_1800.get("reward_ticks") if orb_1800 else None,

                orb_2300["high"] if orb_2300 else None,
                orb_2300["low"] if orb_2300 else None,
                orb_2300["size"] if orb_2300 else None,
                orb_2300["break_dir"] if orb_2300 else None,
                orb_2300["outcome"] if orb_2300 else None,
                orb_2300["r_multiple"] if orb_2300 else None,
                orb_2300.get("entry_price") if orb_2300 else None,
                orb_2300.get("stop_price") if orb_2300 else None,
                orb_2300.get("target_price") if orb_2300 else None,
                orb_2300.get("risk_ticks") if orb_2300 else None,
                orb_2300.get("reward_ticks") if orb_2300 else None,

                orb_0030["high"] if orb_0030 else None,
                orb_0030["low"] if orb_0030 else None,
                orb_0030["size"] if orb_0030 else None,
                orb_0030["break_dir"] if orb_0030 else None,
                orb_0030["outcome"] if orb_0030 else None,
                orb_0030["r_multiple"] if orb_0030 else None,
                orb_0030.get("entry_price") if orb_0030 else None,
                orb_0030.get("stop_price") if orb_0030 else None,
                orb_0030.get("target_price") if orb_0030 else None,
                orb_0030.get("risk_ticks") if orb_0030 else None,
                orb_0030.get("reward_ticks") if orb_0030 else None,
            ],
        )

        self.con.commit()
        print(f"  [OK] Model B features saved")
        return True

    def init_schema_v3(self):
        """Create table schema for Model B features."""
        self.con.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                date_local DATE NOT NULL,
                instrument VARCHAR NOT NULL,

                orb_0900_high DOUBLE,
                orb_0900_low DOUBLE,
                orb_0900_size DOUBLE,
                orb_0900_break_dir VARCHAR,
                orb_0900_outcome VARCHAR,
                orb_0900_r_multiple DOUBLE,
                orb_0900_entry_price DOUBLE,
                orb_0900_stop_price DOUBLE,
                orb_0900_target_price DOUBLE,
                orb_0900_risk_ticks DOUBLE,
                orb_0900_reward_ticks DOUBLE,

                orb_1000_high DOUBLE,
                orb_1000_low DOUBLE,
                orb_1000_size DOUBLE,
                orb_1000_break_dir VARCHAR,
                orb_1000_outcome VARCHAR,
                orb_1000_r_multiple DOUBLE,
                orb_1000_entry_price DOUBLE,
                orb_1000_stop_price DOUBLE,
                orb_1000_target_price DOUBLE,
                orb_1000_risk_ticks DOUBLE,
                orb_1000_reward_ticks DOUBLE,

                orb_1100_high DOUBLE,
                orb_1100_low DOUBLE,
                orb_1100_size DOUBLE,
                orb_1100_break_dir VARCHAR,
                orb_1100_outcome VARCHAR,
                orb_1100_r_multiple DOUBLE,
                orb_1100_entry_price DOUBLE,
                orb_1100_stop_price DOUBLE,
                orb_1100_target_price DOUBLE,
                orb_1100_risk_ticks DOUBLE,
                orb_1100_reward_ticks DOUBLE,

                orb_1800_high DOUBLE,
                orb_1800_low DOUBLE,
                orb_1800_size DOUBLE,
                orb_1800_break_dir VARCHAR,
                orb_1800_outcome VARCHAR,
                orb_1800_r_multiple DOUBLE,
                orb_1800_entry_price DOUBLE,
                orb_1800_stop_price DOUBLE,
                orb_1800_target_price DOUBLE,
                orb_1800_risk_ticks DOUBLE,
                orb_1800_reward_ticks DOUBLE,

                orb_2300_high DOUBLE,
                orb_2300_low DOUBLE,
                orb_2300_size DOUBLE,
                orb_2300_break_dir VARCHAR,
                orb_2300_outcome VARCHAR,
                orb_2300_r_multiple DOUBLE,
                orb_2300_entry_price DOUBLE,
                orb_2300_stop_price DOUBLE,
                orb_2300_target_price DOUBLE,
                orb_2300_risk_ticks DOUBLE,
                orb_2300_reward_ticks DOUBLE,

                orb_0030_high DOUBLE,
                orb_0030_low DOUBLE,
                orb_0030_size DOUBLE,
                orb_0030_break_dir VARCHAR,
                orb_0030_outcome VARCHAR,
                orb_0030_r_multiple DOUBLE,
                orb_0030_entry_price DOUBLE,
                orb_0030_stop_price DOUBLE,
                orb_0030_target_price DOUBLE,
                orb_0030_risk_ticks DOUBLE,
                orb_0030_reward_ticks DOUBLE,

                PRIMARY KEY (date_local, instrument)
            )
            """
        )
        self.con.commit()
        print(f"{self.table_name} table created (Model B, sl_mode={self.sl_mode})")

    def close(self):
        self.con.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build daily features with Model B execution")
    parser.add_argument("start_date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("end_date", type=str, nargs="?", default=None, help="End date (YYYY-MM-DD), optional")
    parser.add_argument("--sl-mode", type=str, choices=["full", "half"], default="full",
                        help="Stop loss mode: 'full' (opposite edge) or 'half' (midpoint)")
    parser.add_argument("--buffer-ticks", type=float, default=0.0,
                        help="Buffer ticks outside ORB for trigger (e.g., 0.5)")

    args = parser.parse_args()

    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date) if args.end_date else start_date
    sl_mode = args.sl_mode
    buffer_ticks = args.buffer_ticks

    # Model B: Use separate tables for full/half
    table_name = "daily_features_v3_modelb_half" if sl_mode == "half" else "daily_features_v3_modelb"

    print("="*80)
    print("BUILDING MODEL B FEATURES (Entry-Anchored, 5-min ORB, Next-Bar-Open)")
    print("="*80)
    print(f"Date range: {start_date} to {end_date}")
    print(f"SL mode: {sl_mode}")
    print(f"Buffer ticks: {buffer_ticks}")
    print(f"Target table: {table_name}")
    print()

    builder = FeatureBuilderV3(sl_mode=sl_mode, table_name=table_name)
    builder.init_schema_v3()

    cur = start_date
    count = 0
    while cur <= end_date:
        builder.build_features(cur, buffer_ticks=buffer_ticks)
        count += 1
        if count % 50 == 0:
            print(f"  [{count} days processed]")
        cur += timedelta(days=1)

    builder.close()
    print()
    print(f"COMPLETED: {start_date} to {end_date} ({count} days)")
    print(f"Table: {table_name}")


if __name__ == "__main__":
    main()
