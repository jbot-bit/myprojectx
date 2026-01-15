"""
PHASE 2 — LIQUIDITY FAILURE TEST: 2300 ORB

Baseline breakout: -0.188R avg (WORST performer)
Median ORB size: 3.8 ticks

Hypothesis: Breakouts fail → Reaction opportunity exists

STRICT RULES:
- Use ONLY existing pre-computed fields
- No parameter optimization
- Attempt to DISPROVE edge
- Report failures honestly
- 1m execution with worst-case resolution

SAFETY: If uncertain about data leakage → STOP
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "gold.db"
SYMBOL = "MGC"
ORB_CODE = "2300"

def test_liquidity_reaction_2300(con, date_local):
    """
    Test liquidity reaction on single date for 2300 ORB.

    Entry rule: SIMPLE
    - IF price breaks ORB
    - WAIT for reaction (pull back into ORB range)
    - Enter when price reclaims ORB boundary (close back inside)

    This tests: Do failed breakouts reverse?
    """

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    # 2300 ORB window: 23:00-23:05 same day
    # Test window: 23:05-00:00 (55 minutes post-ORB)
    test_start = datetime.combine(date_obj, datetime.min.time()).replace(hour=23, minute=5)
    test_end = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=0)

    # Get 1m bars
    bars = con.execute("""
        SELECT
            ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local,
            open, high, low, close
        FROM bars_1m
        WHERE symbol = ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, test_start, test_end]).df()

    # Get ORB boundaries (pre-computed)
    orb_data = con.execute("""
        SELECT orb_2300_high, orb_2300_low, orb_2300_break_dir
        FROM daily_features
        WHERE date_local = ? AND instrument = ?
    """, [date_local, SYMBOL]).fetchone()

    if bars.empty or orb_data is None:
        return None

    orb_high, orb_low, break_dir = orb_data

    if orb_high is None or orb_low is None or break_dir == 'NONE':
        return None  # No breakout occurred

    bars['ts_local'] = bars['ts_local'].astype(str)

    # LIQUIDITY FAILURE PATTERN:
    # Price broke ORB → look for reclaim (failure of breakout)

    entry_price = None
    entry_idx = None
    direction = None

    if break_dir == 'UP':
        # Price broke UP → look for reclaim DOWN (back into ORB)
        # Entry: First close BELOW orb_high after break
        for idx, bar in bars.iterrows():
            if bar['close'] < orb_high:
                entry_price = bar['close']
                entry_idx = idx
                direction = 'SHORT'  # Fade the failed UP break
                break

    elif break_dir == 'DOWN':
        # Price broke DOWN → look for reclaim UP (back into ORB)
        # Entry: First close ABOVE orb_low after break
        for idx, bar in bars.iterrows():
            if bar['close'] > orb_low:
                entry_price = bar['close']
                entry_idx = idx
                direction = 'LONG'  # Fade the failed DOWN break
                break

    if entry_price is None:
        return None  # No reclaim occurred

    # STOP: Opposite ORB boundary
    if direction == 'SHORT':
        stop_price = orb_high + 0.5  # 5 ticks above (allow small buffer)
        target_price = orb_low  # Target: Full ORB range reversal
    else:  # LONG
        stop_price = orb_low - 0.5  # 5 ticks below
        target_price = orb_high  # Target: Full ORB range reversal

    # OUTCOME: Next 30 minutes (30 bars)
    outcome_bars = bars.iloc[entry_idx:entry_idx+30]

    if outcome_bars.empty:
        return None

    if direction == 'SHORT':
        max_adverse = outcome_bars['high'].max() - entry_price
        max_favorable = entry_price - outcome_bars['low'].min()
        stop_hit = (outcome_bars['high'].max() >= stop_price)
        target_hit = (outcome_bars['low'].min() <= target_price)
    else:  # LONG
        max_adverse = entry_price - outcome_bars['low'].min()
        max_favorable = outcome_bars['high'].max() - entry_price
        stop_hit = (outcome_bars['low'].min() <= stop_price)
        target_hit = (outcome_bars['high'].max() >= target_price)

    risk = abs(entry_price - stop_price)
    if risk <= 0:
        risk = 1.0

    # WORST CASE: Both hit = LOSS
    if stop_hit and target_hit:
        outcome = 'LOSS'
        r_multiple = -max_adverse / risk
    elif stop_hit:
        outcome = 'LOSS'
        r_multiple = -max_adverse / risk
    elif target_hit:
        outcome = 'WIN'
        r_multiple = max_favorable / risk
    else:
        # Timeout: Exit at close of 30th bar
        exit_price = outcome_bars.iloc[-1]['close']
        pnl = (entry_price - exit_price) if direction == 'SHORT' else (exit_price - entry_price)
        outcome = 'TIMEOUT'
        r_multiple = pnl / risk

    return {
        'date': str(date_local).split()[0],
        'break_dir': break_dir,
        'entry_direction': direction,
        'entry_price': entry_price,
        'stop_price': stop_price,
        'target_price': target_price,
        'outcome': outcome,
        'r_multiple': r_multiple
    }


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*80)
    print("PHASE 2 — LIQUIDITY FAILURE TEST: 2300 ORB")
    print("="*80)
    print()
    print("Hypothesis: Failed breakouts reverse (fade opportunity)")
    print("Baseline breakout: -0.188R (worst performer)")
    print()

    # Get all dates with 2300 ORB breaks
    dates = con.execute("""
        SELECT date_local
        FROM daily_features
        WHERE orb_2300_break_dir IS NOT NULL
            AND orb_2300_break_dir != 'NONE'
            AND instrument = ?
        ORDER BY date_local
    """, [SYMBOL]).df()

    print(f"Total dates with breakouts: {len(dates)}")
    print()

    # Test reaction approach
    results = []

    for date in dates['date_local']:
        result = test_liquidity_reaction_2300(con, date)
        if result:
            results.append(result)

    if len(results) == 0:
        print("[FAILURE] No reaction trades triggered")
        print("VERDICT: Edge does NOT exist (no reclaim patterns found)")
        con.close()
        return

    df = pd.DataFrame(results)

    print(f"Reaction trades triggered: {len(df)}")
    print()

    # Results
    wins = (df['outcome'] == 'WIN').sum()
    losses = (df['outcome'] == 'LOSS').sum()
    timeouts = (df['outcome'] == 'TIMEOUT').sum()

    win_rate = (wins / len(df) * 100) if len(df) > 0 else 0
    avg_r = df['r_multiple'].mean()
    total_r = df['r_multiple'].sum()

    print("RESULTS:")
    print("-"*80)
    print(f"Trades: {len(df)}")
    print(f"Wins: {wins} ({win_rate:.1f}%)")
    print(f"Losses: {losses}")
    print(f"Timeouts: {timeouts}")
    print(f"Avg R: {avg_r:+.3f}R")
    print(f"Total R: {total_r:+.2f}R")
    print()

    # ATTEMPT TO DISPROVE
    print("="*80)
    print("DISPROVING ANALYSIS")
    print("="*80)
    print()

    # Check 1: Is edge positive?
    if avg_r <= 0:
        print("[DISPROVED] Avg R is negative or zero")
        print(f"Result: {avg_r:+.3f}R")
        print("VERDICT: Edge does NOT exist")
        print()
        con.close()
        return

    # Check 2: Is sample size sufficient?
    if len(df) < 30:
        print("[INCONCLUSIVE] Sample size too small")
        print(f"Trades: {len(df)} (need 30+)")
        print("VERDICT: Cannot validate edge with small sample")
        print()

    # Check 3: Temporal stability
    if len(df) >= 30:
        chunk_size = len(df) // 3
        chunk1 = df.iloc[:chunk_size]
        chunk2 = df.iloc[chunk_size:2*chunk_size]
        chunk3 = df.iloc[2*chunk_size:]

        print("TEMPORAL STABILITY CHECK:")
        print(f"  Early: {chunk1['r_multiple'].mean():+.3f}R ({len(chunk1)} trades)")
        print(f"  Middle: {chunk2['r_multiple'].mean():+.3f}R ({len(chunk2)} trades)")
        print(f"  Late: {chunk3['r_multiple'].mean():+.3f}R ({len(chunk3)} trades)")
        print()

        positive_chunks = sum([
            chunk1['r_multiple'].mean() > 0,
            chunk2['r_multiple'].mean() > 0,
            chunk3['r_multiple'].mean() > 0
        ])

        if positive_chunks < 2:
            print("[DISPROVED] Temporal instability")
            print(f"Only {positive_chunks}/3 chunks positive")
            print("VERDICT: Edge is likely noise/luck")
            print()
            con.close()
            return

    # VERDICT
    print("="*80)
    print("FINAL VERDICT")
    print("="*80)
    print()

    if avg_r > 0.10 and len(df) >= 30:
        print(f"[EDGE EXISTS] 2300 ORB liquidity reaction shows {avg_r:+.3f}R avg")
        print(f"Sample: {len(df)} trades")
        print(f"Temporal stability: {positive_chunks}/3 chunks positive")
        print()
        print("Edge: Failed breakouts DO reverse (fade opportunity)")
    elif avg_r > 0.05:
        print(f"[WEAK EDGE] 2300 ORB shows marginal edge ({avg_r:+.3f}R)")
        print(f"Not strong enough to trade with confidence")
    else:
        print(f"[NO EDGE] 2300 ORB liquidity reaction fails")

    print()

    # Save
    df.to_csv('2300_liquidity_reaction_results.csv', index=False)
    print("Results saved to: 2300_liquidity_reaction_results.csv")
    print()

    con.close()


if __name__ == '__main__':
    main()
