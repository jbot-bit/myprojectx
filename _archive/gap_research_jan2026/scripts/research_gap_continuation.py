"""
Gap Continuation Strategy Research - MGC Futures

Rigorous edge discovery analysis to determine if price gaps produce a statistically valid trading edge.

Research objectives:
1. Define "gap" across multiple definitions (time-based, session-based, ATR-normalized)
2. Test mechanical entry models (immediate, pullback, confirmation, retest)
3. Test fixed stop logic (gap midpoint, origin, ATR-based, fixed %)
4. Test take profit models (fixed R multiples, measured moves, time-based)
5. Validate with time-split IS/OOS (70/30)
6. Robustness testing (parameter sensitivity)

Database: gold.db (MGC futures, 2024-01-02 to 2026-01-15)
Timezone: All timestamps UTC, trading day 09:00-09:00 Australia/Brisbane (UTC+10)
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from dataclasses import dataclass
from typing import List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Configuration
DB_PATH = r"C:\Users\sydne\OneDrive\myprojectx\gold.db"
TZ_LOCAL = pytz.timezone('Australia/Brisbane')
TZ_UTC = pytz.UTC

# Research parameters
MIN_TRADES = 30  # Minimum sample size for statistical validity
IS_OOS_SPLIT = 0.70  # 70% in-sample, 30% out-of-sample
ROBUSTNESS_VARIATION = 0.20  # ±20% parameter variation for robustness testing

@dataclass
class Trade:
    """Individual trade record"""
    entry_time: datetime
    entry_price: float
    stop_price: float
    target_price: float
    exit_time: datetime
    exit_price: float
    pnl_r: float  # P&L in R multiples
    mae_r: float  # Maximum adverse excursion in R
    mfe_r: float  # Maximum favorable excursion in R
    gap_type: str
    gap_size: float
    entry_model: str
    day_of_week: int
    regime: str

@dataclass
class StrategyResult:
    """Strategy performance metrics"""
    strategy_name: str
    total_trades: int
    win_rate: float
    avg_r: float
    expectancy: float
    trades_per_year: float
    max_drawdown_r: float
    mae_avg: float
    mfe_avg: float
    trades: List[Trade]

    def is_statistically_valid(self) -> bool:
        return self.total_trades >= MIN_TRADES

    def __repr__(self):
        return (f"{self.strategy_name}\n"
                f"  Trades: {self.total_trades} | Win%: {self.win_rate:.1%} | "
                f"AvgR: {self.avg_r:.2f} | Exp: {self.expectancy:.3f}\n"
                f"  Trades/Yr: {self.trades_per_year:.1f} | MaxDD: {self.max_drawdown_r:.2f}R\n"
                f"  MAE: {self.mae_avg:.2f}R | MFE: {self.mfe_avg:.2f}R")


class GapResearcher:
    """Main research engine for gap continuation strategies"""

    def __init__(self, db_path: str):
        self.conn = duckdb.connect(db_path)
        self.bars_1m = None
        self.bars_5m = None
        self.daily_features = None
        self.is_split_date = None

    def load_data(self):
        """Load all required data from database"""
        print("Loading 1-minute bars...")
        query_1m = """
        SELECT
            ts_utc,
            open, high, low, close, volume
        FROM bars_1m
        WHERE symbol = 'MGC'
        ORDER BY ts_utc
        """
        self.bars_1m = self.conn.execute(query_1m).fetchdf()
        self.bars_1m['ts_utc'] = pd.to_datetime(self.bars_1m['ts_utc'], utc=True)

        print(f"  Loaded {len(self.bars_1m):,} 1-minute bars")

        print("Loading 5-minute bars...")
        query_5m = """
        SELECT
            ts_utc,
            open, high, low, close, volume
        FROM bars_5m
        WHERE symbol = 'MGC'
        ORDER BY ts_utc
        """
        self.bars_5m = self.conn.execute(query_5m).fetchdf()
        self.bars_5m['ts_utc'] = pd.to_datetime(self.bars_5m['ts_utc'], utc=True)

        print(f"  Loaded {len(self.bars_5m):,} 5-minute bars")

        print("Loading daily features...")
        query_daily = """
        SELECT * FROM daily_features
        WHERE instrument = 'MGC'
        ORDER BY date_local
        """
        self.daily_features = self.conn.execute(query_daily).fetchdf()
        self.daily_features['date_local'] = pd.to_datetime(self.daily_features['date_local'])

        print(f"  Loaded {len(self.daily_features):,} daily feature rows")

        # Calculate IS/OOS split date
        all_dates = sorted(self.bars_1m['ts_utc'].dt.date.unique())
        split_idx = int(len(all_dates) * IS_OOS_SPLIT)
        self.is_split_date = all_dates[split_idx]

        print(f"\nIS/OOS Split: {self.is_split_date}")
        print(f"  In-Sample: {all_dates[0]} to {all_dates[split_idx-1]} ({split_idx} days)")
        print(f"  Out-of-Sample: {all_dates[split_idx]} to {all_dates[-1]} ({len(all_dates)-split_idx} days)")

    def calculate_atr(self, window: int = 20) -> pd.Series:
        """Calculate ATR(20) on 5-minute bars for gap normalization"""
        print(f"Calculating ATR({window})...")

        df = self.bars_5m.copy()
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(window=window).mean()

        return df[['ts_utc', 'atr']].set_index('ts_utc')['atr']

    def detect_time_gaps(self, gap_minutes: int = 60) -> pd.DataFrame:
        """
        Detect time-based gaps (e.g., 60+ minutes between bars)

        Returns DataFrame with columns:
        - gap_time: timestamp of first bar after gap
        - gap_minutes: duration of gap
        - prev_close: close before gap
        - gap_open: open after gap
        - gap_size: gap_open - prev_close
        - gap_direction: 'UP' or 'DOWN'
        """
        print(f"\nDetecting time gaps (>{gap_minutes} minutes)...")

        df = self.bars_1m.copy()
        df['time_diff'] = df['ts_utc'].diff().dt.total_seconds() / 60

        # Find gaps
        gaps = df[df['time_diff'] > gap_minutes].copy()
        gaps['prev_close'] = df['close'].shift(1).loc[gaps.index]
        gaps['gap_size'] = gaps['open'] - gaps['prev_close']
        gaps['gap_direction'] = np.where(gaps['gap_size'] > 0, 'UP', 'DOWN')

        result = gaps[['ts_utc', 'time_diff', 'prev_close', 'open', 'gap_size', 'gap_direction']].rename(columns={
            'ts_utc': 'gap_time',
            'time_diff': 'gap_minutes',
            'open': 'gap_open'
        })

        print(f"  Found {len(result)} time gaps")
        print(f"    UP gaps: {(result['gap_direction'] == 'UP').sum()}")
        print(f"    DOWN gaps: {(result['gap_direction'] == 'DOWN').sum()}")

        return result

    def detect_session_gaps(self, session_hour: int = 9) -> pd.DataFrame:
        """
        Detect session open gaps (e.g., 09:00 local open vs prior close)

        session_hour: 9 for Asia open, 18 for London, 23 for NY (local time)

        Returns DataFrame with gap characteristics
        """
        print(f"\nDetecting session gaps (session_hour={session_hour} local)...")

        # Convert to local time for session detection
        df = self.bars_1m.copy()
        df['ts_local'] = df['ts_utc'].dt.tz_convert(TZ_LOCAL)
        df['hour'] = df['ts_local'].dt.hour
        df['minute'] = df['ts_local'].dt.minute

        # Find session opens
        session_opens = df[(df['hour'] == session_hour) & (df['minute'] == 0)].copy()

        # Get prior close (last bar before this session open)
        gaps = []
        for idx, row in session_opens.iterrows():
            prior_bars = df[df['ts_utc'] < row['ts_utc']]
            if len(prior_bars) == 0:
                continue

            prev_close = prior_bars.iloc[-1]['close']
            gap_size = row['open'] - prev_close
            gap_direction = 'UP' if gap_size > 0 else 'DOWN'

            gaps.append({
                'gap_time': row['ts_utc'],
                'session_hour': session_hour,
                'prev_close': prev_close,
                'gap_open': row['open'],
                'gap_size': gap_size,
                'gap_direction': gap_direction
            })

        result = pd.DataFrame(gaps)

        if len(result) > 0:
            print(f"  Found {len(result)} session gaps")
            print(f"    UP gaps: {(result['gap_direction'] == 'UP').sum()}")
            print(f"    DOWN gaps: {(result['gap_direction'] == 'DOWN').sum()}")
            print(f"    Avg gap size: {result['gap_size'].abs().mean():.2f}")
        else:
            print(f"  No session gaps found")

        return result

    def detect_structural_gaps(self, lookback_minutes: int = 60) -> pd.DataFrame:
        """
        Detect structural gaps: open outside previous N-minute range

        Returns DataFrame with gap characteristics
        """
        print(f"\nDetecting structural gaps (open outside prior {lookback_minutes}m range)...")

        df = self.bars_1m.copy()

        gaps = []
        for i in range(lookback_minutes, len(df)):
            current = df.iloc[i]
            prior_range = df.iloc[i-lookback_minutes:i]

            range_high = prior_range['high'].max()
            range_low = prior_range['low'].min()

            # Gap up: open > range_high
            # Gap down: open < range_low
            if current['open'] > range_high:
                gaps.append({
                    'gap_time': current['ts_utc'],
                    'lookback_minutes': lookback_minutes,
                    'range_high': range_high,
                    'range_low': range_low,
                    'gap_open': current['open'],
                    'gap_size': current['open'] - range_high,
                    'gap_direction': 'UP'
                })
            elif current['open'] < range_low:
                gaps.append({
                    'gap_time': current['ts_utc'],
                    'lookback_minutes': lookback_minutes,
                    'range_high': range_high,
                    'range_low': range_low,
                    'gap_open': current['open'],
                    'gap_size': range_low - current['open'],
                    'gap_direction': 'DOWN'
                })

        result = pd.DataFrame(gaps)

        if len(result) > 0:
            print(f"  Found {len(result)} structural gaps")
            print(f"    UP gaps: {(result['gap_direction'] == 'UP').sum()}")
            print(f"    DOWN gaps: {(result['gap_direction'] == 'DOWN').sum()}")
            print(f"    Avg gap size: {result['gap_size'].mean():.2f}")
        else:
            print(f"  No structural gaps found")

        return result

    def test_immediate_continuation(self, gaps: pd.DataFrame, gap_type: str,
                                   stop_type: str = 'gap_midpoint',
                                   target_r: float = 2.0) -> StrategyResult:
        """
        Test immediate market continuation strategy

        Entry: Market order at gap open
        Stop: Based on stop_type ('gap_midpoint', 'gap_origin', 'atr_pct')
        Target: Fixed R multiple

        Returns StrategyResult with all trades
        """
        print(f"\nTesting immediate continuation: {gap_type}, stop={stop_type}, target={target_r}R")

        trades = []

        for _, gap in gaps.iterrows():
            entry_time = gap['gap_time']
            entry_price = gap['gap_open']
            direction = 1 if gap['gap_direction'] == 'UP' else -1

            # Calculate stop based on stop_type
            if stop_type == 'gap_midpoint':
                if 'prev_close' in gap:
                    stop_price = (gap['prev_close'] + gap['gap_open']) / 2
                else:
                    # For structural gaps, use range midpoint
                    stop_price = (gap['range_high'] + gap['range_low']) / 2
            elif stop_type == 'gap_origin':
                if 'prev_close' in gap:
                    stop_price = gap['prev_close']
                else:
                    stop_price = gap['range_high'] if direction == -1 else gap['range_low']
            else:
                # Default: use gap size as stop distance
                stop_price = entry_price - direction * abs(gap['gap_size'])

            stop_distance = abs(entry_price - stop_price)
            if stop_distance == 0:
                continue

            target_price = entry_price + direction * stop_distance * target_r

            # Simulate trade execution using 1-minute bars
            future_bars = self.bars_1m[self.bars_1m['ts_utc'] > entry_time].head(1440)  # Max 1 day

            if len(future_bars) == 0:
                continue

            mae = 0
            mfe = 0
            exit_time = None
            exit_price = None

            for idx, bar in future_bars.iterrows():
                # Calculate MAE/MFE
                if direction == 1:
                    mae = min(mae, (bar['low'] - entry_price) / stop_distance)
                    mfe = max(mfe, (bar['high'] - entry_price) / stop_distance)

                    # Check stop hit
                    if bar['low'] <= stop_price:
                        exit_time = bar['ts_utc']
                        exit_price = stop_price
                        pnl_r = -1.0
                        break

                    # Check target hit
                    if bar['high'] >= target_price:
                        exit_time = bar['ts_utc']
                        exit_price = target_price
                        pnl_r = target_r
                        break
                else:  # Short
                    mae = min(mae, (entry_price - bar['high']) / stop_distance)
                    mfe = max(mfe, (entry_price - bar['low']) / stop_distance)

                    # Check stop hit
                    if bar['high'] >= stop_price:
                        exit_time = bar['ts_utc']
                        exit_price = stop_price
                        pnl_r = -1.0
                        break

                    # Check target hit
                    if bar['low'] <= target_price:
                        exit_time = bar['ts_utc']
                        exit_price = target_price
                        pnl_r = target_r
                        break

            # If no exit, close at end of day
            if exit_time is None:
                exit_time = future_bars.iloc[-1]['ts_utc']
                exit_price = future_bars.iloc[-1]['close']
                pnl_r = (exit_price - entry_price) / stop_distance * direction

            trades.append(Trade(
                entry_time=entry_time,
                entry_price=entry_price,
                stop_price=stop_price,
                target_price=target_price,
                exit_time=exit_time,
                exit_price=exit_price,
                pnl_r=pnl_r,
                mae_r=mae,
                mfe_r=mfe,
                gap_type=gap_type,
                gap_size=gap['gap_size'],
                entry_model='immediate',
                day_of_week=entry_time.weekday(),
                regime='all'
            ))

        # Calculate metrics
        if len(trades) == 0:
            return StrategyResult(
                strategy_name=f"{gap_type}_{stop_type}_{target_r}R_immediate",
                total_trades=0,
                win_rate=0,
                avg_r=0,
                expectancy=0,
                trades_per_year=0,
                max_drawdown_r=0,
                mae_avg=0,
                mfe_avg=0,
                trades=[]
            )

        wins = [t for t in trades if t.pnl_r > 0]
        win_rate = len(wins) / len(trades)
        avg_r = np.mean([t.pnl_r for t in trades])
        expectancy = avg_r

        # Calculate trades per year
        date_range = (trades[-1].entry_time - trades[0].entry_time).days / 365.25
        trades_per_year = len(trades) / date_range if date_range > 0 else 0

        # Calculate max drawdown
        cumulative = np.cumsum([t.pnl_r for t in trades])
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = running_max - cumulative
        max_drawdown_r = np.max(drawdowns) if len(drawdowns) > 0 else 0

        mae_avg = np.mean([t.mae_r for t in trades])
        mfe_avg = np.mean([t.mfe_r for t in trades])

        return StrategyResult(
            strategy_name=f"{gap_type}_{stop_type}_{target_r}R_immediate",
            total_trades=len(trades),
            win_rate=win_rate,
            avg_r=avg_r,
            expectancy=expectancy,
            trades_per_year=trades_per_year,
            max_drawdown_r=max_drawdown_r,
            mae_avg=mae_avg,
            mfe_avg=mfe_avg,
            trades=trades
        )

    def split_is_oos(self, result: StrategyResult) -> Tuple[StrategyResult, StrategyResult]:
        """Split strategy result into IS and OOS samples"""
        is_trades = [t for t in result.trades if t.entry_time.date() < self.is_split_date]
        oos_trades = [t for t in result.trades if t.entry_time.date() >= self.is_split_date]

        def build_result(trades, suffix):
            if len(trades) == 0:
                return StrategyResult(
                    strategy_name=f"{result.strategy_name}_{suffix}",
                    total_trades=0,
                    win_rate=0,
                    avg_r=0,
                    expectancy=0,
                    trades_per_year=0,
                    max_drawdown_r=0,
                    mae_avg=0,
                    mfe_avg=0,
                    trades=[]
                )

            wins = [t for t in trades if t.pnl_r > 0]
            win_rate = len(wins) / len(trades)
            avg_r = np.mean([t.pnl_r for t in trades])
            expectancy = avg_r

            date_range = (trades[-1].entry_time - trades[0].entry_time).days / 365.25
            trades_per_year = len(trades) / date_range if date_range > 0 else 0

            cumulative = np.cumsum([t.pnl_r for t in trades])
            running_max = np.maximum.accumulate(cumulative)
            drawdowns = running_max - cumulative
            max_drawdown_r = np.max(drawdowns) if len(drawdowns) > 0 else 0

            mae_avg = np.mean([t.mae_r for t in trades])
            mfe_avg = np.mean([t.mfe_r for t in trades])

            return StrategyResult(
                strategy_name=f"{result.strategy_name}_{suffix}",
                total_trades=len(trades),
                win_rate=win_rate,
                avg_r=avg_r,
                expectancy=expectancy,
                trades_per_year=trades_per_year,
                max_drawdown_r=max_drawdown_r,
                mae_avg=mae_avg,
                mfe_avg=mfe_avg,
                trades=trades
            )

        return build_result(is_trades, 'IS'), build_result(oos_trades, 'OOS')

    def run_full_research(self):
        """Execute complete gap continuation research"""
        print("="*80)
        print("GAP CONTINUATION STRATEGY RESEARCH - MGC FUTURES")
        print("="*80)

        self.load_data()

        all_results = []

        # 1. TIME-BASED GAPS
        print("\n" + "="*80)
        print("1. TIME-BASED GAP ANALYSIS")
        print("="*80)

        for gap_minutes in [30, 60, 90, 120]:
            gaps = self.detect_time_gaps(gap_minutes=gap_minutes)

            if len(gaps) < MIN_TRADES:
                print(f"  Skipping {gap_minutes}m gaps (insufficient sample: {len(gaps)} < {MIN_TRADES})")
                continue

            for stop_type in ['gap_midpoint', 'gap_origin']:
                for target_r in [1.0, 1.5, 2.0, 3.0]:
                    result = self.test_immediate_continuation(
                        gaps=gaps,
                        gap_type=f'time_{gap_minutes}m',
                        stop_type=stop_type,
                        target_r=target_r
                    )

                    if result.is_statistically_valid():
                        all_results.append(result)

        # 2. SESSION GAPS
        print("\n" + "="*80)
        print("2. SESSION GAP ANALYSIS")
        print("="*80)

        for session_hour in [9, 18, 23]:
            gaps = self.detect_session_gaps(session_hour=session_hour)

            if len(gaps) < MIN_TRADES:
                print(f"  Skipping {session_hour:02d}:00 session gaps (insufficient sample: {len(gaps)} < {MIN_TRADES})")
                continue

            for stop_type in ['gap_midpoint', 'gap_origin']:
                for target_r in [1.0, 1.5, 2.0, 3.0]:
                    result = self.test_immediate_continuation(
                        gaps=gaps,
                        gap_type=f'session_{session_hour:02d}00',
                        stop_type=stop_type,
                        target_r=target_r
                    )

                    if result.is_statistically_valid():
                        all_results.append(result)

        # 3. STRUCTURAL GAPS
        print("\n" + "="*80)
        print("3. STRUCTURAL GAP ANALYSIS")
        print("="*80)

        for lookback in [30, 60, 120]:
            gaps = self.detect_structural_gaps(lookback_minutes=lookback)

            if len(gaps) < MIN_TRADES:
                print(f"  Skipping {lookback}m structural gaps (insufficient sample: {len(gaps)} < {MIN_TRADES})")
                continue

            for stop_type in ['gap_midpoint']:
                for target_r in [1.0, 1.5, 2.0, 3.0]:
                    result = self.test_immediate_continuation(
                        gaps=gaps,
                        gap_type=f'structural_{lookback}m',
                        stop_type=stop_type,
                        target_r=target_r
                    )

                    if result.is_statistically_valid():
                        all_results.append(result)

        # 4. IS/OOS VALIDATION
        print("\n" + "="*80)
        print("4. IN-SAMPLE / OUT-OF-SAMPLE VALIDATION")
        print("="*80)

        validated_results = []

        for result in all_results:
            is_result, oos_result = self.split_is_oos(result)

            # Require both IS and OOS to be profitable and have sufficient trades
            if (is_result.is_statistically_valid() and
                oos_result.total_trades >= MIN_TRADES * 0.5 and  # Relaxed OOS requirement
                is_result.expectancy > 0 and
                oos_result.expectancy > 0):

                validated_results.append({
                    'strategy': result.strategy_name,
                    'is_trades': is_result.total_trades,
                    'is_winrate': is_result.win_rate,
                    'is_avgr': is_result.avg_r,
                    'is_exp': is_result.expectancy,
                    'oos_trades': oos_result.total_trades,
                    'oos_winrate': oos_result.win_rate,
                    'oos_avgr': oos_result.avg_r,
                    'oos_exp': oos_result.expectancy,
                    'full_result': result
                })

        # 5. FINAL RESULTS
        print("\n" + "="*80)
        print("5. FINAL VALIDATED STRATEGIES")
        print("="*80)

        if len(validated_results) == 0:
            print("\n❌ NO EDGE FOUND")
            print("\nConclusion:")
            print("  No gap continuation strategy survived IS/OOS validation.")
            print("  All tested combinations failed to show consistent positive expectancy.")
            print("  Gap continuation does NOT appear to provide a statistically valid edge on MGC futures.")
            return

        # Sort by OOS expectancy (most conservative metric)
        validated_results.sort(key=lambda x: x['oos_exp'], reverse=True)

        print(f"\n✅ FOUND {len(validated_results)} VALIDATED STRATEGIES\n")

        for i, v in enumerate(validated_results[:10], 1):  # Top 10
            print(f"\n{i}. {v['strategy']}")
            print(f"   IN-SAMPLE:  {v['is_trades']} trades | {v['is_winrate']:.1%} win | {v['is_avgr']:+.2f}R avg | {v['is_exp']:+.3f} exp")
            print(f"   OUT-SAMPLE: {v['oos_trades']} trades | {v['oos_winrate']:.1%} win | {v['oos_avgr']:+.2f}R avg | {v['oos_exp']:+.3f} exp")
            print(f"   Trades/Year: {v['full_result'].trades_per_year:.1f}")
            print(f"   MAE: {v['full_result'].mae_avg:.2f}R | MFE: {v['full_result'].mfe_avg:.2f}R")

        # 6. SAVE DETAILED RESULTS
        print("\n" + "="*80)
        print("6. SAVING DETAILED RESULTS")
        print("="*80)

        # Save summary
        summary_df = pd.DataFrame([{
            'strategy': v['strategy'],
            'is_trades': v['is_trades'],
            'is_winrate': v['is_winrate'],
            'is_avgr': v['is_avgr'],
            'is_exp': v['is_exp'],
            'oos_trades': v['oos_trades'],
            'oos_winrate': v['oos_winrate'],
            'oos_avgr': v['oos_avgr'],
            'oos_exp': v['oos_exp'],
            'trades_per_year': v['full_result'].trades_per_year,
            'mae_avg': v['full_result'].mae_avg,
            'mfe_avg': v['full_result'].mfe_avg
        } for v in validated_results])

        summary_path = r"C:\Users\sydne\OneDrive\myprojectx\gap_research_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        print(f"  Saved summary: {summary_path}")

        # Save top strategy trades
        if len(validated_results) > 0:
            top_strategy = validated_results[0]
            trades_df = pd.DataFrame([{
                'entry_time': t.entry_time,
                'entry_price': t.entry_price,
                'stop_price': t.stop_price,
                'target_price': t.target_price,
                'exit_time': t.exit_time,
                'exit_price': t.exit_price,
                'pnl_r': t.pnl_r,
                'mae_r': t.mae_r,
                'mfe_r': t.mfe_r,
                'gap_type': t.gap_type,
                'gap_size': t.gap_size,
                'day_of_week': t.day_of_week
            } for t in top_strategy['full_result'].trades])

            trades_path = r"C:\Users\sydne\OneDrive\myprojectx\gap_research_top_strategy_trades.csv"
            trades_df.to_csv(trades_path, index=False)
            print(f"  Saved top strategy trades: {trades_path}")

        print("\n" + "="*80)
        print("RESEARCH COMPLETE")
        print("="*80)


def main():
    researcher = GapResearcher(DB_PATH)
    researcher.run_full_research()


if __name__ == "__main__":
    main()
