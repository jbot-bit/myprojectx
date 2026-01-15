"""
ORB Setup Filter
================
Find specific ORB setups based on your criteria.

Usage examples:
  # Find all 10:00 DOWN breakouts
  python filter_orb_setups.py --orb 1000 --direction DOWN

  # Find 00:30 ORBs after NY SWEEP_HIGH
  python filter_orb_setups.py --orb 0030 --ny_type SWEEP_HIGH

  # Find 18:00 UP breakouts that won
  python filter_orb_setups.py --orb 1800 --direction UP --outcome WIN

  # Find Asia ORBs during EXPANDED sessions
  python filter_orb_setups.py --orb 0900 --asia_type EXPANDED

  # Show only winners from last 30 days
  python filter_orb_setups.py --outcome WIN --last_days 30
"""

import duckdb
import argparse
from datetime import date, timedelta
from typing import Optional, List


class ORBFilter:
    """Filter and display ORB setups matching specific criteria"""

    def __init__(self, db_path: str = "gold.db"):
        self.con = duckdb.connect(db_path)

    def filter_setups(
        self,
        orb_time: Optional[str] = None,  # 0900, 1000, 1100, 1800, 2300, 0030
        direction: Optional[str] = None,  # UP, DOWN
        outcome: Optional[str] = None,  # WIN, LOSS, NO_TRADE
        asia_type: Optional[str] = None,  # TIGHT, NORMAL, EXPANDED
        london_type: Optional[str] = None,  # CONSOLIDATION, SWEEP_HIGH, SWEEP_LOW, EXPANSION
        ny_type: Optional[str] = None,  # CONSOLIDATION, SWEEP_HIGH, SWEEP_LOW, EXPANSION
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_asia_range: Optional[float] = None,  # Min Asia range in ticks
        max_asia_range: Optional[float] = None,  # Max Asia range in ticks
        min_orb_size: Optional[float] = None,  # Min ORB size in ticks
        max_orb_size: Optional[float] = None,  # Max ORB size in ticks
    ) -> List[dict]:
        """
        Filter setups based on criteria.
        Returns list of matching days with details.
        """

        # Build WHERE clause dynamically
        where_clauses = []
        params = []

        # Date filters
        if start_date:
            where_clauses.append("date_local >= ?")
            params.append(start_date)
        if end_date:
            where_clauses.append("date_local <= ?")
            params.append(end_date)

        # Session type filters
        if asia_type:
            where_clauses.append("asia_type = ?")
            params.append(asia_type)
        if london_type:
            where_clauses.append("london_type = ?")
            params.append(london_type)
        if ny_type:
            where_clauses.append("ny_type = ?")
            params.append(ny_type)

        # Asia range filters
        if min_asia_range is not None:
            where_clauses.append("(asia_range / 0.1) >= ?")
            params.append(min_asia_range)
        if max_asia_range is not None:
            where_clauses.append("(asia_range / 0.1) <= ?")
            params.append(max_asia_range)

        # ORB-specific filters (if ORB time specified)
        if orb_time:
            if direction:
                where_clauses.append(f"orb_{orb_time}_break_dir = ?")
                params.append(direction)
            if outcome:
                where_clauses.append(f"orb_{orb_time}_outcome = ?")
                params.append(outcome)
            if min_orb_size is not None:
                where_clauses.append(f"(orb_{orb_time}_size / 0.1) >= ?")
                params.append(min_orb_size)
            if max_orb_size is not None:
                where_clauses.append(f"(orb_{orb_time}_size / 0.1) <= ?")
                params.append(max_orb_size)

            # Ensure ORB data exists
            where_clauses.append(f"orb_{orb_time}_break_dir IS NOT NULL")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Select columns based on ORB time
        if orb_time:
            orb_cols = f"""
                orb_{orb_time}_high AS orb_high,
                orb_{orb_time}_low AS orb_low,
                orb_{orb_time}_size AS orb_size,
                orb_{orb_time}_break_dir AS orb_dir,
                orb_{orb_time}_outcome AS orb_outcome,
                orb_{orb_time}_r_multiple AS orb_r
            """
        else:
            orb_cols = "NULL AS orb_high, NULL AS orb_low, NULL AS orb_size, NULL AS orb_dir, NULL AS orb_outcome, NULL AS orb_r"

        query = f"""
            SELECT
                date_local,
                asia_high,
                asia_low,
                asia_range,
                asia_type,
                london_type,
                ny_type,
                atr_20,
                {orb_cols}
            FROM daily_features
            WHERE {where_sql}
            ORDER BY date_local DESC
        """

        rows = self.con.execute(query, params).fetchall()

        # Convert to list of dicts
        results = []
        for row in rows:
            results.append({
                "date": row[0],
                "asia_high": row[1],
                "asia_low": row[2],
                "asia_range": row[3],
                "asia_range_ticks": row[3] / 0.1 if row[3] else None,
                "asia_type": row[4],
                "london_type": row[5],
                "ny_type": row[6],
                "atr_20": row[7],
                "orb_high": row[8],
                "orb_low": row[9],
                "orb_size": row[10],
                "orb_size_ticks": row[10] / 0.1 if row[10] else None,
                "orb_dir": row[11],
                "orb_outcome": row[12],
                "orb_r": row[13],
            })

        return results

    def display_results(self, results: List[dict], orb_time: Optional[str] = None):
        """Pretty print results"""
        if not results:
            print("\nNo setups found matching your criteria.")
            return

        print(f"\nFound {len(results)} matching setups:\n")
        print("=" * 120)

        orb_label = {
            "0900": "09:00",
            "1000": "10:00",
            "1100": "11:00",
            "1800": "18:00",
            "2300": "23:00",
            "0030": "00:30",
        }

        for r in results:
            print(f"\nDate: {r['date']}")

            asia_ticks_str = f"{r['asia_range_ticks']:.0f}" if r['asia_range_ticks'] else "N/A"
            atr_str = f"{r['atr_20']:.2f}" if r['atr_20'] else "N/A"
            print(f"  Asia: {asia_ticks_str} ticks ({r['asia_type']}) | ATR_20: {atr_str}")
            print(f"  London: {r['london_type']} | NY: {r['ny_type']}")

            if orb_time and r['orb_high']:
                orb_name = orb_label.get(orb_time, orb_time)
                orb_ticks_str = f"{r['orb_size_ticks']:.0f}" if r['orb_size_ticks'] else "N/A"
                print(f"  ORB {orb_name}: {orb_ticks_str} ticks ({r['orb_high']:.1f}-{r['orb_low']:.1f})")
                r_str = f"{r['orb_r']:+.1f}" if r['orb_r'] is not None else "N/A"
                print(f"    Direction: {r['orb_dir']} | Outcome: {r['orb_outcome']} | R: {r_str}")

        print("\n" + "=" * 120)

    def close(self):
        self.con.close()


def main():
    parser = argparse.ArgumentParser(
        description="Filter ORB setups by criteria",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Best performing setups (from analysis)
  python filter_orb_setups.py --orb 1000 --direction DOWN
  python filter_orb_setups.py --orb 1800 --direction UP

  # Find 00:30 ORBs after specific NY session types
  python filter_orb_setups.py --orb 0030 --ny_type SWEEP_HIGH
  python filter_orb_setups.py --orb 0030 --ny_type EXPANSION

  # Find Asia ORBs during EXPANDED sessions
  python filter_orb_setups.py --orb 0900 --asia_type EXPANDED
  python filter_orb_setups.py --orb 1000 --asia_type EXPANDED

  # Find all winners in last 30 days
  python filter_orb_setups.py --orb 1000 --outcome WIN --last_days 30

  # Find tight ORBs (< 50 ticks) that won
  python filter_orb_setups.py --orb 1000 --outcome WIN --max_orb_size 50

  # Find days with large Asia range (> 400 ticks)
  python filter_orb_setups.py --min_asia_range 400
        """
    )

    parser.add_argument("--orb", choices=["0900", "1000", "1100", "1800", "2300", "0030"],
                        help="ORB time to filter")
    parser.add_argument("--direction", choices=["UP", "DOWN"],
                        help="Break direction")
    parser.add_argument("--outcome", choices=["WIN", "LOSS", "NO_TRADE"],
                        help="Trade outcome")
    parser.add_argument("--asia_type", choices=["TIGHT", "NORMAL", "EXPANDED"],
                        help="Asia session type")
    parser.add_argument("--london_type", choices=["CONSOLIDATION", "SWEEP_HIGH", "SWEEP_LOW", "EXPANSION"],
                        help="London session type")
    parser.add_argument("--ny_type", choices=["CONSOLIDATION", "SWEEP_HIGH", "SWEEP_LOW", "EXPANSION"],
                        help="NY session type")
    parser.add_argument("--start_date", type=str,
                        help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str,
                        help="End date (YYYY-MM-DD)")
    parser.add_argument("--last_days", type=int,
                        help="Filter to last N days")
    parser.add_argument("--min_asia_range", type=float,
                        help="Minimum Asia range in ticks")
    parser.add_argument("--max_asia_range", type=float,
                        help="Maximum Asia range in ticks")
    parser.add_argument("--min_orb_size", type=float,
                        help="Minimum ORB size in ticks")
    parser.add_argument("--max_orb_size", type=float,
                        help="Maximum ORB size in ticks")

    args = parser.parse_args()

    # Parse dates
    start_date = None
    end_date = None

    if args.last_days:
        end_date = date.today()
        start_date = end_date - timedelta(days=args.last_days)
    else:
        if args.start_date:
            start_date = date.fromisoformat(args.start_date)
        if args.end_date:
            end_date = date.fromisoformat(args.end_date)

    # Run filter
    filter = ORBFilter()
    try:
        results = filter.filter_setups(
            orb_time=args.orb,
            direction=args.direction,
            outcome=args.outcome,
            asia_type=args.asia_type,
            london_type=args.london_type,
            ny_type=args.ny_type,
            start_date=start_date,
            end_date=end_date,
            min_asia_range=args.min_asia_range,
            max_asia_range=args.max_asia_range,
            min_orb_size=args.min_orb_size,
            max_orb_size=args.max_orb_size,
        )

        filter.display_results(results, args.orb)

    finally:
        filter.close()


if __name__ == "__main__":
    main()
