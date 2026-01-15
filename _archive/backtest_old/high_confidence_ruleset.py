"""
High-Confidence Trading Ruleset

Based on honest analysis of in-sample data.
Only includes rules with HIGH confidence of working forward.

RULESET:
--------
1. SKIP 2300 entirely (loses -75.8R across all conditions)
2. SKIP 0030 entirely (loses -33.5R across all conditions)
3. Trade 1800 with NO ORB filter (works across all sizes: +54.0R)
4. Trade 0900, 1000, 1100 with NO filters (keep it simple)

RATIONALE:
----------
- Avoiding clear losers (2300/0030) is high confidence
- 1800 performs well without filters (no overfitting)
- Keep other sessions simple (less risk of curve-fitting)
- Total trades: ~1,500 (adequate sample size)
- Conservative approach: only exclude what clearly doesn't work

OPTIONAL (Medium Confidence - Paper Trade First):
--------------------------------------------------
- 0900: Only trade when ORB > 50 ticks (42% WR, +50R improvement)
- 1100: Only trade when ORB > 30 ticks (+32R improvement)

Results shown for both conservative and aggressive approaches.
"""

import duckdb

DB_PATH = "gold.db"

def test_high_confidence():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*100)
    print("HIGH-CONFIDENCE TRADING RULESET")
    print("="*100)
    print()
    print("Philosophy: Only filter what we're SURE doesn't work")
    print("="*100)
    print()

    sessions = ['0900', '1000', '1100', '1800', '2300', '0030']

    # HIGH CONFIDENCE RULES (Conservative)
    high_conf_rules = {
        '0900': {'active': True, 'min_orb': 0, 'max_orb': 999},
        '1000': {'active': True, 'min_orb': 0, 'max_orb': 999},
        '1100': {'active': True, 'min_orb': 0, 'max_orb': 999},
        '1800': {'active': True, 'min_orb': 0, 'max_orb': 999},
        '2300': {'active': False, 'min_orb': 999, 'max_orb': 0},  # SKIP
        '0030': {'active': False, 'min_orb': 999, 'max_orb': 0},  # SKIP
    }

    # MEDIUM CONFIDENCE RULES (Aggressive - includes ORB filters)
    med_conf_rules = {
        '0900': {'active': True, 'min_orb': 50, 'max_orb': 999},   # Only high volatility
        '1000': {'active': True, 'min_orb': 0, 'max_orb': 999},    # No filter
        '1100': {'active': True, 'min_orb': 30, 'max_orb': 999},   # Large ORBs only
        '1800': {'active': True, 'min_orb': 0, 'max_orb': 999},    # No filter
        '2300': {'active': False, 'min_orb': 999, 'max_orb': 0},   # SKIP
        '0030': {'active': False, 'min_orb': 999, 'max_orb': 0},   # SKIP
    }

    # Baseline (trade everything)
    baseline_trades = 0
    baseline_r = 0

    # High confidence results
    hc_trades = 0
    hc_r = 0

    # Medium confidence results
    mc_trades = 0
    mc_r = 0

    print("SESSION BREAKDOWN:")
    print("-"*100)
    print()

    for session in sessions:
        # Baseline
        baseline = con.execute("""
            SELECT
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
                AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
                SUM(r_multiple) as total_r
            FROM orb_trades_5m_exec_orbr
            WHERE orb = ?
                AND rr = 2.0
                AND close_confirmations = 1
                AND sl_mode = 'half'
                AND buffer_ticks = 0
                AND outcome IN ('WIN', 'LOSS')
        """, [session]).fetchone()

        if not baseline or baseline[0] == 0:
            continue

        b_trades, b_wins, b_wr, b_r = baseline

        # High confidence filter
        hc_rule = high_conf_rules[session]
        if hc_rule['active']:
            hc_result = con.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                    COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
                    AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
                    SUM(r_multiple) as total_r
                FROM orb_trades_5m_exec_orbr
                WHERE orb = ?
                    AND rr = 2.0
                    AND close_confirmations = 1
                    AND sl_mode = 'half'
                    AND buffer_ticks = 0
                    AND outcome IN ('WIN', 'LOSS')
                    AND orb_range_ticks >= ?
                    AND orb_range_ticks < ?
            """, [session, hc_rule['min_orb'], hc_rule['max_orb']]).fetchone()

            if hc_result and hc_result[0] > 0:
                hc_t, hc_w, hc_wr, hc_tr = hc_result
            else:
                hc_t, hc_w, hc_wr, hc_tr = 0, 0, 0, 0
        else:
            hc_t, hc_w, hc_wr, hc_tr = 0, 0, 0, 0

        # Medium confidence filter
        mc_rule = med_conf_rules[session]
        if mc_rule['active']:
            mc_result = con.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                    COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
                    AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
                    SUM(r_multiple) as total_r
                FROM orb_trades_5m_exec_orbr
                WHERE orb = ?
                    AND rr = 2.0
                    AND close_confirmations = 1
                    AND sl_mode = 'half'
                    AND buffer_ticks = 0
                    AND outcome IN ('WIN', 'LOSS')
                    AND orb_range_ticks >= ?
                    AND orb_range_ticks < ?
            """, [session, mc_rule['min_orb'], mc_rule['max_orb']]).fetchone()

            if mc_result and mc_result[0] > 0:
                mc_t, mc_w, mc_wr, mc_tr = mc_result
            else:
                mc_t, mc_w, mc_wr, mc_tr = 0, 0, 0, 0
        else:
            mc_t, mc_w, mc_wr, mc_tr = 0, 0, 0, 0

        session_name = {
            '0900': '09:00', '1000': '10:00', '1100': '11:00',
            '1800': '18:00', '2300': '23:00', '0030': '00:30'
        }.get(session, session)

        print(f"{session_name} ORB:")

        if not hc_rule['active']:
            print(f"  HIGH-CONF: SKIP (losing session)")
            print(f"    Baseline: {b_trades} trades | {b_r:+.1f}R | Avoided!")
        else:
            if hc_rule['min_orb'] == 0 and hc_rule['max_orb'] == 999:
                print(f"  HIGH-CONF: Trade all ORB sizes")
            else:
                print(f"  HIGH-CONF: ORB {hc_rule['min_orb']}-{hc_rule['max_orb']} ticks")
            print(f"    {hc_t} trades | {hc_w}W | WR={hc_wr:.1%} | R={hc_tr:+.1f}")

        if mc_rule['active'] and (mc_rule['min_orb'] != hc_rule['min_orb'] or mc_rule['max_orb'] != hc_rule['max_orb']):
            print(f"  MED-CONF: ORB {mc_rule['min_orb']}-{mc_rule['max_orb']} ticks")
            print(f"    {mc_t} trades | {mc_w}W | WR={mc_wr:.1%} | R={mc_tr:+.1f}")
        elif not mc_rule['active']:
            print(f"  MED-CONF: SKIP")

        print()

        baseline_trades += b_trades
        baseline_r += b_r
        hc_trades += hc_t
        hc_r += hc_tr
        mc_trades += mc_t
        mc_r += mc_tr

    print("="*100)
    print("PORTFOLIO COMPARISON")
    print("="*100)
    print()

    print("BASELINE (trade everything):")
    print(f"  {baseline_trades} trades | Total R: {baseline_r:+.1f}")
    print(f"  Avg R per trade: {baseline_r/baseline_trades:+.3f}R")
    print()

    print("HIGH-CONFIDENCE RULESET (skip 2300/0030 only):")
    print(f"  {hc_trades} trades | Total R: {hc_r:+.1f}")
    print(f"  Avg R per trade: {hc_r/hc_trades:+.3f}R")
    print(f"  Improvement: {hc_r - baseline_r:+.1f}R ({(hc_r - baseline_r)/abs(baseline_r)*100:+.0f}%)")
    print()

    print("MEDIUM-CONFIDENCE RULESET (skip 2300/0030 + ORB filters):")
    print(f"  {mc_trades} trades | Total R: {mc_r:+.1f}")
    print(f"  Avg R per trade: {mc_r/mc_trades:+.3f}R")
    print(f"  Improvement: {mc_r - baseline_r:+.1f}R ({(mc_r - baseline_r)/abs(baseline_r)*100:+.0f}%)")
    print()

    print("="*100)
    print("RECOMMENDATION")
    print("="*100)
    print()

    print("START WITH HIGH-CONFIDENCE RULES:")
    print("  - Skip 2300 and 0030 sessions entirely")
    print("  - Trade 0900, 1000, 1100, 1800 without ORB filters")
    print(f"  - Expected: {hc_r:+.1f}R on ~{hc_trades} trades")
    print(f"  - Conservative, less overfitting risk")
    print()

    print("OPTIONALLY ADD (paper trade first):")
    print("  - 0900: Only when ORB > 50 ticks")
    print("  - 1100: Only when ORB > 30 ticks")
    print(f"  - Potential upside: +{mc_r - hc_r:.1f}R (if filters work forward)")
    print(f"  - Risk: Fewer trades ({mc_trades} vs {hc_trades}), possible overfitting")
    print()

    print("REALITY CHECK:")
    print(f"  - Backtest shows {hc_r:+.1f}R (high-confidence)")
    print(f"  - Real performance likely 50-80% of backtest")
    print(f"  - Conservative expectation: {hc_r * 0.6:+.1f}R to {hc_r * 0.8:+.1f}R")
    print(f"  - Still turning {baseline_r:.1f}R loss into profit!")
    print()

    print("="*100)
    print("SUMMARY: HIGH-CONFIDENCE TRADING RULES")
    print("="*100)
    print()
    print("TRADE THESE SESSIONS (no ORB filters):")
    print("  - 09:00 ORB")
    print("  - 10:00 ORB")
    print("  - 11:00 ORB")
    print("  - 18:00 ORB")
    print()
    print("SKIP THESE SESSIONS:")
    print("  - 23:00 ORB (loses -75.8R)")
    print("  - 00:30 ORB (loses -33.5R)")
    print()
    print("ENTRY/EXIT (applies to all traded sessions):")
    print("  - Entry: 1 consecutive 5m close outside ORB")
    print("  - Stop: Half-ORB (midpoint), buffer=0")
    print("  - Target: 2.0 × ORB_range")
    print("  - 1R = ORB range size (per session, per day)")
    print()
    print("="*100)

    con.close()

if __name__ == "__main__":
    test_high_confidence()
