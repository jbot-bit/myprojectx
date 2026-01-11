"""
AI Query Interface
==================
Natural language interface to query MGC trading data.

This tool interprets your questions and queries the database intelligently.

Usage:
  python ai_query.py "What was the win rate for 11:00 UP breakouts?"
  python ai_query.py "Show me the best performing ORBs"
  python ai_query.py "How many days had Asia EXPANDED sessions?"
  python ai_query.py "What's the avg R for 18:00 after London CONSOLIDATION?"

Features:
- Natural language question parsing
- Intelligent query generation
- Context-aware responses
- Multi-turn conversations (interactive mode)
"""

import duckdb
import sqlite3
import argparse
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import date, timedelta


class AIQueryEngine:
    """
    Natural language query engine for MGC trading data.
    Interprets questions and executes appropriate queries.
    """

    def __init__(self, mgc_db_path: str = "gold.db", journal_db_path: str = "trades.db"):
        self.mgc_db_path = mgc_db_path
        self.journal_db_path = journal_db_path

        # Pattern matching for common queries
        self.patterns = [
            # Win rate queries
            {
                "pattern": r"(?:win rate|winrate|wr).*?(\d{4})\s*(up|down)?",
                "handler": self._handle_win_rate_query,
                "description": "Query win rates for specific ORB setups"
            },
            # Performance queries
            {
                "pattern": r"(?:best|top|highest).*?(?:orb|setup|strategy)",
                "handler": self._handle_best_setups_query,
                "description": "Find best performing setups"
            },
            {
                "pattern": r"(?:worst|bottom|lowest).*?(?:orb|setup|strategy)",
                "handler": self._handle_worst_setups_query,
                "description": "Find worst performing setups"
            },
            # Session queries
            {
                "pattern": r"(?:how many|count).*?(?:asia|london|ny).*?(tight|normal|expanded|consolidation|sweep|expansion)",
                "handler": self._handle_session_count_query,
                "description": "Count session types"
            },
            # Average R queries
            {
                "pattern": r"(?:avg|average)\s*r.*?(\d{4})\s*(up|down)?",
                "handler": self._handle_avg_r_query,
                "description": "Query average R for setups"
            },
            # Recent performance
            {
                "pattern": r"(?:recent|last|past)\s*(\d+)?\s*(?:days?|trades?)",
                "handler": self._handle_recent_query,
                "description": "Query recent performance"
            },
            # Specific date queries
            {
                "pattern": r"(\d{4}-\d{2}-\d{2})",
                "handler": self._handle_date_query,
                "description": "Query specific date"
            },
            # Journal queries
            {
                "pattern": r"(?:my|journal|personal).*?(?:trades?|performance|stats)",
                "handler": self._handle_journal_query,
                "description": "Query your trading journal"
            },
            # Comparison queries
            {
                "pattern": r"compare.*?(\d{4}).*?(?:vs|versus|against|with).*?(\d{4})",
                "handler": self._handle_comparison_query,
                "description": "Compare two setups"
            },
        ]

    def _parse_orb_time(self, text: str) -> Optional[str]:
        """Extract ORB time from text"""
        # Look for 4-digit times
        match = re.search(r'(\d{4})', text)
        if match:
            return match.group(1)

        # Look for text representations
        time_map = {
            "nine": "0900", "9am": "0900", "9:00": "0900",
            "ten": "1000", "10am": "1000", "10:00": "1000",
            "eleven": "1100", "11am": "1100", "11:00": "1100",
            "eighteen": "1800", "6pm": "1800", "18:00": "1800",
            "twenty-three": "2300", "23:00": "2300", "11pm": "2300",
            "midnight": "0030", "00:30": "0030", "12:30am": "0030",
        }

        text_lower = text.lower()
        for key, val in time_map.items():
            if key in text_lower:
                return val

        return None

    def _parse_direction(self, text: str) -> Optional[str]:
        """Extract direction from text"""
        text_lower = text.lower()
        if "up" in text_lower or "bullish" in text_lower or "long" in text_lower:
            return "UP"
        elif "down" in text_lower or "bearish" in text_lower or "short" in text_lower:
            return "DOWN"
        return None

    def _handle_win_rate_query(self, question: str, match) -> str:
        """Handle win rate queries"""
        orb_time = match.group(1)
        direction = match.group(2).upper() if match.group(2) else None

        con = duckdb.connect(self.mgc_db_path, read_only=True)
        try:
            conditions = [f"orb_{orb_time}_outcome IN ('WIN', 'LOSS')"]
            params = []

            if direction:
                conditions.append(f"orb_{orb_time}_break_dir = ?")
                params.append(direction)

            where_clause = " AND ".join(conditions)

            result = con.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN orb_{orb_time}_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    AVG(orb_{orb_time}_r_multiple) as avg_r
                FROM daily_features
                WHERE {where_clause}
            """, params).fetchone()

            total, wins, avg_r = result
            win_rate = wins / total if total > 0 else 0

            setup = f"{orb_time} {direction}" if direction else orb_time
            return (f"**{setup} ORB Performance:**\n"
                   f"  Win Rate: {win_rate:.1%}\n"
                   f"  Total Trades: {total}\n"
                   f"  Wins: {wins}\n"
                   f"  Average R: {avg_r:+.2f}")

        finally:
            con.close()

    def _handle_best_setups_query(self, question: str, match) -> str:
        """Handle best setups queries"""
        con = duckdb.connect(self.mgc_db_path, read_only=True)
        try:
            # Find best setups by average R
            results = con.execute("""
                WITH setup_stats AS (
                    SELECT '0900' as orb, orb_0900_break_dir as dir, orb_0900_outcome as outcome, orb_0900_r_multiple as r FROM daily_features WHERE orb_0900_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '1000', orb_1000_break_dir, orb_1000_outcome, orb_1000_r_multiple FROM daily_features WHERE orb_1000_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '1100', orb_1100_break_dir, orb_1100_outcome, orb_1100_r_multiple FROM daily_features WHERE orb_1100_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '1800', orb_1800_break_dir, orb_1800_outcome, orb_1800_r_multiple FROM daily_features WHERE orb_1800_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '2300', orb_2300_break_dir, orb_2300_outcome, orb_2300_r_multiple FROM daily_features WHERE orb_2300_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '0030', orb_0030_break_dir, orb_0030_outcome, orb_0030_r_multiple FROM daily_features WHERE orb_0030_outcome IN ('WIN', 'LOSS')
                )
                SELECT
                    orb || ' ' || dir as setup,
                    COUNT(*) as trades,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END)::DOUBLE / COUNT(*)::DOUBLE as wr,
                    AVG(r) as avg_r,
                    SUM(r) as total_r
                FROM setup_stats
                GROUP BY orb, dir
                HAVING COUNT(*) >= 50
                ORDER BY avg_r DESC
                LIMIT 5
            """).fetchall()

            response = "**Top 5 Best Performing Setups:**\n\n"
            for setup, trades, wr, avg_r, total_r in results:
                response += f"  {setup}: WR={wr:.1%} | Avg R={avg_r:+.2f} | Total R={total_r:+.1f} | Trades={trades}\n"

            return response

        finally:
            con.close()

    def _handle_worst_setups_query(self, question: str, match) -> str:
        """Handle worst setups queries"""
        con = duckdb.connect(self.mgc_db_path, read_only=True)
        try:
            results = con.execute("""
                WITH setup_stats AS (
                    SELECT '0900' as orb, orb_0900_break_dir as dir, orb_0900_outcome as outcome, orb_0900_r_multiple as r FROM daily_features WHERE orb_0900_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '1000', orb_1000_break_dir, orb_1000_outcome, orb_1000_r_multiple FROM daily_features WHERE orb_1000_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '1100', orb_1100_break_dir, orb_1100_outcome, orb_1100_r_multiple FROM daily_features WHERE orb_1100_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '1800', orb_1800_break_dir, orb_1800_outcome, orb_1800_r_multiple FROM daily_features WHERE orb_1800_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '2300', orb_2300_break_dir, orb_2300_outcome, orb_2300_r_multiple FROM daily_features WHERE orb_2300_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '0030', orb_0030_break_dir, orb_0030_outcome, orb_0030_r_multiple FROM daily_features WHERE orb_0030_outcome IN ('WIN', 'LOSS')
                )
                SELECT
                    orb || ' ' || dir as setup,
                    COUNT(*) as trades,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END)::DOUBLE / COUNT(*)::DOUBLE as wr,
                    AVG(r) as avg_r,
                    SUM(r) as total_r
                FROM setup_stats
                GROUP BY orb, dir
                HAVING COUNT(*) >= 50
                ORDER BY avg_r ASC
                LIMIT 5
            """).fetchall()

            response = "**Top 5 Worst Performing Setups (AVOID):**\n\n"
            for setup, trades, wr, avg_r, total_r in results:
                response += f"  {setup}: WR={wr:.1%} | Avg R={avg_r:+.2f} | Total R={total_r:+.1f} | Trades={trades}\n"

            return response

        finally:
            con.close()

    def _handle_session_count_query(self, question: str, match) -> str:
        """Handle session count queries"""
        session_type = match.group(1).upper()

        con = duckdb.connect(self.mgc_db_path, read_only=True)
        try:
            # Determine which column to query
            question_lower = question.lower()
            if "asia" in question_lower:
                col = "asia_type"
            elif "london" in question_lower:
                col = "london_type"
            elif "ny" in question_lower:
                col = "ny_type"
            else:
                return "Please specify which session (Asia, London, or NY)"

            result = con.execute(f"""
                SELECT COUNT(*) FROM daily_features WHERE {col} = ?
            """, [session_type]).fetchone()[0]

            return f"**Session Count:**\n  {col.replace('_', ' ').title()} = {session_type}: {result} days"

        finally:
            con.close()

    def _handle_avg_r_query(self, question: str, match) -> str:
        """Handle average R queries"""
        return self._handle_win_rate_query(question, match)  # Same logic

    def _handle_recent_query(self, question: str, match) -> str:
        """Handle recent performance queries"""
        days = int(match.group(1)) if match.group(1) else 30
        cutoff = date.today() - timedelta(days=days)

        con = duckdb.connect(self.mgc_db_path, read_only=True)
        try:
            result = con.execute("""
                WITH recent_trades AS (
                    SELECT '0900' as orb, orb_0900_outcome as outcome, orb_0900_r_multiple as r FROM daily_features WHERE date_local >= ? AND orb_0900_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '1000', orb_1000_outcome, orb_1000_r_multiple FROM daily_features WHERE date_local >= ? AND orb_1000_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '1100', orb_1100_outcome, orb_1100_r_multiple FROM daily_features WHERE date_local >= ? AND orb_1100_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '1800', orb_1800_outcome, orb_1800_r_multiple FROM daily_features WHERE date_local >= ? AND orb_1800_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '2300', orb_2300_outcome, orb_2300_r_multiple FROM daily_features WHERE date_local >= ? AND orb_2300_outcome IN ('WIN', 'LOSS')
                    UNION ALL SELECT '0030', orb_0030_outcome, orb_0030_r_multiple FROM daily_features WHERE date_local >= ? AND orb_0030_outcome IN ('WIN', 'LOSS')
                )
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    AVG(r) as avg_r,
                    SUM(r) as total_r
                FROM recent_trades
            """, [cutoff] * 6).fetchone()

            total, wins, avg_r, total_r = result
            wr = wins / total if total > 0 else 0

            return (f"**Last {days} Days Performance:**\n"
                   f"  Total Trades: {total}\n"
                   f"  Win Rate: {wr:.1%}\n"
                   f"  Average R: {avg_r:+.2f}\n"
                   f"  Total R: {total_r:+.1f}")

        finally:
            con.close()

    def _handle_date_query(self, question: str, match) -> str:
        """Handle specific date queries"""
        target_date = date.fromisoformat(match.group(1))

        con = duckdb.connect(self.mgc_db_path, read_only=True)
        try:
            result = con.execute("""
                SELECT
                    asia_type, london_type, ny_type,
                    (asia_range / 0.1) as asia_ticks,
                    orb_0900_break_dir, orb_0900_outcome,
                    orb_1000_break_dir, orb_1000_outcome,
                    orb_1100_break_dir, orb_1100_outcome,
                    orb_1800_break_dir, orb_1800_outcome
                FROM daily_features
                WHERE date_local = ?
            """, [target_date]).fetchone()

            if not result:
                return f"No data found for {target_date}"

            asia_type, london_type, ny_type, asia_ticks = result[0:4]
            orbs = [
                (result[4], result[5], "09:00"),
                (result[6], result[7], "10:00"),
                (result[8], result[9], "11:00"),
                (result[10], result[11], "18:00"),
            ]

            response = f"**Data for {target_date}:**\n\n"
            response += f"  Sessions:\n"
            response += f"    Asia: {asia_type} ({asia_ticks:.0f} ticks)\n"
            response += f"    London: {london_type}\n"
            response += f"    NY: {ny_type}\n"
            response += f"\n  ORB Results:\n"

            for dir, outcome, time in orbs:
                if dir and outcome:
                    response += f"    {time} {dir}: {outcome}\n"

            return response

        finally:
            con.close()

    def _handle_journal_query(self, question: str, match) -> str:
        """Handle journal queries"""
        con = sqlite3.connect(self.journal_db_path)
        try:
            result = con.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    AVG(r_multiple) as avg_r,
                    SUM(pnl_usd) as total_pnl
                FROM trades
                WHERE outcome IN ('WIN', 'LOSS', 'SCRATCH')
            """).fetchone()

            total, wins, avg_r, total_pnl = result
            wr = wins / total if total > 0 else 0

            if total == 0:
                return "**Your Journal is Empty**\n  Use 'python journal.py add' to log trades"

            return (f"**Your Trading Journal:**\n"
                   f"  Total Trades: {total}\n"
                   f"  Win Rate: {wr:.1%}\n"
                   f"  Average R: {avg_r:+.2f}\n"
                   f"  Total P&L: ${total_pnl:,.2f}")

        finally:
            con.close()

    def _handle_comparison_query(self, question: str, match) -> str:
        """Handle setup comparison queries"""
        orb1 = match.group(1)
        orb2 = match.group(2)

        con = duckdb.connect(self.mgc_db_path, read_only=True)
        try:
            results = []
            for orb in [orb1, orb2]:
                result = con.execute(f"""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN orb_{orb}_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                        AVG(orb_{orb}_r_multiple) as avg_r,
                        SUM(orb_{orb}_r_multiple) as total_r
                    FROM daily_features
                    WHERE orb_{orb}_outcome IN ('WIN', 'LOSS')
                """).fetchone()
                results.append((orb, *result))

            response = "**Setup Comparison:**\n\n"
            for orb, total, wins, avg_r, total_r in results:
                wr = wins / total if total > 0 else 0
                response += f"  {orb}: WR={wr:.1%} | Avg R={avg_r:+.2f} | Total R={total_r:+.1f} | Trades={total}\n"

            return response

        finally:
            con.close()

    def query(self, question: str) -> str:
        """Process a natural language query"""
        question = question.strip()

        if not question:
            return "Please ask a question about your trading data"

        # Try each pattern
        for pattern_info in self.patterns:
            match = re.search(pattern_info["pattern"], question, re.IGNORECASE)
            if match:
                try:
                    return pattern_info["handler"](question, match)
                except Exception as e:
                    return f"Error processing query: {str(e)}"

        # No pattern matched
        return self._handle_fallback(question)

    def _handle_fallback(self, question: str) -> str:
        """Fallback handler for unrecognized questions"""
        response = "I'm not sure how to answer that. Try asking:\n\n"
        response += "  - \"What was the win rate for 1100 UP?\"\n"
        response += "  - \"Show me the best performing ORBs\"\n"
        response += "  - \"How did I perform in the last 30 days?\"\n"
        response += "  - \"Compare 1100 vs 1800\"\n"
        response += "  - \"What happened on 2026-01-09?\"\n\n"
        response += "Or use these tools directly:\n"
        response += "  - analyze_orb_performance.py\n"
        response += "  - filter_orb_setups.py\n"
        response += "  - journal.py stats\n"
        return response

    def interactive_mode(self):
        """Interactive query session"""
        print("\n" + "="*80)
        print("AI QUERY INTERFACE - Interactive Mode")
        print("="*80)
        print("\nAsk questions about your MGC trading data in natural language.")
        print("Type 'exit' or 'quit' to end the session.\n")

        while True:
            try:
                question = input("\n> ").strip()

                if question.lower() in ['exit', 'quit', 'q']:
                    print("\nGoodbye!")
                    break

                if not question:
                    continue

                response = self.query(question)
                print(f"\n{response}")

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description="AI-powered natural language query interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "question",
        nargs="*",
        help="Question to ask (or omit for interactive mode)"
    )

    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Start interactive mode"
    )

    args = parser.parse_args()

    engine = AIQueryEngine()

    if args.interactive or not args.question:
        engine.interactive_mode()
    else:
        question = " ".join(args.question)
        response = engine.query(question)
        print(f"\n{response}\n")


if __name__ == "__main__":
    main()
