"""
MGC ORB Trading Hub - Enhanced Dashboard with AI Assistant
"""

from __future__ import annotations

import io
import os
import inspect
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, List
from dataclasses import asdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from anthropic import Anthropic

import query_engine as qe
from analyze_orb_v2 import ORBAnalyzerV2

# Page config MUST be first Streamlit command
st.set_page_config(
    page_title="MGC ORB Trading Hub",
    layout="wide",
)

# Optional debug (safe here, after set_page_config)
# st.write("query_engine loaded from:", qe.__file__)
# st.write("Filters signature:", str(inspect.signature(qe.Filters)))

# ============================================================================
# AI CHAT INTEGRATION
# ============================================================================

class TradingAIAssistant:
    """AI assistant for trading research using Claude API"""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        if not self.api_key:
            st.warning("⚠️ No ANTHROPIC_API_KEY found in environment. AI chat disabled.")
            self.client = None
        else:
            self.client = Anthropic(api_key=self.api_key)

    def is_available(self) -> bool:
        return self.client is not None

    def get_system_context(self, data_summary: Dict[str, Any]) -> str:
        """Generate system context about current data state"""
        return f"""You are a trading research assistant helping analyze MGC (Micro Gold futures) ORB (Opening Range Breakout) strategies.

Current Data Context:
- Total days analyzed: {data_summary.get('total_days', 'N/A')}
- Date range: {data_summary.get('date_range', 'N/A')}
- ORBs tracked: 09:00, 10:00, 11:00, 18:00, 23:00, 00:30 (6 per day)
- Total opportunities: {data_summary.get('total_orbs', 'N/A')}

Key Principles:
1. Zero-Lookahead Methodology: Only use information available AT decision time
2. Honesty Over Accuracy: Real win rates (50-58%) matter more than inflated backtests
3. PRE blocks (PRE_ASIA, PRE_LONDON, PRE_NY) are valid - known before opens
4. Session type codes are LOOKAHEAD - cannot use for same-day ORB decisions

Known Edges:
- Primary: 10:00 UP (55.5% WR, +0.11 R)
- Best correlation: 10:00 UP after 09:00 WIN (57.9% WR, +0.16 R)
- 11:00 UP with PRE_ASIA > 50 ticks (55.1% WR, +0.10 R)

Help the user:
- Understand edge discovery results
- Optimize parameters
- Validate zero-lookahead compliance
- Design new strategies
- Interpret statistics

Be concise, data-driven, and honest about limitations."""

    def chat(self, user_message: str, conversation_history: List[Dict], data_summary: Dict) -> str:
        """Send message to Claude and get response"""
        if not self.is_available():
            return "AI assistant is not available. Please set ANTHROPIC_API_KEY environment variable."

        try:
            # Build messages from conversation history
            messages = conversation_history + [{"role": "user", "content": user_message}]

            # Call Claude API
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2048,
                system=self.get_system_context(data_summary),
                messages=messages
            )

            return response.content[0].text

        except Exception as e:
            return f"Error communicating with AI: {str(e)}"

# ============================================================================
# CACHING & DATA LOADING
# ============================================================================

@st.cache_resource(show_spinner=False)
def get_connection():
    return qe.get_connection("gold.db")

@st.cache_resource(show_spinner=False)
def get_ai_assistant():
    return TradingAIAssistant()

@st.cache_data(show_spinner=False)
def load_metadata() -> Dict[str, Any]:
    return qe.fetch_filter_metadata(get_connection())

@st.cache_data(show_spinner=False)
def load_headline_stats(
    filters_key: Tuple[Any, ...], strategy_key: Tuple[Any, ...],
    filters: qe.Filters, strategy: qe.StrategyConfig
) -> Dict[str, Any]:
    return qe.headline_stats_with_strategy(get_connection(), filters, strategy)

@st.cache_data(show_spinner=False)
def load_equity_curve(
    filters_key: Tuple[Any, ...], strategy_key: Tuple[Any, ...],
    filters: qe.Filters, strategy: qe.StrategyConfig
) -> pd.DataFrame:
    return qe.equity_curve_with_strategy(get_connection(), filters, strategy)

@st.cache_data(show_spinner=False)
def load_drilldown(
    filters_key: Tuple[Any, ...], strategy_key: Tuple[Any, ...],
    filters: qe.Filters, strategy: qe.StrategyConfig,
    limit: Optional[int], order: str
) -> pd.DataFrame:
    return qe.drilldown_with_strategy(get_connection(), filters, strategy, limit=limit, order=order)

@st.cache_data(show_spinner=False)
def load_funnel(
    filters_key: Tuple[Any, ...], strategy_key: Tuple[Any, ...],
    filters: qe.Filters, strategy: qe.StrategyConfig
) -> Dict[str, int]:
    return qe.entry_funnel(get_connection(), filters, strategy)

@st.cache_data(show_spinner=False)
def discover_edges() -> Dict[str, Any]:
    """Run edge discovery analysis"""
    # Reuse the existing connection to avoid DuckDB connection conflicts
    con = get_connection()
    analyzer = ORBAnalyzerV2(connection=con)

    # Discover all edges
    overall = analyzer.analyze_overall()
    pre_asia = analyzer.analyze_pre_asia()
    correlations = analyzer.analyze_orb_correlations()

    # Find best edges
    all_edges = []

    # Add overall edges
    for orb_time, stats in overall.items():
        for direction in ['UP', 'DOWN']:
            if direction in stats:
                all_edges.append({
                    'setup': f"{orb_time} {direction}",
                    'type': 'baseline',
                    **stats[direction]
                })

    # Add PRE block edges
    for edge in pre_asia:
        all_edges.append({
            'setup': edge['setup'],
            'type': 'pre_block',
            **edge
        })

    # Add correlation edges
    for edge in correlations:
        all_edges.append({
            'setup': edge['setup'],
            'type': 'correlation',
            **edge
        })

    # Sort by win rate * avg_r (quality score)
    for edge in all_edges:
        edge['quality_score'] = edge.get('win_rate', 0) * edge.get('avg_r', 0)

    all_edges.sort(key=lambda x: x['quality_score'], reverse=True)

    return {
        'all_edges': all_edges,
        'overall': overall,
        'pre_asia': pre_asia,
        'correlations': correlations
    }

# ============================================================================
# UI HELPERS
# ============================================================================

def render_metric_card(label: str, value: Any, delta: Optional[str] = None, help_text: Optional[str] = None):
    """Render a metric card with optional delta and help"""
    col = st.columns(1)[0]
    col.metric(label=label, value=value, delta=delta, help=help_text)

def render_edge_card(edge: Dict, index: int):
    """Render an edge discovery card with explanation"""
    setup = edge['setup']
    
    # Add explanation based on setup pattern
    explanation = ""
    if "after" in setup.lower():
        # Correlation pattern
        parts = setup.split(" after ")
        current = parts[0]
        previous = parts[1] if len(parts) > 1 else ""
        explanation = f"<div style='color: #666; font-size: 0.9em; margin-top: 8px;'><strong>Meaning:</strong> When {previous}, then {current} has better odds. This is a <em>momentum continuation pattern</em>.</div>"
    elif "UP" in setup or "DOWN" in setup:
        # Directional pattern
        direction = "UP" if "UP" in setup else "DOWN"
        explanation = f"<div style='color: #666; font-size: 0.9em; margin-top: 8px;'><strong>Meaning:</strong> Price breaks {direction.lower()} (above/below ORB). <em>UP = bullish breakout, DOWN = bearish breakout</em>.</div>"
    
    st.markdown(f"""
    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 8px 0; background: #f9f9f9;">
        <h4 style="margin: 0 0 8px 0;">#{index + 1} - {setup}</h4>
        <div style="display: flex; gap: 24px; flex-wrap: wrap;">
            <div><strong>Win Rate:</strong> {edge.get('win_rate', 0):.1%}</div>
            <div><strong>Avg R:</strong> {edge.get('avg_r', 0):+.2f}</div>
            <div><strong>Total R:</strong> {edge.get('total_r', 0):+.0f}</div>
            <div><strong>Trades:</strong> {edge.get('total_trades', 0)}</div>
            <div><strong>Type:</strong> <span style="background: #007bff; color: white; padding: 2px 8px; border-radius: 4px;">{edge['type']}</span></div>
        </div>
        {explanation}
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.title("📊 MGC ORB Trading Hub")
    st.markdown("**Zero-Lookahead Edge Discovery & Strategy Optimization**")

    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'discovered_edges' not in st.session_state:
        st.session_state.discovered_edges = None

    # Load metadata
    metadata = load_metadata()
    min_date = pd.to_datetime(metadata.get("min_date")).date() if metadata.get("min_date") else None
    max_date = pd.to_datetime(metadata.get("max_date")).date() if metadata.get("max_date") else None

    # Data summary for AI
    data_summary = {
        'total_days': metadata.get('total_days', 0),
        'date_range': f"{min_date} to {max_date}" if min_date and max_date else "N/A",
        'total_orbs': metadata.get('total_days', 0) * 6
    }

    # Sidebar - AI Chat
    with st.sidebar:
        st.markdown("### 🤖 AI Trading Assistant")

        ai = get_ai_assistant()

        if ai.is_available():
            st.success("✓ AI assistant ready")

            # Chat interface
            user_input = st.text_area(
                "Ask me anything about your trading data:",
                placeholder="e.g., What's the best setup for morning trades?",
                height=100,
                key="ai_input"
            )

            col1, col2 = st.columns(2)
            if col1.button("💬 Send", use_container_width=True):
                if user_input.strip():
                    with st.spinner("🤔 Thinking..."):
                        response = ai.chat(user_input, st.session_state.chat_history, data_summary)
                        st.session_state.chat_history.append({"role": "user", "content": user_input})
                        st.session_state.chat_history.append({"role": "assistant", "content": response})

            if col2.button("🗑️ Clear", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

            # Display chat history
            if st.session_state.chat_history:
                st.markdown("---")
                st.markdown("**Conversation:**")
                for msg in st.session_state.chat_history[-6:]:  # Show last 3 exchanges
                    if msg["role"] == "user":
                        st.markdown(f"**You:** {msg['content']}")
                    else:
                        st.markdown(f"**AI:** {msg['content']}")
        else:
            st.error("❌ AI assistant unavailable")
            st.caption("Set ANTHROPIC_API_KEY in .env to enable AI chat")

        st.markdown("---")

        # Quick stats
        st.markdown("### 📈 Data Summary")
        st.metric("Total Days", data_summary['total_days'])
        st.metric("Total ORBs", data_summary['total_orbs'])
        st.caption(f"**Range:** {data_summary['date_range']}")

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Edge Discovery",
        "⚙️ Strategy Builder",
        "📊 Backtest Results",
        "📚 Documentation"
    ])

    # ========================================================================
    # TAB 1: EDGE DISCOVERY
    # ========================================================================
    with tab1:
        st.header("Edge Discovery")
        st.markdown("Discover profitable trading edges using zero-lookahead analysis")
        
        with st.expander("📖 Understanding the Terminology", expanded=False):
            st.markdown("""
            **UP/DOWN** = Break direction (which way price broke out of the ORB)
            - **UP** = Price broke above the ORB high (bullish)
            - **DOWN** = Price broke below the ORB low (bearish)
            
            **WIN/LOSS** = Trade outcome (did the trade make money?)
            - **WIN** = Hit profit target before stop loss
            - **LOSS** = Hit stop loss before profit target
            
            **Example: "10:00 UP after 09:00 WIN"**
            - At 10:00, price broke UP (above 10:00 ORB high)
            - AND the previous 09:00 ORB trade was a WIN
            - This pattern wins 57.9% of the time (vs 55.5% baseline)
            - It's a **momentum continuation** pattern
            
            **How to Use:**
            1. Watch for 09:00 ORB to complete and record if it WINS or LOSES
            2. At 10:00, if 09:00 was a WIN and price breaks UP → Higher confidence trade
            3. Use correlations to filter and size positions
            
            See **TERMINOLOGY_EXPLAINED.md** for full details.
            """)

        col1, col2 = st.columns([3, 1])

        with col2:
            if st.button("🔬 Run Analysis", use_container_width=True, type="primary"):
                with st.spinner("Analyzing 40+ edge configurations..."):
                    st.session_state.discovered_edges = discover_edges()
                st.success("✓ Analysis complete!")
                st.rerun()

        if st.session_state.discovered_edges is None:
            st.info("👆 Click 'Run Analysis' to discover edges")

            # Show quick summary
            st.markdown("### What Gets Analyzed:")
            st.markdown("""
            - **Baseline edges** - All ORBs (09:00, 10:00, 11:00, 18:00, 23:00, 00:30) × directions
            - **PRE block edges** - Filtered by PRE_ASIA, PRE_LONDON, PRE_NY ranges
            - **ORB correlation edges** - Sequential dependencies (e.g., 10:00 after 09:00 WIN)
            - **Quality scoring** - Win Rate × Avg R for ranking
            """)

        else:
            edges = st.session_state.discovered_edges['all_edges']

            # Filters
            st.markdown("### Filter Results")
            col1, col2, col3, col4 = st.columns(4)

            min_wr = col1.slider("Min Win Rate", 0.0, 1.0, 0.50, 0.01)
            min_avg_r = col2.slider("Min Avg R", -1.0, 1.0, 0.0, 0.01)
            min_trades = col3.slider("Min Trades", 0, 200, 20, 10)
            edge_type = col4.multiselect(
                "Edge Type",
                options=['baseline', 'pre_block', 'correlation'],
                default=['baseline', 'pre_block', 'correlation']
            )

            # Filter edges
            filtered = [
                e for e in edges
                if e.get('win_rate', 0) >= min_wr
                and e.get('avg_r', 0) >= min_avg_r
                and e.get('total_trades', 0) >= min_trades
                and e['type'] in edge_type
            ]

            st.markdown(f"### Top Edges ({len(filtered)} found)")

            if len(filtered) == 0:
                st.warning("No edges match your filters. Try relaxing the criteria.")
            else:
                # Display top edges
                for i, edge in enumerate(filtered[:10]):  # Show top 10
                    render_edge_card(edge, i)

                # Export
                st.markdown("---")
                if st.button("💾 Export All Results", use_container_width=True):
                    df = pd.DataFrame(filtered)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"edges_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

    # ========================================================================
    # TAB 2: STRATEGY BUILDER
    # ========================================================================
    with tab2:
        st.header("Strategy Builder")
        st.markdown("Build and test custom ORB strategies")

        # Strategy configuration
        st.markdown("### Strategy Parameters")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Entry Setup**")
            entry_model = st.selectbox(
                "Entry Model",
                options=list(qe.ENTRY_MODELS.keys()),
                format_func=lambda x: qe.ENTRY_MODELS[x]
            )
            confirm_closes = st.number_input("Confirmation Closes", 1, 3, 1)

        with col2:
            st.markdown("**Risk Management**")
            max_stop_ticks = st.number_input("Max Stop (ticks)", 0, 200, 100, 10,
                                            help="0 = no limit")
            rr_target = st.number_input("RR Target", 1.0, 5.0, 2.0, 0.5)

        with col3:
            st.markdown("**Filters**")
            orb_times = st.multiselect(
                "ORB Times",
                options=list(qe.ORB_TIMES),
                default=['1000']
            )
            direction = st.selectbox("Direction", options=['ANY', 'UP', 'DOWN'])

        # Build strategy
        strategy = qe.StrategyConfig(
            level_basis="orb_boundary",
            entry_model=entry_model,
            confirm_closes=confirm_closes,
            retest_required=False,
            retest_rule="touch",
            pierce_ticks=None,
            rejection_tf="1m",
            stop_rule="ORB_opposite_boundary",
            max_stop_ticks=max_stop_ticks if max_stop_ticks > 0 else None,
            cutoff_minutes=None,
            one_trade_per_orb=True
        )

        filters = qe.Filters(
            start_date=str(min_date) if min_date else None,
            end_date=str(max_date) if max_date else None,
            orb_times=tuple(orb_times),
            break_dir=direction,
            outcomes=tuple(qe.OUTCOME_OPTIONS),
            asia_type_code=None,
            include_null_asia=True,
            london_type_code=None,
            include_null_london=True,
            pre_ny_type_code=None,
            include_null_pre_ny=True,
            enable_atr_filter=False,
            atr_min=None,
            atr_max=None,
            enable_asia_range_filter=False,
            asia_range_min=None,
            asia_range_max=None,
        )


        # Generate keys for caching
        filters_key = qe.filters_key(filters)
        strategy_key = qe.strategy_key(strategy)


        # Load results
        if st.button("▶️ Run Backtest", type="primary"):
            with st.spinner("Running backtest..."):
                stats = load_headline_stats(filters_key, strategy_key, filters, strategy)
                funnel = load_funnel(filters_key, strategy_key, filters, strategy)
                equity = load_equity_curve(filters_key, strategy_key, filters, strategy)

            # Display results
            st.markdown("### Results")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Trades", stats.get('total_trades', 0))
            col2.metric("Win Rate", f"{stats.get('win_rate', 0):.1%}")
            col3.metric("Avg R", f"{stats.get('avg_r', 0):+.2f}")
            col4.metric("Total R", f"{stats.get('total_r', 0):+.0f}")

            # Equity curve
            if not equity.empty:
                st.markdown("### Equity Curve")
                fig, ax = plt.subplots(figsize=(12, 4))
                ax.plot(equity.index, equity['cumulative_r'], linewidth=2)
                ax.set_xlabel("Trade Number")
                ax.set_ylabel("Cumulative R")
                ax.grid(alpha=0.3)
                st.pyplot(fig)

            # Entry funnel
            st.markdown("### Entry Funnel")
            funnel_data = {
                'Stage': list(funnel.keys()),
                'Count': list(funnel.values())
            }
            st.bar_chart(pd.DataFrame(funnel_data).set_index('Stage'))

    # ========================================================================
    # TAB 3: BACKTEST RESULTS
    # ========================================================================
    with tab3:
        st.header("Backtest Results")
        st.markdown("View detailed 1-minute precision backtest results")

        # Load RR comparison
        try:
            from rr_summary import get_rr_summary
            rr_df = get_rr_summary()

            st.markdown("### RR Target Comparison")
            st.dataframe(rr_df, use_container_width=True)

            # Chart
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

            ax1.bar(rr_df['rr'], rr_df['win_rate'])
            ax1.set_xlabel("RR Target")
            ax1.set_ylabel("Win Rate")
            ax1.set_title("Win Rate by RR")

            ax2.bar(rr_df['rr'], rr_df['avg_r'])
            ax2.axhline(0, color='red', linestyle='--', alpha=0.5)
            ax2.set_xlabel("RR Target")
            ax2.set_ylabel("Avg R")
            ax2.set_title("Avg R by RR Target")

            st.pyplot(fig)

        except Exception as e:
            st.warning(f"Could not load backtest results: {str(e)}")
            st.info("Run: `python backtest_orb_exec_1m.py --rr-grid \"1.5,2.0,2.5,3.0\" --confirm 1`")

    # ========================================================================
    # TAB 4: DOCUMENTATION
    # ========================================================================
    with tab4:
        st.header("Documentation")

        st.markdown("""
        ### Quick Start Guide

        #### 1. Edge Discovery
        - Click **"Run Analysis"** in the Edge Discovery tab
        - Review top edges ranked by quality score (Win Rate × Avg R)
        - Filter by minimum win rate, avg R, and sample size
        - Export results to CSV for further analysis

        #### 2. Strategy Builder
        - Configure entry model, confirmation closes, and risk parameters
        - Select ORB times and direction filters
        - Run backtest to see performance metrics
        - View equity curve and entry funnel

        #### 3. AI Assistant
        - Ask questions about your data in the sidebar
        - Get insights on edge discovery results
        - Validate zero-lookahead compliance
        - Design new strategy ideas

        ### Key Principles

        #### Zero-Lookahead Methodology
        **Rule:** If you can't calculate it at the open, you can't use it to trade the open.

        **Valid for decisions:**
        - PRE blocks (PRE_ASIA, PRE_LONDON, PRE_NY)
        - Previous day ORB outcomes
        - Completed session stats

        **INVALID (lookahead bias):**
        - Session type codes for current session
        - Intraday session stats before session close
        - Future ORB outcomes

        #### Honesty Over Accuracy
        - Real win rates: 50-58% (honest, tradeable)
        - Inflated backtests: 57%+ (lookahead bias)
        - Lower but REAL numbers are better

        ### Known Edges

        1. **10:00 UP** - 55.5% WR, +0.11 R (247 trades) - Primary edge
        2. **10:00 UP after 09:00 WIN** - 57.9% WR, +0.16 R (114 trades) - Best correlation
        3. **11:00 UP + PRE_ASIA > 50t** - 55.1% WR, +0.10 R (107 trades)
        4. **11:00 DOWN after 09:00 LOSS + 10:00 WIN** - 57.7% WR, +0.15 R (71 trades)

        ### Resources

        - **WORKFLOW_GUIDE.md** - Complete end-to-end process
        - **TRADING_PLAYBOOK.md** - Trading rules and setups
        - **DATABASE_SCHEMA.md** - Table documentation
        - **ZERO_LOOKAHEAD_RULES.md** - Temporal rules

        ### Environment Setup

        To enable AI chat:
        ```bash
        # Add to .env file
        ANTHROPIC_API_KEY=your_key_here
        ```

        Get your API key at: https://console.anthropic.com/
        """)

if __name__ == "__main__":
    main()
