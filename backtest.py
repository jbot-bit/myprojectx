"""
ORB Backtesting Engine
======================
Systematically test ORB strategies with customizable filters.

Features:
- Test any ORB time (09:00, 10:00, 11:00, 18:00, 23:00, 00:30)
- Filter by direction, session types, Asia range, ORB size
- Calculate win rate, avg R, total R, max drawdown
- Generate equity curve
- Export results to CSV

Usage:
  # Test 11:00 UP breakouts
  python backtest.py --orb 1100 --direction UP

  # Test 18:00 with filters
  python backtest.py --orb 1800 --london_type CONSOLIDATION

  # Test multiple setups and compare
  python backtest.py --orb 1100 --direction UP --compare 1800 UP

  # Export results
  python backtest.py --orb 1100 --direction UP --export results_1100_up.csv

  # Custom date range
  python backtest.py --orb 1100 --start 2024-01-01 --end 2025-12-31
"""

import duckdb
import argparse
from datetime import date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import csv


@dataclass
class BacktestResult:
    """Results from a backtest run"""
    strategy_name: str
    total_trades: int
    wins: int
    losses: int
    no_trades: int
    win_rate: float
    avg_r: float
    total_r: float
    best_r: float
    worst_r: float
    max_drawdown_r: float
    sharpe_ratio: float
    trades: List[Dict]  # Individual trade details


class ORBBacktester:
    """Backtest ORB strategies"""

    def __init__(self, db_path: str = "gold.db"):
        self.db_path = db_path

    def backtest_strategy(
        self,
        orb_time: str,
        direction: Optional[str] = None,
        asia_type: Optional[str] = None,
        london_type: Optional[str] = None,
        ny_type: Optional[str] = None,
        min_asia_range: Optional[float] = None,
        max_asia_range: Optional[float] = None,
        min_orb_size: Optional[float] = None,
        max_orb_size: Optional[float] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> BacktestResult:
        """
        Backtest an ORB strategy with filters.

        Args:
            orb_time: ORB time (0900, 1000, 1100, 1800, 2300, 0030)
            direction: UP or DOWN (None = both directions)
            asia_type: TIGHT, NORMAL, EXPANDED
            london_type: CONSOLIDATION, SWEEP_HIGH, SWEEP_LOW, EXPANSION
            ny_type: CONSOLIDATION, SWEEP_HIGH, SWEEP_LOW, EXPANSION
            min_asia_range: Minimum Asia range in ticks
            max_asia_range: Maximum Asia range in ticks
            min_orb_size: Minimum ORB size in ticks
            max_orb_size: Maximum ORB size in ticks
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            BacktestResult with performance metrics and trade list
        """

        con = duckdb.connect(self.db_path, read_only=True)

        try:
            # Build filter conditions
            conditions = [f"orb_{orb_time}_outcome IS NOT NULL"]
            params = []

            if direction:
                conditions.append(f"orb_{orb_time}_break_dir = ?")
                params.append(direction)

            if asia_type:
                conditions.append("asia_type = ?")
                params.append(asia_type)

            if london_type:
                conditions.append("london_type = ?")
                params.append(london_type)

            if ny_type:
                conditions.append("ny_type = ?")
                params.append(ny_type)

            if min_asia_range is not None:
                conditions.append("(asia_range / 0.1) >= ?")
                params.append(min_asia_range)

            if max_asia_range is not None:
                conditions.append("(asia_range / 0.1) <= ?")
                params.append(max_asia_range)

            if min_orb_size is not None:
                conditions.append(f"(orb_{orb_time}_size / 0.1) >= ?")
                params.append(min_orb_size)

            if max_orb_size is not None:
                conditions.append(f"(orb_{orb_time}_size / 0.1) <= ?")
                params.append(max_orb_size)

            if start_date:
                conditions.append("date_local >= ?")
                params.append(start_date)

            if end_date:
                conditions.append("date_local <= ?")
                params.append(end_date)

            where_clause = " AND ".join(conditions)

            # Query trades
            query = f"""
                SELECT
                    date_local,
                    orb_{orb_time}_break_dir as direction,
                    orb_{orb_time}_outcome as outcome,
                    orb_{orb_time}_r_multiple as r_multiple,
                    orb_{orb_time}_size as orb_size,
                    asia_type,
                    london_type,
                    ny_type,
                    (asia_range / 0.1) as asia_range_ticks
                FROM daily_features
                WHERE {where_clause}
                ORDER BY date_local
            """

            rows = con.execute(query, params).fetchall()

            # Process results
            trades = []
            wins = 0
            losses = 0
            no_trades = 0
            r_multiples = []

            for row in rows:
                trade_date, dir, outcome, r_mult, orb_size, asia_t, london_t, ny_t, asia_ticks = row

                trade = {
                    "date": trade_date,
                    "direction": dir,
                    "outcome": outcome,
                    "r_multiple": r_mult,
                    "orb_size": orb_size,
                    "asia_type": asia_t,
                    "london_type": london_t,
                    "ny_type": ny_t,
                    "asia_range_ticks": asia_ticks,
                }

                trades.append(trade)

                if outcome == "WIN":
                    wins += 1
                    if r_mult:
                        r_multiples.append(r_mult)
                elif outcome == "LOSS":
                    losses += 1
                    if r_mult:
                        r_multiples.append(r_mult)
                elif outcome == "NO_TRADE":
                    no_trades += 1

            # Calculate metrics
            total_trades = wins + losses
            win_rate = wins / total_trades if total_trades > 0 else 0
            avg_r = sum(r_multiples) / len(r_multiples) if r_multiples else 0
            total_r = sum(r_multiples) if r_multiples else 0
            best_r = max(r_multiples) if r_multiples else 0
            worst_r = min(r_multiples) if r_multiples else 0

            # Max drawdown (in R)
            cumulative_r = 0
            peak_r = 0
            max_dd_r = 0

            for r in r_multiples:
                cumulative_r += r
                if cumulative_r > peak_r:
                    peak_r = cumulative_r
                dd = peak_r - cumulative_r
                if dd > max_dd_r:
                    max_dd_r = dd

            # Sharpe ratio (simplified: avg R / std dev of R)
            if len(r_multiples) > 1:
                import statistics
                std_r = statistics.stdev(r_multiples)
                sharpe = avg_r / std_r if std_r > 0 else 0
            else:
                sharpe = 0

            # Strategy name
            strategy_name = f"ORB {orb_time}"
            if direction:
                strategy_name += f" {direction}"
            if asia_type:
                strategy_name += f" | Asia {asia_type}"
            if london_type:
                strategy_name += f" | London {london_type}"
            if ny_type:
                strategy_name += f" | NY {ny_type}"

            return BacktestResult(
                strategy_name=strategy_name,
                total_trades=total_trades,
                wins=wins,
                losses=losses,
                no_trades=no_trades,
                win_rate=win_rate,
                avg_r=avg_r,
                total_r=total_r,
                best_r=best_r,
                worst_r=worst_r,
                max_drawdown_r=max_dd_r,
                sharpe_ratio=sharpe,
                trades=trades,
            )

        finally:
            con.close()

    def print_result(self, result: BacktestResult):
        """Print backtest results"""
        print("\n" + "="*80)
        print(f"BACKTEST RESULTS: {result.strategy_name}")
        print("="*80)

        print(f"\nTrade Summary:")
        print(f"  Total Trades: {result.total_trades}")
        print(f"  Wins: {result.wins} | Losses: {result.losses} | No Trades: {result.no_trades}")
        print(f"  Win Rate: {result.win_rate:.1%}")

        print(f"\nPerformance Metrics:")
        print(f"  Average R: {result.avg_r:+.3f}")
        print(f"  Total R: {result.total_r:+.2f}")
        print(f"  Best R: {result.best_r:+.2f}")
        print(f"  Worst R: {result.worst_r:+.2f}")
        print(f"  Max Drawdown: {result.max_drawdown_r:.2f} R")
        print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")

        # Show recent trades
        if result.trades:
            print(f"\nRecent Trades (last 10):")
            print(f"  {'Date':<12} {'Dir':<6} {'Outcome':<8} {'R':<8}")
            print("  " + "-"*40)
            for trade in result.trades[-10:]:
                r_str = f"{trade['r_multiple']:+.2f}" if trade['r_multiple'] else "N/A"
                print(f"  {trade['date']!s:<12} {trade['direction']:<6} {trade['outcome']:<8} {r_str:<8}")

        print("\n" + "="*80)

    def compare_strategies(self, results: List[BacktestResult]):
        """Compare multiple strategy results"""
        if not results:
            return

        print("\n" + "="*120)
        print("STRATEGY COMPARISON")
        print("="*120)

        print(f"\n{'Strategy':<50} {'Trades':>8} {'WR':>8} {'Avg R':>10} {'Total R':>10} {'Max DD':>10} {'Sharpe':>10}")
        print("-"*120)

        # Sort by total R descending
        results_sorted = sorted(results, key=lambda r: r.total_r, reverse=True)

        for result in results_sorted:
            print(f"{result.strategy_name:<50} "
                  f"{result.total_trades:>8} "
                  f"{result.win_rate:>7.1%} "
                  f"{result.avg_r:>+9.3f} "
                  f"{result.total_r:>+9.2f} "
                  f"{result.max_drawdown_r:>9.2f} "
                  f"{result.sharpe_ratio:>9.2f}")

        print("\n" + "="*120)

    def export_trades(self, result: BacktestResult, filename: str):
        """Export trade list to CSV"""
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Date', 'Direction', 'Outcome', 'R Multiple', 'ORB Size',
                'Asia Type', 'London Type', 'NY Type', 'Asia Range Ticks'
            ])

            for trade in result.trades:
                writer.writerow([
                    trade['date'],
                    trade['direction'],
                    trade['outcome'],
                    trade['r_multiple'],
                    trade['orb_size'],
                    trade['asia_type'],
                    trade['london_type'],
                    trade['ny_type'],
                    trade['asia_range_ticks'],
                ])

        print(f"\nExported {len(result.trades)} trades to: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Backtest ORB strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--orb", required=True,
                       choices=["0900", "1000", "1100", "1800", "2300", "0030"],
                       help="ORB time to test")
    parser.add_argument("--direction", choices=["UP", "DOWN"],
                       help="Breakout direction (default: both)")
    parser.add_argument("--asia_type", choices=["TIGHT", "NORMAL", "EXPANDED"],
                       help="Filter by Asia session type")
    parser.add_argument("--london_type",
                       choices=["CONSOLIDATION", "SWEEP_HIGH", "SWEEP_LOW", "EXPANSION"],
                       help="Filter by London session type")
    parser.add_argument("--ny_type",
                       choices=["CONSOLIDATION", "SWEEP_HIGH", "SWEEP_LOW", "EXPANSION"],
                       help="Filter by NY session type")
    parser.add_argument("--min_asia_range", type=float,
                       help="Min Asia range in ticks")
    parser.add_argument("--max_asia_range", type=float,
                       help="Max Asia range in ticks")
    parser.add_argument("--min_orb_size", type=float,
                       help="Min ORB size in ticks")
    parser.add_argument("--max_orb_size", type=float,
                       help="Max ORB size in ticks")
    parser.add_argument("--start", type=str,
                       help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str,
                       help="End date (YYYY-MM-DD)")
    parser.add_argument("--compare", nargs='+', metavar=('ORB', 'DIR'),
                       help="Compare with other setups (e.g., --compare 1800 UP 2300 DOWN)")
    parser.add_argument("--export", type=str, metavar='FILE',
                       help="Export trades to CSV")

    args = parser.parse_args()

    # Parse dates
    start_date = date.fromisoformat(args.start) if args.start else None
    end_date = date.fromisoformat(args.end) if args.end else None

    backtester = ORBBacktester()

    # Run main backtest
    result = backtester.backtest_strategy(
        orb_time=args.orb,
        direction=args.direction,
        asia_type=args.asia_type,
        london_type=args.london_type,
        ny_type=args.ny_type,
        min_asia_range=args.min_asia_range,
        max_asia_range=args.max_asia_range,
        min_orb_size=args.min_orb_size,
        max_orb_size=args.max_orb_size,
        start_date=start_date,
        end_date=end_date,
    )

    backtester.print_result(result)

    # Run comparison backtests if requested
    if args.compare:
        compare_results = [result]

        # Parse compare arguments (pairs of ORB and DIR)
        i = 0
        while i < len(args.compare):
            comp_orb = args.compare[i]
            comp_dir = args.compare[i+1] if i+1 < len(args.compare) else None

            if comp_orb in ["0900", "1000", "1100", "1800", "2300", "0030"]:
                comp_result = backtester.backtest_strategy(
                    orb_time=comp_orb,
                    direction=comp_dir if comp_dir in ["UP", "DOWN"] else None,
                    start_date=start_date,
                    end_date=end_date,
                )
                compare_results.append(comp_result)
                i += 2 if comp_dir in ["UP", "DOWN"] else 1
            else:
                i += 1

        if len(compare_results) > 1:
            backtester.compare_strategies(compare_results)

    # Export if requested
    if args.export:
        backtester.export_trades(result, args.export)


if __name__ == "__main__":
    main()
