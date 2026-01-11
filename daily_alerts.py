"""
Daily Setup Alerts
==================
Analyzes today's session characteristics and recommends high-probability ORB setups.

Usage:
  python daily_alerts.py           # Analyze today
  python daily_alerts.py 2026-01-10   # Analyze specific date

Based on historical performance analysis, this script identifies:
- Best ORB times to trade based on current session conditions
- ORB setups to avoid
- Asia/London/NY session context
"""

import duckdb
import sys
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SetupRecommendation:
    """Recommendation for an ORB setup"""
    orb_time: str
    orb_label: str
    direction: Optional[str]
    reason: str
    historical_wr: float
    historical_avg_r: float
    confidence: str  # HIGH, MEDIUM, LOW
    sample_size: int


class DailyAlertSystem:
    """Analyze daily session and recommend ORB setups"""

    ORB_LABELS = {
        "0900": "09:00 (Asia Open)",
        "1000": "10:00 (Asia Mid)",
        "1100": "11:00 (Asia Late)",
        "1800": "18:00 (London Open)",
        "2300": "23:00 (NY Open)",
        "0030": "00:30 (NYSE)",
    }

    def __init__(self, db_path: str = "gold.db"):
        self.con = duckdb.connect(db_path, read_only=True)

    def get_today_features(self, target_date: date) -> Optional[Dict]:
        """Get features for target date"""
        query = """
            SELECT
                date_local,
                asia_high,
                asia_low,
                asia_range,
                ((asia_high-asia_low)/0.10) AS asia_ticks,
                asia_type,
                london_type,
                ny_type,
                atr_20
            FROM daily_features
            WHERE date_local = ?
        """
        row = self.con.execute(query, [target_date]).fetchone()

        if not row:
            return None

        return {
            "date": row[0],
            "asia_high": row[1],
            "asia_low": row[2],
            "asia_range": row[3],
            "asia_ticks": row[4],
            "asia_type": row[5],
            "london_type": row[6],
            "ny_type": row[7],
            "atr_20": row[8],
        }

    def get_historical_performance(
        self,
        orb_time: str,
        direction: Optional[str] = None,
        asia_type: Optional[str] = None,
        london_type: Optional[str] = None,
        ny_type: Optional[str] = None,
    ) -> Tuple[float, float, int]:
        """
        Get historical win rate and avg R for specific conditions.
        Returns (win_rate, avg_r, sample_size)
        """
        conditions = [f"orb_{orb_time}_outcome IN ('WIN', 'LOSS')"]
        params = []

        if direction:
            conditions.append(f"orb_{orb_time}_break_dir = ?")
            params.append(direction)
        if asia_type and asia_type != "NO_DATA":
            conditions.append("asia_type = ?")
            params.append(asia_type)
        if london_type and london_type != "NO_DATA":
            conditions.append("london_type = ?")
            params.append(london_type)
        if ny_type and ny_type != "NO_DATA":
            conditions.append("ny_type = ?")
            params.append(ny_type)

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT
                COUNT(*) AS total_trades,
                SUM(CASE WHEN orb_{orb_time}_outcome = 'WIN' THEN 1 ELSE 0 END) AS wins,
                AVG(orb_{orb_time}_r_multiple) AS avg_r
            FROM daily_features
            WHERE {where_clause}
        """

        row = self.con.execute(query, params).fetchone()
        total_trades = row[0] or 0
        wins = row[1] or 0
        avg_r = row[2] or 0.0

        win_rate = wins / total_trades if total_trades > 0 else 0.0

        return win_rate, avg_r, total_trades

    def analyze_orb(
        self,
        orb_time: str,
        today_features: Dict,
        min_sample_size: int = 5,
    ) -> List[SetupRecommendation]:
        """Analyze a specific ORB time and generate recommendations"""
        recommendations = []

        asia_type = today_features.get("asia_type")
        london_type = today_features.get("london_type")
        ny_type = today_features.get("ny_type")

        # Determine which session types are relevant for this ORB
        relevant_filters = {}
        if orb_time in ["0900", "1000", "1100"]:
            # Asia ORBs - filter by Asia type
            if asia_type and asia_type != "NO_DATA":
                relevant_filters["asia_type"] = asia_type
        elif orb_time in ["1800", "2300", "0030"]:
            # London/NY ORBs - filter by London and/or NY type
            if london_type and london_type != "NO_DATA":
                relevant_filters["london_type"] = london_type
            if orb_time in ["2300", "0030"] and ny_type and ny_type != "NO_DATA":
                relevant_filters["ny_type"] = ny_type

        # Check directional bias (UP vs DOWN)
        for direction in ["UP", "DOWN"]:
            wr, avg_r, sample_size = self.get_historical_performance(
                orb_time,
                direction=direction,
                **relevant_filters
            )

            if sample_size < min_sample_size:
                continue

            # Determine confidence level
            if sample_size >= 50:
                confidence = "HIGH"
            elif sample_size >= 20:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"

            # Generate recommendation if edge exists
            if wr > 0.55 and avg_r > 0.05:
                reason_parts = [f"{direction} breakouts"]
                if "asia_type" in relevant_filters:
                    reason_parts.append(f"during Asia {relevant_filters['asia_type']}")
                if "london_type" in relevant_filters:
                    reason_parts.append(f"after London {relevant_filters['london_type']}")
                if "ny_type" in relevant_filters:
                    reason_parts.append(f"during NY {relevant_filters['ny_type']}")

                reason = " ".join(reason_parts)

                recommendations.append(SetupRecommendation(
                    orb_time=orb_time,
                    orb_label=self.ORB_LABELS[orb_time],
                    direction=direction,
                    reason=reason,
                    historical_wr=wr,
                    historical_avg_r=avg_r,
                    confidence=confidence,
                    sample_size=sample_size,
                ))

        # Also check overall performance (no directional bias)
        wr, avg_r, sample_size = self.get_historical_performance(
            orb_time,
            **relevant_filters
        )

        if sample_size >= min_sample_size and wr > 0.53 and avg_r > 0.05:
            if not recommendations:  # Only add if no directional edge found
                reason_parts = ["Any breakout"]
                if "asia_type" in relevant_filters:
                    reason_parts.append(f"during Asia {relevant_filters['asia_type']}")
                if "london_type" in relevant_filters:
                    reason_parts.append(f"after London {relevant_filters['london_type']}")
                if "ny_type" in relevant_filters:
                    reason_parts.append(f"during NY {relevant_filters['ny_type']}")

                reason = " ".join(reason_parts)

                confidence = "MEDIUM" if sample_size >= 20 else "LOW"

                recommendations.append(SetupRecommendation(
                    orb_time=orb_time,
                    orb_label=self.ORB_LABELS[orb_time],
                    direction=None,
                    reason=reason,
                    historical_wr=wr,
                    historical_avg_r=avg_r,
                    confidence=confidence,
                    sample_size=sample_size,
                ))

        return recommendations

    def generate_daily_alert(self, target_date: date) -> None:
        """Generate and print daily alert for target date"""
        today_features = self.get_today_features(target_date)

        if not today_features:
            print(f"\nNo data available for {target_date}")
            print("Run: python build_daily_features.py {target_date.strftime('%Y-%m-%d')}")
            return

        # Print header
        print("\n" + "="*80)
        print(f"DAILY SETUP ALERTS - {target_date.strftime('%A, %B %d, %Y')}")
        print("="*80)

        # Print session context
        print("\nSESSION CONTEXT:")
        asia_ticks = f"{today_features['asia_ticks']:.0f}" if today_features['asia_ticks'] else "N/A"
        atr = f"{today_features['atr_20']:.2f}" if today_features['atr_20'] else "N/A"
        print(f"  Asia Range: {asia_ticks} ticks ({today_features['asia_type']})")
        print(f"  London Session: {today_features['london_type']}")
        print(f"  NY Session: {today_features['ny_type']}")
        print(f"  ATR(20): {atr}")

        # Analyze all ORBs
        all_recommendations = []
        for orb_time in ["0900", "1000", "1100", "1800", "2300", "0030"]:
            recs = self.analyze_orb(orb_time, today_features)
            all_recommendations.extend(recs)

        # Sort by avg_r (best first)
        all_recommendations.sort(key=lambda x: x.historical_avg_r, reverse=True)

        # Display recommendations
        if all_recommendations:
            print("\n" + "="*80)
            print("HIGH-PROBABILITY SETUPS (WATCH FOR THESE):")
            print("="*80)

            for i, rec in enumerate(all_recommendations, 1):
                direction_str = f"{rec.direction} breakout" if rec.direction else "Both directions"
                print(f"\n{i}. {rec.orb_label} - {direction_str}")
                print(f"   Reason: {rec.reason}")
                print(f"   Historical: WR={rec.historical_wr:.1%} | Avg R={rec.historical_avg_r:+.2f} | Samples={rec.sample_size}")
                print(f"   Confidence: {rec.confidence}")
        else:
            print("\n" + "="*80)
            print("NO HIGH-PROBABILITY SETUPS FOUND")
            print("="*80)
            print("\nNo historical edge detected for today's session conditions.")
            print("Consider sitting out or trading with reduced size.")

        # Check for setups to avoid (poor historical performance)
        print("\n" + "="*80)
        print("SETUPS TO AVOID:")
        print("="*80)

        avoid_found = False
        for orb_time in ["0900", "1000", "1100", "1800", "2300", "0030"]:
            # Check if this ORB has historically poor performance
            asia_type = today_features.get("asia_type")
            london_type = today_features.get("london_type")
            ny_type = today_features.get("ny_type")

            relevant_filters = {}
            if orb_time in ["0900", "1000", "1100"] and asia_type != "NO_DATA":
                relevant_filters["asia_type"] = asia_type
            elif orb_time in ["1800", "2300", "0030"]:
                if london_type != "NO_DATA":
                    relevant_filters["london_type"] = london_type
                if orb_time in ["2300", "0030"] and ny_type != "NO_DATA":
                    relevant_filters["ny_type"] = ny_type

            wr, avg_r, sample_size = self.get_historical_performance(
                orb_time,
                **relevant_filters
            )

            if sample_size >= 10 and (wr < 0.42 or avg_r < -0.10):
                avoid_found = True
                print(f"\n  {self.ORB_LABELS[orb_time]}")
                print(f"    Historical: WR={wr:.1%} | Avg R={avg_r:+.2f} | Samples={sample_size}")
                print(f"    Reason: Poor historical performance in these conditions")

        if not avoid_found:
            print("\n  None - All ORBs have neutral or positive historical performance")

        print("\n" + "="*80)
        print("DISCLAIMER: Past performance does not guarantee future results.")
        print("Use this as ONE input in your trading decision process.")
        print("="*80 + "\n")

    def close(self):
        self.con.close()


def main():
    # Parse target date from command line
    if len(sys.argv) > 1:
        target_date = date.fromisoformat(sys.argv[1])
    else:
        # Default to today
        target_date = date.today()

    alert_system = DailyAlertSystem()
    try:
        alert_system.generate_daily_alert(target_date)
    finally:
        alert_system.close()


if __name__ == "__main__":
    main()
