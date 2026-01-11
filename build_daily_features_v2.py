"""
Daily Feature Builder V2 - ZERO LOOKAHEAD
==========================================
Rebuilds features with proper temporal structure.

CRITICAL: Each ORB can only use information available AT that exact time.

Session Structure:
------------------
PRE_ASIA (07:00-09:00)       -> Context for ASIA ORBs
ASIA (09:00-17:00)           -> ORBs: 09:00, 10:00, 11:00
PRE_LONDON (17:00-18:00)     -> Context for LONDON ORB
LONDON (18:00-23:00)         -> ORB: 18:00
PRE_NY (23:00-00:30)         -> Context for NYSE ORB
NY FUTURES (23:00+)          -> ORB: 23:00
NYSE (00:30-02:00)           -> ORB: 00:30

What each ORB can see:
----------------------
09:00 ORB: PRE_ASIA (07:00-09:00), previous day, overnight gap
10:00 ORB: PRE_ASIA + ASIA_SO_FAR (09:00-10:00)
11:00 ORB: PRE_ASIA + ASIA_SO_FAR (09:00-11:00)
18:00 ORB: PRE_LONDON (17:00-18:00), completed ASIA (09:00-17:00)
23:00 ORB: Completed LONDON (18:00-23:00), completed ASIA
00:30 ORB: PRE_NY (23:00-00:30), completed LONDON, completed ASIA

Usage:
------
python build_daily_features_v2.py 2026-01-10
python build_daily_features_v2.py 2026-01-01 2026-01-10  # Range
"""

import duckdb
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Tuple, Dict


TZ_LOCAL = ZoneInfo("Australia/Brisbane")
SYMBOL = "MGC"
DB_PATH = "gold.db"
RSI_LEN = 14


class FeatureBuilderV2:
    """Zero-lookahead feature builder"""

    def __init__(self, db_path: str = DB_PATH):
        self.con = duckdb.connect(db_path)

    def get_range_stats(self, start_hour: int, start_min: int,
                       end_hour: int, end_min: int,
                       trade_date: date) -> Optional[Dict]:
        """Get high/low/range for a time window (in local time)"""

        query = """
            SELECT
                MAX(high) as high,
                MIN(low) as low,
                MAX(high) - MIN(low) as range,
                SUM(volume) as volume
            FROM bars_1m
            WHERE symbol = ?
              AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') = ?
              AND (
                (EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') = ?
                 AND EXTRACT(MINUTE FROM ts_utc AT TIME ZONE 'Australia/Brisbane') >= ?)
                OR
                (EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') > ?
                 AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < ?)
                OR
                (EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') = ?
                 AND EXTRACT(MINUTE FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < ?)
              )
        """

        result = self.con.execute(query, [
            SYMBOL, trade_date,
            start_hour, start_min,
            start_hour, end_hour,
            end_hour, end_min
        ]).fetchone()

        if not result or result[0] is None:
            return None

        high, low, range_val, volume = result

        return {
            "high": high,
            "low": low,
            "range": range_val,
            "range_ticks": range_val / 0.1 if range_val else None,
            "volume": volume,
        }

    def calculate_orb(self, orb_hour: int, orb_min: int, trade_date: date) -> Optional[Dict]:
        """Calculate ORB (5-minute window) and outcome"""

        # Get ORB high/low (5 minutes)
        orb_stats = self.get_range_stats(orb_hour, orb_min, orb_hour, orb_min + 5, trade_date)
        if not orb_stats:
            return None

        orb_high = orb_stats["high"]
        orb_low = orb_stats["low"]
        orb_size = orb_stats["range"]

        # Determine break direction (using rest of day)
        # For 00:30, only use until 02:00
        if orb_hour == 0 and orb_min == 30:
            end_hour = 2
            end_min = 0
        else:
            # Use rest of day (up to 09:00 next day boundary)
            # Simplified: use until end of current trading day
            end_hour = 23
            end_min = 59

        break_query = """
            SELECT close
            FROM bars_5m
            WHERE symbol = ?
              AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') = ?
              AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') * 60
                  + EXTRACT(MINUTE FROM ts_utc AT TIME ZONE 'Australia/Brisbane')
                  > ? * 60 + ? + 5
            ORDER BY ts_utc
        """

        bars = self.con.execute(break_query, [
            SYMBOL, trade_date, orb_hour, orb_min
        ]).fetchall()
e": "LOSS", "r_multiple": -1.0}
                if l <= target:
                    return {"high": orb_high, "low": orb_low, "size": (orb_high - orb_low),
                            "break_dir": break_dir, "outcome": "WIN", "r_multiple": float(rr)}

        # If neither hit by scan end
        return {"high": orb_high, "low": orb_low, "size": (orb_high - orb_low),
                "break_dir": break_dir, "outcome": "NO_TRADE", "r_multiple": None}

    def calculate_rsi(self, trade_date: date, at_hour: int, at_min: int) -> Optional[float]:
        """Calculate RSI at specific time using 14 periods of 5-min bars"""

        # Get 15 bars before this time (14 + 1 for calculation)
        query = """
            SELECT close
            FROM bars_5m
            WHERE symbol = ?
              AND ts_utc <= (
                SELECT ts_utc
                FROM bars_5m
                WHERE symbol = ?
                  AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') = ?
                  AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') = ?
                  AND EXTRACT(MINUTE FROM ts_utc AT TIME ZONE 'Australia/Brisbane') = ?
                ORDER BY ts_utc LIMIT 1
              )
            ORDER BY ts_utc DESC
            LIMIT 15
        """

        closes = self.con.execute(query, [
            SYMBOL, SYMBOL, trade_date, at_hour, at_min
        ]).fetchall()

        if len(closes) < 15:
            return None

        closes = [c[0] for c in reversed(closes)]

        # Calculate RSI (Wilder's method)
        gains = []
        losses = []

        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        if not gains:
            return None

        avg_gain = sum(gains[:RSI_LEN]) / RSI_LEN
        avg_loss = sum(losses[:RSI_LEN]) / RSI_LEN

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def build_features(self, trade_date: date) -> bool:
        """Build all features for a trading day"""

        print(f"Building features for {trade_date}...")

        # PRE blocks (context available AT the open)
        pre_asia = self.get_range_stats(7, 0, 9, 0, trade_date)  # 07:00-09:00
        pre_london = self.get_range_stats(17, 0, 18, 0, trade_date)  # 17:00-18:00
        pre_ny = self.get_range_stats(23, 0, 0, 30, trade_date)  # 23:00-00:30 (next day)

        # SESSION blocks (for analytics, NOT for real-time trading decisions)
        asia_session = self.get_range_stats(9, 0, 17, 0, trade_date)  # 09:00-17:00
        london_session = self.get_range_stats(18, 0, 23, 0, trade_date)  # 18:00-23:00
        ny_session = self.get_range_stats(0, 35, 2, 0, trade_date)  # 00:35-02:00

        # ORBs
        orb_0900 = self.calculate_orb(9, 0, trade_date)
        orb_1000 = self.calculate_orb(10, 0, trade_date)
        orb_1100 = self.calculate_orb(11, 0, trade_date)
        orb_1800 = self.calculate_orb(18, 0, trade_date)
        orb_2300 = self.calculate_orb(23, 0, trade_date)
        orb_0030 = self.calculate_orb(0, 30, trade_date)

        # RSI at 00:30
        rsi_at_0030 = self.calculate_rsi(trade_date, 0, 30)

        # ATR (using previous 20 days)
        atr_20 = self.calculate_atr(trade_date)

        # Insert features
        self.con.execute("""
            INSERT OR REPLACE INTO daily_features_v2 (
                date_local, instrument,
                -- PRE blocks (available AT the open)
                pre_asia_high, pre_asia_low, pre_asia_range,
                pre_london_high, pre_london_low, pre_london_range,
                pre_ny_high, pre_ny_low, pre_ny_range,
                -- SESSION blocks (analytics only, known AFTER close)
                asia_high, asia_low, asia_range,
                london_high, london_low, london_range,
                ny_high, ny_low, ny_range,
                -- ORBs
                orb_0900_high, orb_0900_low, orb_0900_size, orb_0900_break_dir, orb_0900_outcome, orb_0900_r_multiple,
                orb_1000_high, orb_1000_low, orb_1000_size, orb_1000_break_dir, orb_1000_outcome, orb_1000_r_multiple,
                orb_1100_high, orb_1100_low, orb_1100_size, orb_1100_break_dir, orb_1100_outcome, orb_1100_r_multiple,
                orb_1800_high, orb_1800_low, orb_1800_size, orb_1800_break_dir, orb_1800_outcome, orb_1800_r_multiple,
                orb_2300_high, orb_2300_low, orb_2300_size, orb_2300_break_dir, orb_2300_outcome, orb_2300_r_multiple,
                orb_0030_high, orb_0030_low, orb_0030_size, orb_0030_break_dir, orb_0030_outcome, orb_0030_r_multiple,
                -- Indicators
                rsi_at_0030, atr_20
            ) VALUES (
                ?, ?,
                -- PRE blocks
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                -- SESSION blocks
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                -- ORBs
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                -- Indicators
                ?, ?
            )
        """, [
            trade_date, "MGC",
            # PRE blocks
            pre_asia["high"] if pre_asia else None,
            pre_asia["low"] if pre_asia else None,
            pre_asia["range"] if pre_asia else None,
            pre_london["high"] if pre_london else None,
            pre_london["low"] if pre_london else None,
            pre_london["range"] if pre_london else None,
            pre_ny["high"] if pre_ny else None,
            pre_ny["low"] if pre_ny else None,
            pre_ny["range"] if pre_ny else None,
            # SESSION blocks
            asia_session["high"] if asia_session else None,
            asia_session["low"] if asia_session else None,
            asia_session["range"] if asia_session else None,
            london_session["high"] if london_session else None,
            london_session["low"] if london_session else None,
            london_session["range"] if london_session else None,
            ny_session["high"] if ny_session else None,
            ny_session["low"] if ny_session else None,
            ny_session["range"] if ny_session else None,
            # ORBs
            orb_0900["high"] if orb_0900 else None,
            orb_0900["low"] if orb_0900 else None,
            orb_0900["size"] if orb_0900 else None,
            orb_0900["break_dir"] if orb_0900 else None,
            orb_0900["outcome"] if orb_0900 else None,
            orb_0900["r_multiple"] if orb_0900 else None,

            orb_1000["high"] if orb_1000 else None,
            orb_1000["low"] if orb_1000 else None,
            orb_1000["size"] if orb_1000 else None,
            orb_1000["break_dir"] if orb_1000 else None,
            orb_1000["outcome"] if orb_1000 else None,
            orb_1000["r_multiple"] if orb_1000 else None,

            orb_1100["high"] if orb_1100 else None,
            orb_1100["low"] if orb_1100 else None,
            orb_1100["size"] if orb_1100 else None,
            orb_1100["break_dir"] if orb_1100 else None,
            orb_1100["outcome"] if orb_1100 else None,
            orb_1100["r_multiple"] if orb_1100 else None,

            orb_1800["high"] if orb_1800 else None,
            orb_1800["low"] if orb_1800 else None,
            orb_1800["size"] if orb_1800 else None,
            orb_1800["break_dir"] if orb_1800 else None,
            orb_1800["outcome"] if orb_1800 else None,
            orb_1800["r_multiple"] if orb_1800 else None,

            orb_2300["high"] if orb_2300 else None,
            orb_2300["low"] if orb_2300 else None,
            orb_2300["size"] if orb_2300 else None,
            orb_2300["break_dir"] if orb_2300 else None,
            orb_2300["outcome"] if orb_2300 else None,
            orb_2300["r_multiple"] if orb_2300 else None,

            orb_0030["high"] if orb_0030 else None,
            orb_0030["low"] if orb_0030 else None,
            orb_0030["size"] if orb_0030 else None,
            orb_0030["break_dir"] if orb_0030 else None,
            orb_0030["outcome"] if orb_0030 else None,
            orb_0030["r_multiple"] if orb_0030 else None,

            # Indicators
            rsi_at_0030,
            atr_20,
        ])

        self.con.commit()
        print(f"  [OK] Features saved")
        return True

    def calculate_atr(self, trade_date: date) -> Optional[float]:
        """Calculate 20-period ATR using previous days"""

        query = """
            SELECT asia_high, asia_low
            FROM daily_features
            WHERE date_local < ?
              AND asia_high IS NOT NULL
            ORDER BY date_local DESC
            LIMIT 20
        """

        rows = self.con.execute(query, [trade_date]).fetchall()

        if len(rows) < 20:
            return None

        true_ranges = []
        for high, low in rows:
            tr = high - low
            true_ranges.append(tr)

        atr = sum(true_ranges) / len(true_ranges)
        return atr

    def init_schema_v2(self):
        """Create daily_features_v2 table"""

        self.con.execute("""
            CREATE TABLE IF NOT EXISTS daily_features_v2 (
                date_local DATE NOT NULL,
                instrument VARCHAR NOT NULL,

                -- PRE blocks (known AT the open - zero lookahead)
                pre_asia_high DOUBLE,
                pre_asia_low DOUBLE,
                pre_asia_range DOUBLE,
                pre_london_high DOUBLE,
                pre_london_low DOUBLE,
                pre_london_range DOUBLE,
                pre_ny_high DOUBLE,
                pre_ny_low DOUBLE,
                pre_ny_range DOUBLE,

                -- SESSION blocks (analytics only - known AFTER close)
                asia_high DOUBLE,
                asia_low DOUBLE,
                asia_range DOUBLE,
                london_high DOUBLE,
                london_low DOUBLE,
                london_range DOUBLE,
                ny_high DOUBLE,
                ny_low DOUBLE,
                ny_range DOUBLE,

                -- ORBs
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

                -- Indicators
                rsi_at_0030 DOUBLE,
                atr_20 DOUBLE,

                PRIMARY KEY (date_local, instrument)
            )
        """)

        self.con.commit()
        print("daily_features_v2 table created")

    def close(self):
        self.con.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python build_daily_features_v2.py YYYY-MM-DD [YYYY-MM-DD]")
        return

    start_date = date.fromisoformat(sys.argv[1])

    if len(sys.argv) == 3:
        end_date = date.fromisoformat(sys.argv[2])
    else:
        end_date = start_date

    builder = FeatureBuilderV2()

    # Init schema
    builder.init_schema_v2()

    # Build features
    current = start_date
    while current <= end_date:
        builder.build_features(current)
        current += timedelta(days=1)

    builder.close()

    print(f"\nCompleted: {start_date} to {end_date}")


if __name__ == "__main__":
    main()
