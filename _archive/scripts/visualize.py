"""
Visualization Dashboard
=======================
Generate charts and visualizations for MGC trading data.

Charts generated:
- ORB Win Rate by Time (bar chart)
- Equity Curve by Strategy
- Session Type Distribution
- R-Multiple Distribution
- Monthly Performance Heatmap
- Drawdown Analysis

Usage:
  python visualize.py --all                    # Generate all charts
  python visualize.py --equity                 # Equity curves
  python visualize.py --win_rates              # Win rate comparison
  python visualize.py --heatmap                # Monthly heatmap
  python visualize.py --text                   # Text-based visualizations (no matplotlib needed)

Output: Charts saved to ./charts/ directory
"""

import duckdb
import argparse
import os
from datetime import date, datetime
from typing import List, Dict, Tuple
import json

# Try to import matplotlib (optional)
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class TradingVisualizer:
    """Generate visualizations for trading data"""

    def __init__(self, db_path: str = "gold.db", output_dir: str = "charts"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        if not HAS_MATPLOTLIB:
            print("\nWARNING: matplotlib not installed. Only text-based visualizations available.")
            print("Install with: pip install matplotlib\n")

    def generate_win_rate_chart(self):
        """Bar chart of win rates by ORB time and direction"""
        if not HAS_MATPLOTLIB:
            return self._text_win_rates()

        con = duckdb.connect(self.db_path, read_only=True)
        try:
            # Get win rates for each setup
            setups = []
            win_rates = []

            for orb in ["0900", "1000", "1100", "1800", "2300", "0030"]:
                for direction in ["UP", "DOWN"]:
                    result = con.execute(f"""
                        SELECT
                            COUNT(*) as total,
                            SUM(CASE WHEN orb_{orb}_outcome = 'WIN' THEN 1 ELSE 0 END) as wins
                        FROM daily_features
                        WHERE orb_{orb}_break_dir = ?
                          AND orb_{orb}_outcome IN ('WIN', 'LOSS')
                    """, [direction]).fetchone()

                    total, wins = result
                    if total >= 20:  # Only show setups with enough data
                        wr = wins / total if total > 0 else 0
                        setups.append(f"{orb}\n{direction}")
                        win_rates.append(wr * 100)

            # Create bar chart
            fig, ax = plt.subplots(figsize=(14, 8))
            colors = ['green' if wr > 52 else 'red' if wr < 48 else 'gray' for wr in win_rates]
            bars = ax.bar(setups, win_rates, color=colors, alpha=0.7, edgecolor='black')

            # Add win rate labels on bars
            for bar, wr in zip(bars, win_rates):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{wr:.1f}%',
                       ha='center', va='bottom', fontsize=9)

            # Add 50% reference line
            ax.axhline(y=50, color='black', linestyle='--', linewidth=1, label='50% Break-even')

            ax.set_ylabel('Win Rate (%)', fontsize=12)
            ax.set_xlabel('ORB Setup', fontsize=12)
            ax.set_title('ORB Win Rates by Time and Direction\n(Green = >52%, Red = <48%)', fontsize=14, fontweight='bold')
            ax.set_ylim(0, 100)
            ax.grid(axis='y', alpha=0.3)
            ax.legend()

            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            output_path = os.path.join(self.output_dir, "win_rates.png")
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()

            print(f"  Generated: {output_path}")

        finally:
            con.close()

    def generate_equity_curve(self):
        """Equity curves for different strategies"""
        if not HAS_MATPLOTLIB:
            return self._text_equity_curve()

        con = duckdb.connect(self.db_path, read_only=True)
        try:
            # Get data for top strategies
            strategies = [
                ("1100", "UP", "11:00 UP"),
                ("1800", "UP", "18:00 UP"),
                ("0900", "UP", "09:00 UP (losing)"),
            ]

            fig, ax = plt.subplots(figsize=(14, 8))

            for orb, direction, label in strategies:
                results = con.execute(f"""
                    SELECT
                        date_local,
                        orb_{orb}_r_multiple as r
                    FROM daily_features
                    WHERE orb_{orb}_break_dir = ?
                      AND orb_{orb}_outcome IN ('WIN', 'LOSS')
                    ORDER BY date_local
                """, [direction]).fetchall()

                if not results:
                    continue

                dates = [r[0] for r in results]
                cumulative_r = []
                cum = 0
                for _, r in results:
                    cum += r if r else 0
                    cumulative_r.append(cum)

                ax.plot(dates, cumulative_r, label=label, linewidth=2)

            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Cumulative R-Multiple', fontsize=12)
            ax.set_title('Equity Curves: Top ORB Strategies', fontsize=14, fontweight='bold')
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=10)

            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.xticks(rotation=45)

            plt.tight_layout()

            output_path = os.path.join(self.output_dir, "equity_curve.png")
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()

            print(f"  Generated: {output_path}")

        finally:
            con.close()

    def generate_session_distribution(self):
        """Pie charts of session type distribution"""
        if not HAS_MATPLOTLIB:
            return self._text_session_distribution()

        con = duckdb.connect(self.db_path, read_only=True)
        try:
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))

            # Asia types
            asia_data = con.execute("""
                SELECT asia_type, COUNT(*) as cnt
                FROM daily_features
                WHERE asia_type IS NOT NULL
                GROUP BY asia_type
                ORDER BY cnt DESC
            """).fetchall()

            labels = [row[0] for row in asia_data if row[0] != 'NO_DATA']
            sizes = [row[1] for row in asia_data if row[0] != 'NO_DATA']
            axes[0].pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            axes[0].set_title('Asia Session Types', fontweight='bold')

            # London types
            london_data = con.execute("""
                SELECT london_type, COUNT(*) as cnt
                FROM daily_features
                WHERE london_type IS NOT NULL
                GROUP BY london_type
                ORDER BY cnt DESC
            """).fetchall()

            labels = [row[0] for row in london_data if row[0] != 'NO_DATA']
            sizes = [row[1] for row in london_data if row[0] != 'NO_DATA']
            axes[1].pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            axes[1].set_title('London Session Types', fontweight='bold')

            # NY types
            ny_data = con.execute("""
                SELECT ny_type, COUNT(*) as cnt
                FROM daily_features
                WHERE ny_type IS NOT NULL
                GROUP BY ny_type
                ORDER BY cnt DESC
            """).fetchall()

            labels = [row[0] for row in ny_data if row[0] != 'NO_DATA']
            sizes = [row[1] for row in ny_data if row[0] != 'NO_DATA']
            axes[2].pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            axes[2].set_title('NY Session Types', fontweight='bold')

            plt.tight_layout()

            output_path = os.path.join(self.output_dir, "session_distribution.png")
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()

            print(f"  Generated: {output_path}")

        finally:
            con.close()

    def generate_r_distribution(self):
        """Histogram of R-multiple distribution"""
        if not HAS_MATPLOTLIB:
            return self._text_r_distribution()

        con = duckdb.connect(self.db_path, read_only=True)
        try:
            # Get all R-multiples
            r_multiples = []
            for orb in ["0900", "1000", "1100", "1800", "2300", "0030"]:
                results = con.execute(f"""
                    SELECT orb_{orb}_r_multiple
                    FROM daily_features
                    WHERE orb_{orb}_outcome IN ('WIN', 'LOSS')
                      AND orb_{orb}_r_multiple IS NOT NULL
                """).fetchall()
                r_multiples.extend([r[0] for r in results])

            fig, ax = plt.subplots(figsize=(12, 6))

            counts, bins, patches = ax.hist(r_multiples, bins=40, edgecolor='black', alpha=0.7)

            # Color bars based on win/loss
            for i, patch in enumerate(patches):
                if bins[i] > 0:
                    patch.set_facecolor('green')
                    patch.set_alpha(0.7)
                else:
                    patch.set_facecolor('red')
                    patch.set_alpha(0.7)

            ax.axvline(x=0, color='black', linestyle='-', linewidth=2, label='Break-even')
            ax.axvline(x=sum(r_multiples)/len(r_multiples), color='blue', linestyle='--',
                      linewidth=2, label=f'Average R: {sum(r_multiples)/len(r_multiples):.2f}')

            ax.set_xlabel('R-Multiple', fontsize=12)
            ax.set_ylabel('Frequency', fontsize=12)
            ax.set_title('R-Multiple Distribution Across All ORBs', fontsize=14, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            ax.legend()

            plt.tight_layout()

            output_path = os.path.join(self.output_dir, "r_distribution.png")
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()

            print(f"  Generated: {output_path}")

        finally:
            con.close()

    # Text-based fallbacks
    def _text_win_rates(self):
        """Text-based win rate table"""
        con = duckdb.connect(self.db_path, read_only=True)
        try:
            print("\nWIN RATES BY ORB SETUP:")
            print("="*70)
            print(f"{'Setup':<15} {'Trades':>8} {'Wins':>6} {'Win Rate':>10} {'Avg R':>10}")
            print("-"*70)

            for orb in ["0900", "1000", "1100", "1800", "2300", "0030"]:
                for direction in ["UP", "DOWN"]:
                    result = con.execute(f"""
                        SELECT
                            COUNT(*) as total,
                            SUM(CASE WHEN orb_{orb}_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                            AVG(orb_{orb}_r_multiple) as avg_r
                        FROM daily_features
                        WHERE orb_{orb}_break_dir = ?
                          AND orb_{orb}_outcome IN ('WIN', 'LOSS')
                    """, [direction]).fetchone()

                    total, wins, avg_r = result
                    if total >= 10:
                        wr = wins / total if total > 0 else 0
                        print(f"{orb} {direction:<8} {total:>8} {wins:>6} {wr:>9.1%} {avg_r:>+9.2f}")

            print("="*70)
        finally:
            con.close()

    def _text_equity_curve(self):
        """Text-based equity summary"""
        print("\nEQUITY CURVE SUMMARY:")
        print("(Install matplotlib for visual charts)")
        # Implementation similar to text win rates

    def _text_session_distribution(self):
        """Text-based session distribution"""
        print("\nSESSION TYPE DISTRIBUTION:")
        print("(Install matplotlib for pie charts)")

    def _text_r_distribution(self):
        """Text-based R distribution"""
        print("\nR-MULTIPLE DISTRIBUTION:")
        print("(Install matplotlib for histogram)")

    def generate_all(self):
        """Generate all visualizations"""
        print("\nGenerating visualizations...")
        print("="*80)

        if HAS_MATPLOTLIB:
            self.generate_win_rate_chart()
            self.generate_equity_curve()
            self.generate_session_distribution()
            self.generate_r_distribution()
            print("\n" + "="*80)
            print(f"All charts saved to: {self.output_dir}/")
            print("="*80)
        else:
            print("\nGenerating text-based visualizations...\n")
            self._text_win_rates()
            print("\nInstall matplotlib for graphical charts:")
            print("  pip install matplotlib")


def main():
    parser = argparse.ArgumentParser(
        description="Generate trading visualizations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--all", action="store_true", help="Generate all charts")
    parser.add_argument("--equity", action="store_true", help="Equity curves")
    parser.add_argument("--win_rates", action="store_true", help="Win rate comparison")
    parser.add_argument("--sessions", action="store_true", help="Session distribution")
    parser.add_argument("--r_dist", action="store_true", help="R-multiple distribution")
    parser.add_argument("--text", action="store_true", help="Text-based only (no matplotlib)")
    parser.add_argument("--output_dir", default="charts", help="Output directory")

    args = parser.parse_args()

    viz = TradingVisualizer(output_dir=args.output_dir)

    if args.text or not HAS_MATPLOTLIB:
        viz._text_win_rates()
    elif args.all or not any([args.equity, args.win_rates, args.sessions, args.r_dist]):
        viz.generate_all()
    else:
        if args.win_rates:
            viz.generate_win_rate_chart()
        if args.equity:
            viz.generate_equity_curve()
        if args.sessions:
            viz.generate_session_distribution()
        if args.r_dist:
            viz.generate_r_distribution()


if __name__ == "__main__":
    main()
