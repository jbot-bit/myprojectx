"""
CRITICAL ROBUSTNESS TEST: Temporal Stability

Break 49 trades into 3 chronological chunks (early/middle/late).
Check if each chunk has positive avg R.

This test matters more than adding more years.
"""

import pandas as pd
import numpy as np

def main():
    print("="*80)
    print("TEMPORAL STABILITY TEST - 1800 LIQUIDITY REACTION")
    print("="*80)
    print()
    print("Question: Is the edge real or just one lucky cluster?")
    print()

    # Load all reaction results from the 3 states
    # State #1: 1800_state1_reaction_results.csv
    # State #2 and #3: Need to extract from test_1800_all_states.py run

    # Let me rebuild this by re-running the comparison and collecting all trades
    print("[Collecting all 49 trades from 3 states...]")
    print()

    # For now, let me create a script that properly collects this
    print("ERROR: Need to collect trade-by-trade results with dates")
    print()
    print("Rebuilding test to capture individual trade dates...")
    print()

if __name__ == '__main__':
    main()
