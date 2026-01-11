# build_daily_features_v2.py
"""
Daily Feature Builder V2 - ZERO LOOKAHEAD (FIXED)
================================================
Rebuilds features with proper temporal structure.

CRITICAL:
- Each ORB can only use information available AT that exact time.
- The "trade_date" here is the ASIA date (local Australia/Brisbane):
    ASIA date D covers:
      PRE_ASIA     D 07:00–09:00
      ASIA         D 09:00–17:00  (ORBs 09:00/10:00/11:00)
      PRE_LONDON   D 17:00–18:00
      LONDON       D 18:00–23:00  (ORB 18:00)
      PRE_NY       D 23:00–(D+1)00:30
      NY_FUTURES   D 23:00–(D+1)00:30 (ORB 23:00)
      NYSE_ORB     (D+1)00:30–00:35 (ORB 00:30)
      NY_CASH      (D+1)00:35–02:00

Execution Model (1-minute):
- ORB = first 5 minutes of that open (range from bars_1m high/low)
- Entry trigger = first 1m CLOSE outside ORB after ORB window ends
- SL = opposite ORB boundary
- TP = entry +/- RR * risk (risk = abs(entry_close - SL))
- Outcome checked using subsequent 1m high/low (conservative: if both hit in same bar => LOSS)

Usage:
  python build_daily_features_v2.py 2026-01-10
  python build_daily_features_v2.py 2024-01-02 2026-01-10
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
RSI_LEN = 14

RR_DEFAULT = 1.0  # keep simple for now


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


class FeatureBuilderV2:
    def __init__(self, db_path: str = DB_PATH):
        self.con = duckdb.connect(db_path)

    # ---------- core time-window fetchers (FIX midnight safely) ----------
    def _window_stats_1m(self, start_local: datetime, end_local: datetime) -> Optional[Dict]:
        start_utc = start_local.astimezone(TZ_UTC)
        end_utc = end_local.astimezone(TZ_UTC)

        row = self.con.execute(
            """
            SELECT
              MAX(high) AS high,
              MIN(low)  AS low,
              MAX(high) - MIN(low) AS range,
              SUM(volume) AS volume
            FROM bars_1m
            WHERE symbol = ?
              AND ts_utc >= ? AND ts_utc < ?
            """,
            [SYMBOL, start_utc, end_utc],
        ).fetchone()

        if not row or row[0] is None:
            return None

        high, low, rng, vol = row
        return {
            "high": float(high),
            "low": float(low),
            "range": float(rng),
            "range_ticks": float(rng) / 0.1 if rng is not None else None,
            "volume": int(vol) if vol is not None else 0,
        }

    def _fetch_1m_bars(self, start_local: datetime, end_local: datetime) -> List[Tuple[datetime, float, float, float]]:
        start_utc = start_local.astimezone(TZ_UTC)
        end_utc = end_local.astimezone(TZ_UTC)

        return self.con.execute(
            """
            SELECT ts_utc, high, low, close
            FROM bars_1m
            WHERE symbol = ?
              AND ts_utc >= ? AND ts_utc < ?
            ORDER BY ts_utc
            """,
            [SYMBOL, start_utc, end_utc],
        ).fetchall()

    # ---------- blocks ----------
    def get_pre_asia(self, trade_date: date) -> Optional[Dict]:
        return self._window_stats_1m(_dt_local(trade_date, 7, 0), _dt_local(trade_date, 9, 0))

    def get_pre_london(self, trade_date: date) -> Optional[Dict]:
        return self._window_stats_1m(_dt_local(trade_date, 17, 0), _dt_local(trade_date, 18, 0))

    def get_pre_ny(self, trade_date: date) -> Optional[Dict]:
        # FIXED: D 23:00 -> (D+1) 00:30
        return self._window_stats_1m(_dt_local(trade_date, 23, 0), _dt_local(trade_date + timedelta(days=1), 0, 30))

    def get_asia_session(self, trade_date: date) -> Optional[Dict]:
        return self._window_stats_1m(_dt_local(trade_date, 9, 0), _dt_local(trade_date, 17, 0))

    def get_london_session(self, trade_date: date) -> Optional[Dict]:
        return self._window_stats_1m(_dt_local(trade_date, 18, 0), _dt_local(trade_date, 23, 0))

    def get_ny_cash_session(self, trade_date: date) -> Optional[Dict]:
        # (D+1) 00:35 -> 02:00
        return self._window_stats_1m(_dt_local(trade_date + timedelta(days=1), 0, 35),
                                     _dt_local(trade_date + timedelta(days=1), 2, 0))

    # ---------- ORB w/ 1m execution ----------
    def calculate_orb_1m_exec(self, orb_start_local: datetime, scan_end_local: datetime, rr: float = RR_DEFAULT) -> Optional[Dict]:
        orb_end_local = orb_start_local + timedelta(minutes=5)

        orb_stats = self._window_stats_1m(orb_start_local, orb_end_local)
        if not orb_stats:
            return None

        orb_high = orb_stats["high"]
        orb_low = orb_stats["low"]
        orb_size = orb_high - orb_low

        # bars AFTER orb end
        bars = self._fetch_1m_bars(orb_end_local, scan_end_local)

        break_dir = "NONE"
        entry_ts = None
        entry_price = None

        # entry = first 1m close outside ORB
        for ts_utc, h, l, c in bars:
            c = float(c)
            if c > orb_high:
                break_dir = "UP"
                entry_ts = ts_utc
                entry_price = c
                break
            if c < orb_low:
                break_dir = "DOWN"
                entry_ts = ts_utc
                entry_price = c
                break

        if break_dir == "NONE":
            return {"high": orb_high, "low": orb_low, "size": orb_size, "break_dir": "NONE", "outcome": "NO_TRADE", "r_multiple": None}

        stop = orb_low if break_dir == "UP" else orb_high
        risk = abs(entry_price - stop)
        if risk <= 0:
            return {"high": orb_high, "low": orb_low, "size": orb_size, "break_dir": break_dir, "outcome": "NO_TRADE", "r_multiple": None}

        target = entry_price + rr * risk if break_dir == "UP" else entry_price - rr * risk

        # start checking AFTER entry bar
        start_i = 0
        for i, (ts_utc, _, _, _) in enumerate(bars):
            if ts_utc == entry_ts:
                start_i = i + 1
                break

        for ts_utc, h, l, c in bars[start_i:]:
            h = float(h)
            l = float(l)

            if break_dir == "UP":
                hit_stop = l <= stop
                hit_target = h >= target
                if hit_stop and hit_target:
                    return {"high": orb_high, "low": orb_low, "size": orb_size, "break_dir": break_dir, "outcome": "LOSS", "r_multiple": -1.0}
                if hit_target:
                    return {"high": orb_high, "low": orb_low, "size": orb_size, "break_dir": break_dir, "outcome": "WIN", "r_multiple": float(rr)}
                if hit_stop:
                    return {"high": orb_high, "low": orb_low, "size": orb_size, "break_dir": break_dir, "outcome": "LOSS", "r_multiple": -1.0}
            else:
                hit_stop = h >= stop
                hit_target = l <= target
                if hit_stop and hit_target:
                    return {"high": orb_high, "low": orb_low, "size": orb_size, "break_dir": break_dir, "outcome": "LOSS", "r_multiple": -1.0}
                if hit_target:
                    return {"high": orb_high, "low": orb_low, "size": orb_size, "break_dir": break_dir, "outcome": "WIN", "r_multiple": float(rr)}
                if hit_stop:
                    return {"high": orb_high, "low": orb_low, "size": orb_size, "break_dir": break_dir, "outcome": "LOSS", "r_multiple": -1.0}

        return {"high": orb_high, "low": orb_low, "size": orb_size, "break_dir": break_dir, "outcome": "NO_TRADE", "r_multiple": None}

    # ---------- RSI ----------
    def calculate_rsi_at(self, at_local: datetime) -> Optional[float]:
        at_utc = at_local.astimezone(TZ_UTC)
        closes = self.con.execute(
            """
            SELECT close
            FROM bars_5m
            WHERE symbol = ?
              AND ts_utc <= ?
            ORDER BY ts_utc DESC
            LIMIT 15
            """,
            [SYMBOL, at_utc],
        ).fetchall()

        if len(closes) < 15:
            return None

        closes = [float(x[0]) for x in reversed(closes)]
        gains, losses = [], []
        for i in range(1, len(closes)):
            ch = closes[i] - closes[i - 1]
            gains.append(max(ch, 0.0))
            losses.append(max(-ch, 0.0))

        avg_gain = sum(gains[:RSI_LEN]) / RSI_LEN
        avg_loss = sum(losses[:RSI_LEN]) / RSI_LEN
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    # ---------- ATR (simple) ----------
    def calculate_atr(self, trade_date: date) -> Optional[float]:
        rows = self.con.execute(
            """
            SELECT asia_high, asia_low
            FROM daily_features_v2
            WHERE date_local < ?
              AND asia_high IS NOT NULL
            ORDER BY date_local DESC
            LIMIT 20
            """,
            [trade_date],
        ).fetchall()

        if len(rows) < 20:
            return None

        trs = [float(h) - float(l) for (h, l) in rows]
        return sum(trs) / len(trs)

    # ---------- deterministic type codes (level interactions only) ----------
    @staticmethod
    def classify_asia_code(asia_range: Optional[float], atr_20: Optional[float]) -> Optional[str]:
        if asia_range is None or atr_20 is None or atr_20 == 0:
            return None
        ratio = asia_range / atr_20
        if ratio < 0.3:
            return "A1_TIGHT"
        if ratio > 0.8:
            return "A2_EXPANDED"
        return "A0_NORMAL"

    @staticmethod
    def classify_london_code(london_high: Optional[float], london_low: Optional[float],
                             asia_high: Optional[float], asia_low: Optional[float]) -> Optional[str]:
        if None in (london_high, london_low, asia_high, asia_low):
            return None
        took_high = london_high > asia_high
        took_low = london_low < asia_low
        if took_high and took_low:
            return "L3_EXPANSION"
        if took_high:
            return "L1_SWEEP_HIGH"
        if took_low:
            return "L2_SWEEP_LOW"
        return "L4_CONSOLIDATION"

    @staticmethod
    def classify_pre_ny_code(pre_ny_high: Optional[float], pre_ny_low: Optional[float],
                             london_high: Optional[float], london_low: Optional[float],
                             asia_high: Optional[float], asia_low: Optional[float],
                             atr_20: Optional[float]) -> Optional[str]:
        if None in (pre_ny_high, pre_ny_low, london_high, london_low, asia_high, asia_low):
            return None
        ref_high = max(london_high, asia_high)
        ref_low = min(london_low, asia_low)

        if pre_ny_high > ref_high and pre_ny_low >= ref_low:
            return "N1_SWEEP_HIGH"
        if pre_ny_low < ref_low and pre_ny_high <= ref_high:
            return "N2_SWEEP_LOW"

        if atr_20 and atr_20 > 0:
            rng = pre_ny_high - pre_ny_low
            ratio = rng / atr_20
            if ratio < 0.25:
                return "N3_CONSOLIDATION"
            if ratio > 0.8:
                return "N4_EXPANSION"

        return "N0_NORMAL"

    # ---------- build ----------
    def build_features(self, trade_date: date) -> bool:
        print(f"Building features for {trade_date}...")

        pre_asia = self.get_pre_asia(trade_date)
        pre_london = self.get_pre_london(trade_date)
        pre_ny = self.get_pre_ny(trade_date)

        asia_session = self.get_asia_session(trade_date)
        london_session = self.get_london_session(trade_date)
        ny_session = self.get_ny_cash_session(trade_date)

        orb_0900 = self.calculate_orb_1m_exec(_dt_local(trade_date, 9, 0), _dt_local(trade_date, 17, 0))
        orb_1000 = self.calculate_orb_1m_exec(_dt_local(trade_date, 10, 0), _dt_local(trade_date, 17, 0))
        orb_1100 = self.calculate_orb_1m_exec(_dt_local(trade_date, 11, 0), _dt_local(trade_date, 17, 0))
        orb_1800 = self.calculate_orb_1m_exec(_dt_local(trade_date, 18, 0), _dt_local(trade_date, 23, 0))
        orb_2300 = self.calculate_orb_1m_exec(_dt_local(trade_date, 23, 0), _dt_local(trade_date + timedelta(days=1), 0, 30))
        orb_0030 = self.calculate_orb_1m_exec(_dt_local(trade_date + timedelta(days=1), 0, 30), _dt_local(trade_date + timedelta(days=1), 2, 0))

        rsi_at_0030 = self.calculate_rsi_at(_dt_local(trade_date + timedelta(days=1), 0, 30))
        atr_20 = self.calculate_atr(trade_date)

        asia_code = self.classify_asia_code(asia_session["range"] if asia_session else None, atr_20)
        london_code = self.classify_london_code(
            london_session["high"] if london_session else None,
            london_session["low"] if london_session else None,
            asia_session["high"] if asia_session else None,
            asia_session["low"] if asia_session else None,
        )
        pre_ny_code = self.classify_pre_ny_code(
            pre_ny["high"] if pre_ny else None,
            pre_ny["low"] if pre_ny else None,
            london_session["high"] if london_session else None,
            london_session["low"] if london_session else None,
            asia_session["high"] if asia_session else None,
            asia_session["low"] if asia_session else None,
            atr_20,
        )

        self.con.execute(
            """
            INSERT OR REPLACE INTO daily_features_v2 (
                date_local, instrument,

                pre_asia_high, pre_asia_low, pre_asia_range,
                pre_london_high, pre_london_low, pre_london_range,
                pre_ny_high, pre_ny_low, pre_ny_range,

                asia_high, asia_low, asia_range,
                london_high, london_low, london_range,
                ny_high, ny_low, ny_range,
                asia_type_code, london_type_code, pre_ny_type_code,

                orb_0900_high, orb_0900_low, orb_0900_size, orb_0900_break_dir, orb_0900_outcome, orb_0900_r_multiple,
                orb_1000_high, orb_1000_low, orb_1000_size, orb_1000_break_dir, orb_1000_outcome, orb_1000_r_multiple,
                orb_1100_high, orb_1100_low, orb_1100_size, orb_1100_break_dir, orb_1100_outcome, orb_1100_r_multiple,
                orb_1800_high, orb_1800_low, orb_1800_size, orb_1800_break_dir, orb_1800_outcome, orb_1800_r_multiple,
                orb_2300_high, orb_2300_low, orb_2300_size, orb_2300_break_dir, orb_2300_outcome, orb_2300_r_multiple,
                orb_0030_high, orb_0030_low, orb_0030_size, orb_0030_break_dir, orb_0030_outcome, orb_0030_r_multiple,

                rsi_at_0030, atr_20
            ) VALUES (
                ?, ?,

                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,

                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,

                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,

                ?, ?
            )
            """,
            [
                trade_date, "MGC",

                pre_asia["high"] if pre_asia else None,
                pre_asia["low"] if pre_asia else None,
                pre_asia["range"] if pre_asia else None,

                pre_london["high"] if pre_london else None,
                pre_london["low"] if pre_london else None,
                pre_london["range"] if pre_london else None,

                pre_ny["high"] if pre_ny else None,
                pre_ny["low"] if pre_ny else None,
                pre_ny["range"] if pre_ny else None,

                asia_session["high"] if asia_session else None,
                asia_session["low"] if asia_session else None,
                asia_session["range"] if asia_session else None,

                london_session["high"] if london_session else None,
                london_session["low"] if london_session else None,
                london_session["range"] if london_session else None,

                ny_session["high"] if ny_session else None,
                ny_session["low"] if ny_session else None,
                ny_session["range"] if ny_session else None,

                asia_code, london_code, pre_ny_code,

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

                rsi_at_0030,
                atr_20,
            ],
        )

        self.con.commit()
        print("  [OK] Features saved")
        return True

    def init_schema_v2(self):
        self.con.execute(
            """
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
            )
            """
        )
        self.con.commit()
        print("daily_features_v2 table created")

    def close(self):
        self.con.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python build_daily_features_v2.py YYYY-MM-DD [YYYY-MM-DD]")
        return

    start_date = date.fromisoformat(sys.argv[1])
    end_date = date.fromisoformat(sys.argv[2]) if len(sys.argv) == 3 else start_date

    builder = FeatureBuilderV2()
    builder.init_schema_v2()

    cur = start_date
    while cur <= end_date:
        builder.build_features(cur)
        cur += timedelta(days=1)

    builder.close()
    print(f"\nCompleted: {start_date} to {end_date}")


if __name__ == "__main__":
    main()
