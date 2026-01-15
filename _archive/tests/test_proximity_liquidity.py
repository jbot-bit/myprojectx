"""
PROXIMITY LIQUIDITY TEST - Middle Layer Discovery

Tests whether proximity of session levels (Asia/London high/low) creates
a tradeable liquidity-reaction edge between ORBs and Cascades.

Structure (EXACT, no optimization):
1. Proximity: Two session levels close (≤5pts OR ≤0.3*ATR_20)
2. Compression: Price trades between levels
3. Trigger: Sweep both levels (or sweep one + tag other within 5min)
4. Failure: Close back inside within 3 bars
5. Entry: Retest of proximity zone
6. Stop: Beyond furthest extreme
7. Exit: Structure trail OR session end

NO grid search. NO optimization. ONE test.
"""

import duckdb
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

DB_PATH = "gold.db"
SYMBOL = "MGC"
TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")

# Single threshold test (not optimized)
PROXIMITY_POINTS = 5.0  # Fixed: levels within 5 points
PROXIMITY_ATR_MULT = 0.3  # Fixed: OR within 0.3 * ATR_20
TAG_WINDOW_MIN = 5  # Minutes to tag second level after first sweep
FAILURE_BARS = 3  # Bars to check for failure
ENTRY_TOLERANCE = 0.1  # Entry within 0.1pts of zone


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


class ProximityLiquidityTest:
    def __init__(self):
        self.con = duckdb.connect(DB_PATH, read_only=True)

    def get_session_levels(self, trade_date: date) -> dict | None:
        """Get session levels + ATR from daily_features."""
        result = self.con.execute("""
            SELECT asia_high, asia_low, london_high, london_low, atr_20
            FROM daily_features
            WHERE date_local = ? AND instrument = ?
        """, [trade_date, SYMBOL]).fetchone()

        if not result or any(x is None for x in result):
            return None

        return {
            "asia_high": float(result[0]),
            "asia_low": float(result[1]),
            "london_high": float(result[2]),
            "london_low": float(result[3]),
            "atr_20": float(result[4]) if result[4] else None,
        }

    def get_bars(self, start_local: datetime, end_local: datetime):
        start_utc = start_local.astimezone(TZ_UTC)
        end_utc = end_local.astimezone(TZ_UTC)
        return self.con.execute("""
            SELECT ts_utc, open, high, low, close FROM bars_1m
            WHERE symbol = ? AND ts_utc >= ? AND ts_utc < ?
            ORDER BY ts_utc
        """, [SYMBOL, start_utc, end_utc]).fetchall()

    def find_proximity_pairs(self, levels: dict) -> list:
        """Find all pairs of session levels that are proximate."""
        pairs = []

        # Define all possible pairs
        candidates = [
            ("asia_high", "london_high"),
            ("asia_low", "london_low"),
            ("asia_high", "asia_low"),  # Asia range compression
            ("london_high", "london_low"),  # London range compression
        ]

        atr_threshold = levels["atr_20"] * PROXIMITY_ATR_MULT if levels["atr_20"] else None

        for level1_name, level2_name in candidates:
            level1 = levels[level1_name]
            level2 = levels[level2_name]
            distance = abs(level1 - level2)

            # Check proximity (points OR ATR)
            is_proximate = (distance <= PROXIMITY_POINTS)
            if atr_threshold and not is_proximate:
                is_proximate = (distance <= atr_threshold)

            if is_proximate and distance > 0:  # Avoid identical levels
                pairs.append({
                    "level1_name": level1_name,
                    "level2_name": level2_name,
                    "level1": level1,
                    "level2": level2,
                    "distance": distance,
                    "zone_high": max(level1, level2),
                    "zone_low": min(level1, level2),
                })

        return pairs

    def test_proximity_setup(self, trade_date: date, pair: dict) -> dict | None:
        """Test a single proximity pair for setup."""
        zone_high = pair["zone_high"]
        zone_low = pair["zone_low"]

        # Scan window: 23:00 onwards (NY session)
        scan_start = _dt_local(trade_date, 23, 0)
        scan_end = _dt_local(trade_date + timedelta(days=1), 2, 0)
        bars = self.get_bars(scan_start, scan_end)

        if not bars:
            return None

        # Find sweep of both levels
        swept_high = False
        swept_low = False
        sweep_high_idx = None
        sweep_low_idx = None
        furthest_high = zone_high
        furthest_low = zone_low

        for i, (ts_utc, o, h, l, c) in enumerate(bars):
            h, l = float(h), float(l)

            if h > zone_high and not swept_high:
                swept_high = True
                sweep_high_idx = i
                furthest_high = max(furthest_high, h)

            if l < zone_low and not swept_low:
                swept_low = True
                sweep_low_idx = i
                furthest_low = min(furthest_low, l)

            # Track furthest extremes
            if swept_high:
                furthest_high = max(furthest_high, h)
            if swept_low:
                furthest_low = min(furthest_low, l)

            # Check if both swept (within TAG_WINDOW_MIN)
            if swept_high and swept_low:
                time_diff = abs(sweep_high_idx - sweep_low_idx)
                if time_diff <= TAG_WINDOW_MIN:
                    # Both levels swept, check for failure
                    last_sweep_idx = max(sweep_high_idx, sweep_low_idx)

                    # Check next FAILURE_BARS for close back inside zone
                    for j in range(last_sweep_idx + 1, min(last_sweep_idx + FAILURE_BARS + 1, len(bars))):
                        close_j = float(bars[j][4])

                        if zone_low < close_j < zone_high:
                            # Failure! Price closed back inside
                            # Look for entry on retest
                            for k in range(j, len(bars)):
                                bar_h, bar_l = float(bars[k][2]), float(bars[k][3])

                                # Entry: retest zone (high or low edge)
                                entry_at_high = abs(bar_l - zone_high) <= ENTRY_TOLERANCE
                                entry_at_low = abs(bar_h - zone_low) <= ENTRY_TOLERANCE

                                if entry_at_high or entry_at_low:
                                    # Determine direction
                                    if furthest_high - zone_high > zone_low - furthest_low:
                                        # Swept more upside, enter SHORT
                                        direction = "SHORT"
                                        entry_price = zone_high
                                        stop_price = furthest_high
                                    else:
                                        # Swept more downside, enter LONG
                                        direction = "LONG"
                                        entry_price = zone_low
                                        stop_price = furthest_low

                                    risk = abs(entry_price - stop_price)
                                    if risk <= 0:
                                        continue

                                    # Scan for outcome (simple: stop or session end)
                                    outcome = None
                                    exit_price = None

                                    for m in range(k, len(bars)):
                                        bar_h, bar_l, bar_c = [float(x) for x in bars[m][2:5]]

                                        if direction == "SHORT":
                                            if bar_h >= stop_price:
                                                outcome = "LOSS"
                                                exit_price = stop_price
                                                break
                                        else:  # LONG
                                            if bar_l <= stop_price:
                                                outcome = "LOSS"
                                                exit_price = stop_price
                                                break

                                    if outcome is None:
                                        outcome = "TIME_EXIT"
                                        exit_price = float(bars[-1][4])

                                    if direction == "SHORT":
                                        r_mult = (entry_price - exit_price) / risk
                                    else:
                                        r_mult = (exit_price - entry_price) / risk

                                    return {
                                        "date": trade_date,
                                        "pair": f"{pair['level1_name']}/{pair['level2_name']}",
                                        "distance": pair["distance"],
                                        "direction": direction,
                                        "zone_high": zone_high,
                                        "zone_low": zone_low,
                                        "furthest_high": furthest_high,
                                        "furthest_low": furthest_low,
                                        "entry_price": entry_price,
                                        "stop_price": stop_price,
                                        "risk": risk,
                                        "outcome": outcome,
                                        "r_multiple": r_mult,
                                    }

        return None

    def test_single_day(self, trade_date: date) -> dict | None:
        """Test all proximity pairs for a single day."""
        levels = self.get_session_levels(trade_date)
        if not levels:
            return None

        pairs = self.find_proximity_pairs(levels)
        if not pairs:
            return None

        # Test each pair (return first valid setup)
        for pair in pairs:
            result = self.test_proximity_setup(trade_date, pair)
            if result:
                return result

        return None

    def run_test(self, start_date: date, end_date: date):
        print("="*80)
        print("PROXIMITY LIQUIDITY TEST - Middle Layer Discovery")
        print("="*80)
        print()
        print("Structure:")
        print("  1. Proximity: Levels within 5pts OR 0.3*ATR_20")
        print("  2. Compression: Price between levels")
        print("  3. Sweep both levels (within 5 minutes)")
        print("  4. Failure: Close back inside within 3 bars")
        print("  5. Entry: Retest of zone")
        print("  6. Stop: Beyond furthest extreme")
        print("  7. Exit: Stop or session end")
        print()
        print("-"*80)
        print()

        trades = []
        cur = start_date

        while cur <= end_date:
            result = self.test_single_day(cur)
            if result:
                trades.append(result)
            cur += timedelta(days=1)

        total_days = (end_date - start_date).days + 1
        frequency = len(trades) / total_days * 100

        print(f"Total setups: {len(trades)}")
        print(f"Frequency: {frequency:.1f}% of days ({len(trades)}/{total_days})")
        print()

        if not trades:
            print("No setups found")
            return

        # Calculate metrics
        avg_r = sum(t["r_multiple"] for t in trades) / len(trades)
        sorted_r = sorted(t["r_multiple"] for t in trades)
        median_r = sorted_r[len(sorted_r)//2]
        max_r = max(t["r_multiple"] for t in trades)
        min_r = min(t["r_multiple"] for t in trades)

        wins = [t for t in trades if t["r_multiple"] > 0]
        win_rate = len(wins) / len(trades) * 100 if trades else 0

        print("="*80)
        print("RESULTS")
        print("="*80)
        print()
        print(f"Average R:   {avg_r:+.2f}R")
        print(f"Median R:    {median_r:+.2f}R")
        print(f"Max R:       {max_r:+.2f}R")
        print(f"Min R:       {min_r:+.2f}R")
        print(f"Win rate:    {win_rate:.1f}%")
        print()

        # Direction breakdown
        shorts = [t for t in trades if t["direction"] == "SHORT"]
        longs = [t for t in trades if t["direction"] == "LONG"]

        if shorts:
            avg_r_short = sum(t["r_multiple"] for t in shorts) / len(shorts)
            print(f"SHORT: {len(shorts)} trades, {avg_r_short:+.2f}R avg")

        if longs:
            avg_r_long = sum(t["r_multiple"] for t in longs) / len(longs)
            print(f"LONG: {len(longs)} trades, {avg_r_long:+.2f}R avg")

        print()

        # Pair analysis
        print("Most common pairs:")
        pair_counts = {}
        for t in trades:
            pair = t["pair"]
            pair_counts[pair] = pair_counts.get(pair, 0) + 1

        for pair, count in sorted(pair_counts.items(), key=lambda x: -x[1])[:5]:
            pair_trades = [t for t in trades if t["pair"] == pair]
            pair_avg = sum(t["r_multiple"] for t in pair_trades) / len(pair_trades)
            print(f"  {pair}: {count} trades ({count/len(trades)*100:.0f}%), {pair_avg:+.2f}R avg")

        print()
        print("="*80)
        print("COMPARISON TO OTHER STRATEGIES")
        print("="*80)
        print()
        print("Proximity Liquidity: {:.1f}% freq, {:+.2f}R avg, {:.1f}% WR".format(
            frequency, avg_r, win_rate))
        print()
        print("VS Existing Strategies:")
        print("  Cascades:         9.3% freq, +1.95R avg, 19-27% WR (PRIMARY)")
        print("  Single Liquidity: 16% freq,  +1.44R avg, 33.7% WR (BACKUP)")
        print("  00:30 ORB:        56% freq,  +1.54R avg, 50.8% WR (SECONDARY)")
        print("  23:00 ORB:        63% freq,  +1.08R avg, 41.5% WR (SECONDARY)")
        print("  Day ORBs:         64-66% freq, +0.27-0.39R avg (TERTIARY)")
        print()

        # Verdict
        print("="*80)
        print("VERDICT")
        print("="*80)
        print()

        if avg_r < 0.27:  # Worse than worst day ORB
            print(">>> DISCARD - Edge weaker than day ORBs")
        elif avg_r < 0.39:  # Between day ORBs
            print(">>> MARGINAL - Similar to day ORBs (tertiary tier)")
        elif avg_r < 1.08:  # Between day and night ORBs
            print(">>> POSSIBLE MIDDLE LAYER - Better than day ORBs, weaker than night ORBs")
        elif avg_r < 1.44:  # Between night ORBs and single liquidity
            print(">>> STRONG MIDDLE LAYER - Between night ORBs and single liquidity")
        elif avg_r < 1.95:  # Between single liquidity and cascades
            print(">>> SUCCESS - Sits between single liquidity and cascades")
            print("    This is the target middle layer!")
        else:
            print(">>> UNEXPECTED - Stronger than cascades (check for errors)")

        print()

        if frequency > 50:
            print("Note: High frequency may indicate too loose criteria")
        elif frequency < 5:
            print("Note: Low frequency may limit usefulness")

        print()

    def close(self):
        self.con.close()


if __name__ == "__main__":
    test = ProximityLiquidityTest()
    test.run_test(date(2024, 1, 1), date(2026, 1, 10))
    test.close()
