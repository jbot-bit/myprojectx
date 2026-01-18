"""
CSV Chart Analyzer - FREE chart analysis from TradingView CSV exports

Analyzes OHLCV CSV data to detect ORBs, calculate indicators, and recommend strategies.
NO API COSTS - Pure Python analysis.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pytz
from io import StringIO, BytesIO

from config import TZ_LOCAL, ORB_TIMES
from setup_detector import SetupDetector

logger = logging.getLogger(__name__)


class CSVChartAnalyzer:
    """Analyzes trading charts from CSV data exports (TradingView format)."""

    def __init__(self, instrument: str = "MGC"):
        """
        Initialize CSV chart analyzer.

        Args:
            instrument: Trading instrument (MGC, NQ, MPL)
        """
        self.instrument = instrument
        self.setup_detector = SetupDetector(instrument=instrument)

    def analyze_csv(self, csv_data: bytes) -> Optional[Dict]:
        """
        Analyze chart data from CSV file.

        Expected CSV format (TradingView export):
        time,open,high,low,close,volume
        2024-01-15 09:00,2650.0,2652.0,2649.5,2651.5,1234

        Args:
            csv_data: CSV file bytes

        Returns:
            Dictionary with analysis results or None if error
        """
        try:
            # Read CSV
            df = pd.read_csv(BytesIO(csv_data))

            # Validate columns
            required_cols = ['time', 'open', 'high', 'low', 'close']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"CSV missing required columns. Got: {df.columns.tolist()}")
                return None

            # Parse timestamps
            df['time'] = pd.to_datetime(df['time'])

            # Sort by time
            df = df.sort_values('time')

            if df.empty:
                logger.error("CSV is empty")
                return None

            # Perform analysis
            analysis = {
                "success": True,
                "data_summary": self._analyze_data_summary(df),
                "current_state": self._analyze_current_state(df),
                "orb_analysis": self._detect_orbs(df),
                "indicators": self._calculate_indicators(df),
                "market_structure": self._analyze_structure(df),
                "session_context": self._determine_session(df),
                "raw_data": df
            }

            return analysis

        except Exception as e:
            logger.error(f"CSV analysis failed: {e}")
            return None

    def _analyze_data_summary(self, df: pd.DataFrame) -> Dict:
        """Analyze basic data summary."""
        return {
            "total_bars": len(df),
            "start_time": df['time'].iloc[0],
            "end_time": df['time'].iloc[-1],
            "duration_hours": (df['time'].iloc[-1] - df['time'].iloc[0]).total_seconds() / 3600,
            "price_range": {
                "high": df['high'].max(),
                "low": df['low'].min(),
                "range": df['high'].max() - df['low'].min()
            }
        }

    def _analyze_current_state(self, df: pd.DataFrame) -> Dict:
        """Analyze current price state."""
        latest = df.iloc[-1]

        return {
            "current_price": latest['close'],
            "current_time": latest['time'],
            "open": latest['open'],
            "high": latest['high'],
            "low": latest['low'],
            "volume": latest.get('volume', None)
        }

    def _detect_orbs(self, df: pd.DataFrame) -> Dict:
        """
        Detect Opening Range Breakouts in the data.

        Looks for 5-minute windows at standard ORB times.
        """
        orb_results = {}

        # Try to detect each ORB time
        for orb_info in ORB_TIMES:
            orb_name = orb_info["name"]
            orb_hour = orb_info["hour"]
            orb_min = orb_info["min"]

            # Find bars in the ORB window (5 minutes)
            orb_bars = df[
                (df['time'].dt.hour == orb_hour) &
                (df['time'].dt.minute >= orb_min) &
                (df['time'].dt.minute < orb_min + 5)
            ]

            if not orb_bars.empty:
                orb_high = orb_bars['high'].max()
                orb_low = orb_bars['low'].min()
                orb_size = orb_high - orb_low

                # Get latest price to determine position
                latest_price = df['close'].iloc[-1]

                if latest_price > orb_high:
                    position = "ABOVE"
                    potential_direction = "LONG"
                elif latest_price < orb_low:
                    position = "BELOW"
                    potential_direction = "SHORT"
                else:
                    position = "INSIDE"
                    potential_direction = "WAIT"

                orb_results[orb_name] = {
                    "detected": True,
                    "high": orb_high,
                    "low": orb_low,
                    "size": orb_size,
                    "midpoint": (orb_high + orb_low) / 2,
                    "price_position": position,
                    "potential_direction": potential_direction,
                    "bars_count": len(orb_bars)
                }
            else:
                orb_results[orb_name] = {
                    "detected": False,
                    "note": f"No bars found for {orb_name} ORB window"
                }

        return orb_results

    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate technical indicators."""
        indicators = {}

        # ATR (14-period on close prices as approximation)
        if len(df) >= 14:
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift())
            low_close = abs(df['low'] - df['close'].shift())

            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)

            atr_14 = true_range.rolling(window=14).mean().iloc[-1]
            indicators['atr_14'] = atr_14
        else:
            indicators['atr_14'] = None

        # ATR (20-period - our standard)
        if len(df) >= 20:
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift())
            low_close = abs(df['low'] - df['close'].shift())

            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)

            atr_20 = true_range.rolling(window=20).mean().iloc[-1]
            indicators['atr_20'] = atr_20
        else:
            indicators['atr_20'] = None

        # RSI (14-period)
        if len(df) >= 14:
            close_delta = df['close'].diff()
            gain = (close_delta.where(close_delta > 0, 0)).rolling(window=14).mean()
            loss = (-close_delta.where(close_delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            indicators['rsi_14'] = rsi.iloc[-1]
        else:
            indicators['rsi_14'] = None

        # Recent volatility (last 20 bars)
        if len(df) >= 20:
            recent_bars = df.tail(20)
            indicators['recent_volatility'] = recent_bars['close'].std()
        else:
            indicators['recent_volatility'] = None

        return indicators

    def _analyze_structure(self, df: pd.DataFrame) -> Dict:
        """Analyze market structure."""
        if len(df) < 10:
            return {"note": "Insufficient data for structure analysis"}

        # Get recent price action (last 50 bars or all if less)
        recent = df.tail(min(50, len(df)))

        # Calculate trend
        first_price = recent['close'].iloc[0]
        last_price = recent['close'].iloc[-1]
        price_change = last_price - first_price
        price_change_pct = (price_change / first_price) * 100

        if abs(price_change_pct) < 0.5:
            trend = "RANGING"
        elif price_change > 0:
            trend = "TRENDING_UP"
        else:
            trend = "TRENDING_DOWN"

        # Find support/resistance levels (recent swing highs/lows)
        swing_highs = recent['high'].rolling(window=5, center=True).max()
        swing_lows = recent['low'].rolling(window=5, center=True).min()

        # Get unique levels (within 0.5% tolerance)
        resistance_levels = swing_highs[swing_highs == recent['high']].unique()
        support_levels = swing_lows[swing_lows == recent['low']].unique()

        return {
            "trend": trend,
            "price_change": price_change,
            "price_change_pct": price_change_pct,
            "recent_high": recent['high'].max(),
            "recent_low": recent['low'].min(),
            "resistance_levels": resistance_levels[:3].tolist() if len(resistance_levels) > 0 else [],
            "support_levels": support_levels[:3].tolist() if len(support_levels) > 0 else []
        }

    def _determine_session(self, df: pd.DataFrame) -> Dict:
        """Determine current trading session."""
        latest_time = df['time'].iloc[-1]

        # Assume UTC timestamps, convert to Brisbane time
        if latest_time.tzinfo is None:
            latest_time = latest_time.tz_localize('UTC')

        local_time = latest_time.astimezone(TZ_LOCAL)
        hour = local_time.hour

        if 9 <= hour < 18:
            session = "ASIA"
        elif 18 <= hour < 23:
            session = "LONDON"
        else:
            session = "NY"

        return {
            "session": session,
            "local_time": local_time,
            "hour": hour
        }

    def recommend_strategies(self, analysis: Dict, top_n: int = 5) -> List[Dict]:
        """
        Recommend strategies based on CSV analysis.

        Args:
            analysis: CSV analysis dictionary
            top_n: Number of top strategies to return

        Returns:
            List of strategy recommendations
        """
        if not analysis or not analysis.get("success"):
            return []

        recommendations = []

        try:
            # Get all validated setups
            all_setups = self.setup_detector.get_all_validated_setups(self.instrument)

            if not all_setups:
                logger.warning(f"No validated setups found for {self.instrument}")
                return []

            # Get analysis components
            current_state = analysis.get("current_state", {})
            orb_analysis = analysis.get("orb_analysis", {})
            indicators = analysis.get("indicators", {})
            session = analysis.get("session_context", {}).get("session")

            # Score and rank setups
            for setup in all_setups:
                score = self._score_setup_csv(setup, current_state, orb_analysis, indicators, session)

                if score > 0:
                    reasoning = self._generate_reasoning_csv(setup, current_state, orb_analysis, indicators, session)

                    recommendations.append({
                        "setup": setup,
                        "score": score,
                        "reasoning": reasoning
                    })

            # Sort by score (descending)
            recommendations.sort(key=lambda x: x["score"], reverse=True)

            # Return top N
            return recommendations[:top_n]

        except Exception as e:
            logger.error(f"Failed to recommend strategies: {e}")
            return []

    def _score_setup_csv(self, setup: Dict, current_state: Dict, orb_analysis: Dict, indicators: Dict, session: str) -> float:
        """Score a setup based on CSV analysis."""
        score = 0.0

        # Base score from tier
        tier_scores = {"S+": 50, "S": 40, "A": 30, "B": 20, "C": 10}
        score += tier_scores.get(setup.get("tier", "C"), 10)

        # Bonus for expectancy
        avg_r = setup.get("avg_r", 0)
        if avg_r > 0.4:
            score += 15
        elif avg_r > 0.3:
            score += 10
        elif avg_r > 0.2:
            score += 5

        # Bonus for high win rate
        win_rate = setup.get("win_rate", 0)
        if win_rate > 50:
            score += 10
        elif win_rate > 40:
            score += 5

        # Session match bonus
        orb_time = setup.get("orb_time", "")
        if session:
            if orb_time in ["0900", "1000", "1100"] and session == "ASIA":
                score += 15
            elif orb_time == "1800" and session == "LONDON":
                score += 15
            elif orb_time in ["2300", "0030"] and session == "NY":
                score += 15

        # Check if ORB is detected for this setup
        orb_data = orb_analysis.get(orb_time, {})
        if orb_data.get("detected"):
            score += 20  # Big bonus for detected ORB

            # Check filter pass (if setup has filter)
            orb_filter = setup.get("orb_size_filter")
            atr_20 = indicators.get("atr_20")

            if orb_filter and atr_20:
                orb_size = orb_data.get("size", 0)
                ratio = orb_size / atr_20
                if ratio < orb_filter:
                    score += 20  # PASSES filter
                else:
                    score -= 10  # FAILS filter (penalize)

            # Bonus for price position
            position = orb_data.get("price_position")
            if position in ["ABOVE", "BELOW"]:
                score += 10  # Price already outside = setup active
            elif position == "INSIDE":
                score += 5  # Preparing for breakout

        return score

    def _generate_reasoning_csv(self, setup: Dict, current_state: Dict, orb_analysis: Dict, indicators: Dict, session: str) -> str:
        """Generate reasoning for CSV-based recommendation."""
        reasons = []

        # Setup quality
        tier = setup.get("tier", "C")
        win_rate = setup.get("win_rate", 0)
        avg_r = setup.get("avg_r", 0)
        annual_trades = setup.get("annual_trades", 0)

        reasons.append(f"{tier} tier ({win_rate:.1f}% WR, +{avg_r:.2f}R avg)")

        # Session
        if session:
            reasons.append(f"{session} session match")

        # ORB detection
        orb_time = setup.get("orb_time", "")
        orb_data = orb_analysis.get(orb_time, {})

        if orb_data.get("detected"):
            orb_size = orb_data.get("size", 0)
            position = orb_data.get("price_position", "")
            reasons.append(f"ORB detected ({orb_size:.2f} pts, price {position})")

            # Filter check
            orb_filter = setup.get("orb_size_filter")
            atr_20 = indicators.get("atr_20")

            if orb_filter and atr_20:
                ratio = orb_size / atr_20
                if ratio < orb_filter:
                    reasons.append(f"Filter PASSED ({ratio:.3f} < {orb_filter:.3f})")
                else:
                    reasons.append(f"Filter FAILED ({ratio:.3f} > {orb_filter:.3f})")
            else:
                reasons.append("No filter (trades all ORBs)")

            # Direction
            direction = orb_data.get("potential_direction")
            if direction != "WAIT":
                reasons.append(f"Setup: {direction} breakout")
        else:
            reasons.append("ORB not in data range")

        # Expectancy
        annual_exp = avg_r * annual_trades
        reasons.append(f"+{annual_exp:.0f}R/year expectancy")

        return " | ".join(reasons)


def analyze_csv_and_recommend(csv_data: bytes, instrument: str = "MGC", top_n: int = 5) -> Tuple[Optional[Dict], List[Dict]]:
    """
    Convenience function to analyze CSV and recommend strategies.

    Args:
        csv_data: CSV file bytes
        instrument: Trading instrument
        top_n: Number of recommendations

    Returns:
        Tuple of (analysis dict, recommendations list)
    """
    analyzer = CSVChartAnalyzer(instrument=instrument)

    analysis = analyzer.analyze_csv(csv_data)
    recommendations = analyzer.recommend_strategies(analysis, top_n) if analysis else []

    return analysis, recommendations
