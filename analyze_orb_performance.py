"""
ORB Performance Analysis
========================
Analyzes win rates, R-multiples, and performance by:
- ORB time (09:00, 10:00, 11:00, 18:00, 23:00, 00:30)
- Break direction (UP/DOWN)
- Session types (Asia: TIGHT/NORMAL/EXPANDED, London/NY: types)
- Combined conditions
"""

import duckdb
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ORBStats:
    """Statistics for an ORB setup"""
    total_trades: int
    wins: int
    losses: int
    no_trades: int
    win_rate: float
    total_r: float
    avg_r: float

    def __str__(self):
        if self.total_trades == 0:
            return "No trades"
        return (f"Trades: {self.total_trades} | Win: {self.wins} Loss: {self.losses} "
                f"| WR: {self.win_rate:.1%} | Total R: {self.total_r:+.1f} | Avg R: {self.avg_r:+.2f}")


def calculate_stats(rows: List[Tuple]) -> ORBStats:
    """Calculate statistics from query results (outcome, r_multiple)"""
    if not rows:
        return ORBStats(0, 0, 0, 0, 0.0, 0.0, 0.0)

    wins = sum(1 for outcome, _ in rows if outcome == "WIN")
    losses = sum(1 for outcome, _ in rows if outcome == "LOSS")
    no_trades = sum(1 for outcome, _ in rows if outcome == "NO_TRADE" or outcome is None)

    # Only count actual trades (exclude NO_TRADE)
    trades = [r for r in rows if r[0] in ("WIN", "LOSS") and r[1] is not None]
    total_trades = len(trades)

    if total_trades == 0:
        return ORBStats(0, 0, 0, no_trades, 0.0, 0.0, 0.0)

    total_r = sum(r[1] for r in trades)
    avg_r = total_r / total_trades
    win_rate = wins / total_trades if total_trades > 0 else 0.0

    return ORBStats(total_trades, wins, losses, no_trades, win_rate, total_r, avg_r)


def analyze_orb_by_time(con: duckdb.DuckDBPyConnection):
    """Analyze each ORB time slot overall performance"""
    print("\n" + "="*80)
    print("ORB PERFORMANCE BY TIME")
    print("="*80)

    orb_times = ["0900", "1000", "1100", "1800", "2300", "0030"]
    orb_labels = {
        "0900": "09:00 (Asia Open)",
        "1000": "10:00 (Asia Mid)",
        "1100": "11:00 (Asia Late)",
        "1800": "18:00 (London Open)",
        "2300": "23:00 (NY Open)",
        "0030": "00:30 (NYSE)",
    }

    for orb in orb_times:
        rows = con.execute(f"""
            SELECT orb_{orb}_outcome, orb_{orb}_r_multiple
            FROM daily_features
            WHERE orb_{orb}_outcome IS NOT NULL
        """).fetchall()

        stats = calculate_stats(rows)
        print(f"\n{orb_labels[orb]}:")
        print(f"  {stats}")


def analyze_orb_by_direction(con: duckdb.DuckDBPyConnection):
    """Analyze ORB performance by break direction (UP/DOWN)"""
    print("\n" + "="*80)
    print("ORB PERFORMANCE BY BREAK DIRECTION")
    print("="*80)

    orb_times = ["0900", "1000", "1100", "1800", "2300", "0030"]
    orb_labels = {
        "0900": "09:00",
        "1000": "10:00",
        "1100": "11:00",
        "1800": "18:00",
        "2300": "23:00",
        "0030": "00:30",
    }

    for orb in orb_times:
        print(f"\n{orb_labels[orb]}:")

        # UP breaks
        rows_up = con.execute(f"""
            SELECT orb_{orb}_outcome, orb_{orb}_r_multiple
            FROM daily_features
            WHERE orb_{orb}_break_dir = 'UP'
        """).fetchall()

        stats_up = calculate_stats(rows_up)
        print(f"  UP:   {stats_up}")

        # DOWN breaks
        rows_down = con.execute(f"""
            SELECT orb_{orb}_outcome, orb_{orb}_r_multiple
            FROM daily_features
            WHERE orb_{orb}_break_dir = 'DOWN'
        """).fetchall()

        stats_down = calculate_stats(rows_down)
        print(f"  DOWN: {stats_down}")


def analyze_orb_by_asia_type(con: duckdb.DuckDBPyConnection):
    """Analyze ORB performance by Asia session type"""
    print("\n" + "="*80)
    print("ORB PERFORMANCE BY ASIA TYPE")
    print("="*80)

    asia_types = ["TIGHT", "NORMAL", "EXPANDED"]
    orb_times = ["0900", "1000", "1100"]  # Focus on Asia ORBs

    for asia_type in asia_types:
        print(f"\nAsia {asia_type}:")
        for orb in orb_times:
            rows = con.execute(f"""
                SELECT orb_{orb}_outcome, orb_{orb}_r_multiple
                FROM daily_features
                WHERE asia_type = ?
                  AND orb_{orb}_outcome IS NOT NULL
            """, [asia_type]).fetchall()

            stats = calculate_stats(rows)
            if stats.total_trades > 0:
                print(f"  {orb}: {stats}")


def analyze_orb_by_london_type(con: duckdb.DuckDBPyConnection):
    """Analyze ORB performance by London session type"""
    print("\n" + "="*80)
    print("ORB PERFORMANCE BY LONDON TYPE")
    print("="*80)

    london_types = ["CONSOLIDATION", "SWEEP_HIGH", "SWEEP_LOW", "EXPANSION"]
    orb_times = ["1800", "2300", "0030"]  # Focus on London/NY ORBs

    for london_type in london_types:
        print(f"\nLondon {london_type}:")
        for orb in orb_times:
            rows = con.execute(f"""
                SELECT orb_{orb}_outcome, orb_{orb}_r_multiple
                FROM daily_features
                WHERE london_type = ?
                  AND orb_{orb}_outcome IS NOT NULL
            """, [london_type]).fetchall()

            stats = calculate_stats(rows)
            if stats.total_trades > 0:
                print(f"  {orb}: {stats}")


def analyze_orb_by_ny_type(con: duckdb.DuckDBPyConnection):
    """Analyze ORB performance by NY session type"""
    print("\n" + "="*80)
    print("ORB PERFORMANCE BY NY TYPE")
    print("="*80)

    ny_types = ["CONSOLIDATION", "SWEEP_HIGH", "SWEEP_LOW", "EXPANSION"]
    orb_times = ["2300", "0030"]  # Focus on NY ORBs

    for ny_type in ny_types:
        print(f"\nNY {ny_type}:")
        for orb in orb_times:
            rows = con.execute(f"""
                SELECT orb_{orb}_outcome, orb_{orb}_r_multiple
                FROM daily_features
                WHERE ny_type = ?
                  AND orb_{orb}_outcome IS NOT NULL
            """, [ny_type]).fetchall()

            stats = calculate_stats(rows)
            if stats.total_trades > 0:
                print(f"  {orb}: {stats}")


def analyze_best_setups(con: duckdb.DuckDBPyConnection):
    """Find the best performing setups (combinations with >60% win rate and >5 trades)"""
    print("\n" + "="*80)
    print("BEST SETUPS (Win Rate > 60%, Min 5 Trades)")
    print("="*80)

    orb_times = ["0900", "1000", "1100", "1800", "2300", "0030"]
    orb_labels = {
        "0900": "09:00",
        "1000": "10:00",
        "1100": "11:00",
        "1800": "18:00",
        "2300": "23:00",
        "0030": "00:30",
    }

    best_setups = []

    # Check all ORB x Direction combinations
    for orb in orb_times:
        for direction in ["UP", "DOWN"]:
            rows = con.execute(f"""
                SELECT orb_{orb}_outcome, orb_{orb}_r_multiple
                FROM daily_features
                WHERE orb_{orb}_break_dir = ?
                  AND orb_{orb}_outcome IN ('WIN', 'LOSS')
            """, [direction]).fetchall()

            stats = calculate_stats(rows)
            if stats.total_trades >= 5 and stats.win_rate > 0.6:
                best_setups.append((f"{orb_labels[orb]} {direction}", stats))

    # Check ORB x Asia type combinations
    for orb in ["0900", "1000", "1100"]:
        for asia_type in ["TIGHT", "NORMAL", "EXPANDED"]:
            rows = con.execute(f"""
                SELECT orb_{orb}_outcome, orb_{orb}_r_multiple
                FROM daily_features
                WHERE asia_type = ?
                  AND orb_{orb}_outcome IN ('WIN', 'LOSS')
            """, [asia_type]).fetchall()

            stats = calculate_stats(rows)
            if stats.total_trades >= 5 and stats.win_rate > 0.6:
                best_setups.append((f"{orb_labels[orb]} on Asia {asia_type}", stats))

    # Sort by win rate
    best_setups.sort(key=lambda x: x[1].win_rate, reverse=True)

    if best_setups:
        for setup, stats in best_setups[:10]:  # Top 10
            print(f"\n{setup}:")
            print(f"  {stats}")
    else:
        print("\nNo setups found meeting criteria (try lowering thresholds)")


def analyze_worst_setups(con: duckdb.DuckDBPyConnection):
    """Find the worst performing setups (combinations with <40% win rate and >5 trades)"""
    print("\n" + "="*80)
    print("WORST SETUPS (Win Rate < 40%, Min 5 Trades) - AVOID THESE")
    print("="*80)

    orb_times = ["0900", "1000", "1100", "1800", "2300", "0030"]
    orb_labels = {
        "0900": "09:00",
        "1000": "10:00",
        "1100": "11:00",
        "1800": "18:00",
        "2300": "23:00",
        "0030": "00:30",
    }

    worst_setups = []

    # Check all ORB x Direction combinations
    for orb in orb_times:
        for direction in ["UP", "DOWN"]:
            rows = con.execute(f"""
                SELECT orb_{orb}_outcome, orb_{orb}_r_multiple
                FROM daily_features
                WHERE orb_{orb}_break_dir = ?
                  AND orb_{orb}_outcome IN ('WIN', 'LOSS')
            """, [direction]).fetchall()

            stats = calculate_stats(rows)
            if stats.total_trades >= 5 and stats.win_rate < 0.4:
                worst_setups.append((f"{orb_labels[orb]} {direction}", stats))

    # Sort by win rate (ascending)
    worst_setups.sort(key=lambda x: x[1].win_rate)

    if worst_setups:
        for setup, stats in worst_setups[:10]:  # Bottom 10
            print(f"\n{setup}:")
            print(f"  {stats}")
    else:
        print("\nNo setups found meeting criteria")


def main():
    con = duckdb.connect("gold.db")

    try:
        # Check data availability
        count = con.execute("SELECT COUNT(*) FROM daily_features").fetchone()[0]
        print(f"\nAnalyzing {count} days of data...")

        if count == 0:
            print("ERROR: No data in daily_features table. Run backfill first.")
            return

        # Run all analyses
        analyze_orb_by_time(con)
        analyze_orb_by_direction(con)
        analyze_orb_by_asia_type(con)
        analyze_orb_by_london_type(con)
        analyze_orb_by_ny_type(con)
        analyze_best_setups(con)
        analyze_worst_setups(con)

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)

    finally:
        con.close()


if __name__ == "__main__":
    main()
