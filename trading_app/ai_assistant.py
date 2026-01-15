"""
Trading AI Assistant - Claude-powered trading assistant with live context
"""

import os
from typing import List, Dict, Any
import logging
from anthropic import Anthropic
from datetime import datetime

logger = logging.getLogger(__name__)


class TradingAIAssistant:
    """AI assistant for trading with live strategy context and persistent memory"""

    def __init__(self, memory_manager=None):
        self.api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        if not self.api_key:
            logger.warning("No ANTHROPIC_API_KEY found in environment. AI chat disabled.")
            self.client = None
        else:
            try:
                self.client = Anthropic(api_key=self.api_key)
                logger.info("AI assistant initialized with Claude Sonnet 4.5")
            except Exception as e:
                logger.error(f"Error initializing Anthropic client: {e}")
                self.client = None

        self.memory = memory_manager

    def is_available(self) -> bool:
        """Check if AI assistant is available"""
        return self.client is not None

    def get_enhanced_system_context(
        self,
        instrument: str,
        current_price: float,
        strategy_state: Dict = None,
        session_levels: Dict = None,
        orb_data: Dict = None,
        backtest_stats: Dict = None
    ) -> str:
        """Generate comprehensive system context with live trading data"""

        # Live market context
        live_context = ""
        if current_price > 0:
            live_context = f"""
**CURRENT MARKET STATE:**
- {instrument} Price: ${current_price:.2f}
- Session: {strategy_state.get('current_session', 'Unknown') if strategy_state else 'Unknown'}
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        # Strategy context
        strategy_context = ""
        if strategy_state:
            strategy_context = f"""
**ACTIVE STRATEGY:**
- Strategy: {strategy_state.get('strategy', 'None')}
- Action: {strategy_state.get('action', 'STAND_DOWN')}
- Reasons: {' | '.join(strategy_state.get('reasons', []))}
- Next Action: {strategy_state.get('next_action', 'Wait')}
"""

        # Session levels context
        levels_context = ""
        if session_levels:
            levels_context = f"""
**SESSION LEVELS:**
- Asia (09:00-17:00): ${session_levels.get('asia_low', 0):.2f} - ${session_levels.get('asia_high', 0):.2f}
- London (18:00-23:00): ${session_levels.get('london_low', 0):.2f} - ${session_levels.get('london_high', 0):.2f}
- NY (23:00-02:00): ${session_levels.get('ny_low', 0):.2f} - ${session_levels.get('ny_high', 0):.2f}
"""

        # ORB context
        orb_context = ""
        if orb_data:
            orb_context = "**CURRENT ORBs:**\n"
            for orb_name, orb_info in orb_data.items():
                if orb_info and isinstance(orb_info, dict):
                    orb_context += f"- {orb_name}: ${orb_info.get('low', 0):.2f} - ${orb_info.get('high', 0):.2f} (size: {orb_info.get('size', 0):.2f})\n"

        # Performance context
        perf_context = ""
        if backtest_stats:
            perf_context = f"""
**VALIDATED PERFORMANCE ({instrument}):**
- Total R: {backtest_stats.get('total_r', 0):.1f}R
- Win Rate: {backtest_stats.get('win_rate', 0):.1f}%
- Avg R/trade: {backtest_stats.get('avg_r', 0):.3f}R
- Total Trades: {backtest_stats.get('total_trades', 0)}
- Best ORB: {backtest_stats.get('best_orb', 'N/A')} ({backtest_stats.get('best_orb_r', 0):.2f}R)
"""

        system_prompt = f"""You are a LIVE TRADING ASSISTANT for {instrument} ORB strategies.

Your primary job: Help with real-time trade decisions, calculations, and strategy questions.

{live_context}
{strategy_context}
{levels_context}
{orb_context}
{perf_context}

**CALCULATION RULES:**

For MGC (Micro Gold) - HALF SL Mode:
- Stop = ORB Midpoint
- Risk (1R) = Entry to Midpoint = HALF the ORB range
- Target = Entry + (RR × Risk)
- Point value: $10/point
- Example LONG on ORB 2700-2706:
  * Entry: 2706 (break above high)
  * Stop: 2703 (midpoint)
  * Risk: 3 points = 1R = $30
  * Target (RR=1.5): 2706 + 4.5 = 2710.5

For MNQ (Micro Nasdaq) - FULL SL Mode:
- Stop = Opposite ORB edge
- Risk (1R) = Full ORB range
- Target = Entry + (RR × Risk)
- Tick value: $0.50/tick
- Example SHORT on ORB 21,595-21,607:
  * Entry: 21,595 (break below low)
  * Stop: 21,607 (opposite edge)
  * Risk: 12 points = 1R
  * Target (RR=1.5): 21,595 - 18 = 21,577

**STRATEGY HIERARCHY (Priority Order):**

**S+ TIER - MULTI-LIQUIDITY CASCADE (+1.95R avg, 19% WR):**
- **Highest priority strategy** - Always check first
- **Structure:** London sweeps Asia → NY sweeps London (2 cascading sweeps)
- **Requirements:**
  * Gap between Asia/London must be >9.5pts (MGC) or >15pts (NQ) - MANDATORY
  * Second sweep at 23:00+ (NY futures open)
  * Acceptance failure within 3 bars (close back inside level)
- **Entry:** At London level (swept level)
- **Stop:** 0.5 gaps away from entry (tight relative stop)
- **Target:** 2.0 gaps in opposite direction (4R effective)
- **Frequency:** 2-3 trades per month (rare but massive)
- **Why it works:** Two failed auctions create strong reversal pressure

**S TIER - SINGLE LIQUIDITY (+1.44R avg, 33.7% WR):**
- **Backup to CASCADE** - When no cascade structure exists
- **Structure:** Single London level swept at 23:00
- **Requirements:**
  * London creates key high/low
  * NY sweeps that level at 23:00+
  * Acceptance failure within 3 bars
  * No cascade structure needed (simpler)
- **Entry:** At London level (swept level)
- **Stop:** Similar to CASCADE logic
- **Target:** Gap-based targeting
- **Frequency:** 8-12 trades per month
- **Why it works:** Single failed auction at key level

**A TIER - NIGHT_ORB:**
- **23:00 ORB:** +0.387R, 48.9% WR (trades every day, HALF SL mode)
- **00:30 ORB:** +0.231R, 43.5% WR (trades every day, HALF SL mode)
- **Filters:**
  * 23:00: Skip if ORB > 0.155 × ATR (too wide)
  * 00:30: Skip if Pre-NY travel < 167 ticks (too quiet)

**A TIER - DAY_ORB:**
- **18:00 ORB:** +0.39R, 46.4% WR (BEST day ORB, FULL SL, 2R target)
- **11:00 ORB:** +0.30R, 64.9% WR (highest win rate, FULL SL)
- **10:00 ORB:** +0.34R, 33.5% WR (asymmetric 3R target, max 10pt ORB)
- **09:00 ORB:** +0.27R, 63.3% WR (Asia start, FULL SL)

**CORRELATION FILTERS (Session Dependencies):**
- **10:00 UP after 09:00 WIN:** 57.9% WR, +0.16R (momentum continuation)
- **11:00 UP after 09:00+10:00 WIN:** 57.4% WR, +0.15R (triple confirmation)
- **11:00 DOWN after 09:00 LOSS + 10:00 WIN:** 57.7% WR (reversal setup)

**KEY CONCEPTS:**
- **Acceptance Failure:** Price sweeps level, then closes back inside (rejection)
- **Gap:** Distance between session highs/lows (measures liquidity separation)
- **Cascade:** Two sequential sweeps creating layered liquidity failure
- **Half SL:** Stop at ORB midpoint (night ORBs only)
- **Full SL:** Stop at opposite ORB edge (day ORBs)

**WHEN USER ASKS:**
- "Should I trade?" → Check filters, calculate risk, give clear YES/NO
- "What's the market doing?" → Reference live price and strategy state
- "Calculate my stop" → Ask for ORB high/low, direction, then show exact prices
- "Why is X better than Y?" → Reference backtest stats and win rates
- "I'm in a trade" → Ask for entry details, calculate current R, give management advice

**PERSONALITY:**
- Direct and specific (no vague answers)
- Always show exact prices (not ranges)
- Explain WHY, not just WHAT
- Reference the data (backtest stats)
- Helpful but honest (if edge is weak, say so)

Be the trading assistant they can trust in live market conditions.
"""

        return system_prompt

    def chat(
        self,
        user_message: str,
        conversation_history: List[Dict],
        session_id: str,
        instrument: str = "MGC",
        current_price: float = 0,
        strategy_state: Dict = None,
        session_levels: Dict = None,
        orb_data: Dict = None,
        backtest_stats: Dict = None
    ) -> str:
        """Send message to Claude with full context and save to memory"""

        if not self.is_available():
            return "AI assistant not available. Set ANTHROPIC_API_KEY in .env file."

        try:
            # Build messages
            messages = conversation_history + [{"role": "user", "content": user_message}]

            # Get enhanced system context
            system_context = self.get_enhanced_system_context(
                instrument=instrument,
                current_price=current_price,
                strategy_state=strategy_state or {},
                session_levels=session_levels or {},
                orb_data=orb_data or {},
                backtest_stats=backtest_stats or {}
            )

            # Call Claude API
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2048,
                system=system_context,
                messages=messages
            )

            assistant_message = response.content[0].text

            # Save to memory if available
            if self.memory:
                context_data = {
                    "instrument": instrument,
                    "current_price": current_price,
                    "strategy": strategy_state.get('strategy') if strategy_state else None,
                    "action": strategy_state.get('action') if strategy_state else None
                }

                # Determine tags
                tags = []
                user_lower = user_message.lower()
                if any(word in user_lower for word in ['trade', 'enter', 'exit', 'stop', 'target']):
                    tags.append('trade')
                if any(word in user_lower for word in ['calculate', 'orb', 'risk']):
                    tags.append('calculation')
                if any(word in user_lower for word in ['why', 'how', 'explain', 'strategy']):
                    tags.append('strategy')

                self.memory.save_message(session_id, "user", user_message, context_data, instrument, tags)
                self.memory.save_message(session_id, "assistant", assistant_message, context_data, instrument, tags)

            return assistant_message

        except Exception as e:
            error_msg = f"Error communicating with AI: {str(e)}"
            logger.error(error_msg)
            return error_msg
