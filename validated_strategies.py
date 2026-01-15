# VALIDATED_STRATEGIES.py
# HONEST, ZERO-LOOKAHEAD STRATEGIES - Professional Grade
# Based on STRATEGY_HIERARCHY_FINAL.md (741 days, 2024-01-02 to 2026-01-10)
# ALL ORBS ARE PROFITABLE WITH CORRECT PARAMETERS

VALIDATED_MGC_STRATEGIES = {
    '0900': {
        'trades': 741,
        'wins': 469,
        'losses': 272,
        'win_rate': 0.633,
        'expectancy': 0.27,
        'tradeable': True,
        'rr': 1.0,
        'sl_mode': 'FULL',
        'notes': 'Asia ORB - Highest win rate (63.3%)',
        'entry': 'Close outside ORB at 09:05+',
        'stop': 'Opposite ORB edge',
        'target': '1R (full ORB size from entry)'
    },
    '1000': {
        'trades': 474,
        'wins': 159,
        'losses': 315,
        'win_rate': 0.335,
        'expectancy': 0.34,
        'tradeable': True,
        'rr': 3.0,
        'sl_mode': 'FULL',
        'max_stop': 100,  # ORB must be ≤10pts (100 ticks)
        'notes': 'Asymmetric RR setup - Low WR but +3R targets',
        'entry': 'Close outside ORB at 10:05+',
        'stop': 'Opposite ORB edge',
        'target': '3R (3x ORB size from entry)'
    },
    '1100': {
        'trades': 489,
        'wins': 317,
        'losses': 172,
        'win_rate': 0.649,
        'expectancy': 0.30,
        'tradeable': True,
        'rr': 1.0,
        'sl_mode': 'FULL',
        'notes': 'Best Asia ORB - Highest priority (64.9% WR)',
        'entry': 'Close outside ORB at 11:05+',
        'stop': 'Opposite ORB edge',
        'target': '1R (full ORB size from entry)'
    },
    '1800': {
        'trades': 474,
        'wins': 220,
        'losses': 254,
        'win_rate': 0.464,
        'expectancy': 0.39,
        'tradeable': True,
        'rr': 2.0,
        'sl_mode': 'FULL',
        'notes': 'BEST DAY ORB - London open volume',
        'entry': 'Close outside ORB at 18:05+',
        'stop': 'Opposite ORB edge',
        'target': '2R (2x ORB size from entry)'
    },
    '2300': {
        'trades': 740,
        'wins': 362,
        'losses': 378,
        'win_rate': 0.489,
        'expectancy': 0.387,
        'tradeable': True,
        'rr': 1.0,
        'sl_mode': 'HALF',
        'notes': 'NIGHT ORB - Trades every day, small positive edge',
        'entry': 'Close outside ORB at 23:05+',
        'stop': 'ORB midpoint',
        'target': '1R (ORB half-range from entry)'
    },
    '0030': {
        'trades': 740,
        'wins': 322,
        'losses': 418,
        'win_rate': 0.435,
        'expectancy': 0.231,
        'tradeable': True,
        'rr': 1.0,
        'sl_mode': 'HALF',
        'notes': 'NY ORB - Trades every day, small positive edge',
        'entry': 'Close outside ORB at 00:35+',
        'stop': 'ORB midpoint',
        'target': '1R (ORB half-range from entry)'
    }
}

# Top Tier Strategies (Professional Grade)
# Ranked by expectancy and priority

TOP_STRATEGIES = [
    # PRIMARY STRATEGIES (Always check first)
    {
        'name': 'Multi-Liquidity Cascades',
        'win_rate': 0.19,  # Low WR, tail-based
        'expectancy': 1.95,
        'trades': 69,
        'frequency': '2-3 per month (9.3%)',
        'tier': 'S+',
        'description': 'HIGHEST PRIORITY. London sweeps Asia, 23:00 second sweep + acceptance failure.',
        'risk': '0.10-0.25% per trade',
        'entry': 'Entry at London level within 0.1pts',
        'filters': 'Gap >9.5pts (MANDATORY), Acceptance failure within 3 bars'
    },
    {
        'name': 'Single Liquidity Reactions',
        'win_rate': 0.337,
        'expectancy': 1.44,
        'trades': 120,
        'frequency': '16% of days (8-12/month)',
        'tier': 'S',
        'description': 'BACKUP. Single level swept at 23:00, no cascade structure.',
        'risk': '0.25-0.50% per trade',
        'entry': 'Entry on retrace to London level',
        'filters': 'Acceptance failure within 3 bars'
    },

    # SECONDARY STRATEGIES (Night ORBs)
    {
        'name': '23:00 ORB',
        'win_rate': 0.489,
        'expectancy': 0.387,
        'trades': 740,
        'frequency': '100% of days',
        'tier': 'A',
        'description': 'Night ORB - Trades daily. HALF SL mode.',
        'risk': '0.25-0.50% per trade',
        'entry': 'Close outside ORB at 23:05+',
        'stop': 'ORB midpoint',
        'target': '1R'
    },
    {
        'name': '18:00 ORB',
        'win_rate': 0.464,
        'expectancy': 0.39,
        'trades': 474,
        'frequency': '64% of days',
        'tier': 'A',
        'description': 'BEST DAY ORB - London open volume. FULL SL, 2R target.',
        'risk': '0.10-0.25% per trade',
        'entry': 'Close outside ORB at 18:05+',
        'stop': 'Opposite ORB edge',
        'target': '2R'
    },
    {
        'name': '10:00 ORB',
        'win_rate': 0.335,
        'expectancy': 0.34,
        'trades': 474,
        'frequency': '64% of days',
        'tier': 'A',
        'description': 'Asymmetric RR - Low WR but +3R targets. Max 10pt ORB.',
        'risk': '0.10-0.25% per trade',
        'entry': 'Close outside ORB at 10:05+',
        'stop': 'Opposite ORB edge',
        'target': '3R',
        'filters': 'ORB size ≤10pts (100 ticks)'
    },
    {
        'name': '11:00 ORB',
        'win_rate': 0.649,
        'expectancy': 0.30,
        'trades': 489,
        'frequency': '66% of days',
        'tier': 'A',
        'description': 'Best Asia ORB - Highest win rate (64.9%).',
        'risk': '0.10-0.25% per trade',
        'entry': 'Close outside ORB at 11:05+',
        'stop': 'Opposite ORB edge',
        'target': '1R'
    },
    {
        'name': '09:00 ORB',
        'win_rate': 0.633,
        'expectancy': 0.27,
        'trades': 741,
        'frequency': '100% of days',
        'tier': 'B',
        'description': 'Asia session start - High win rate.',
        'risk': '0.10-0.25% per trade',
        'entry': 'Close outside ORB at 09:05+',
        'stop': 'Opposite ORB edge',
        'target': '1R'
    },
    {
        'name': '00:30 ORB',
        'win_rate': 0.435,
        'expectancy': 0.231,
        'trades': 740,
        'frequency': '100% of days',
        'tier': 'B',
        'description': 'NY ORB - Trades daily. HALF SL mode.',
        'risk': '0.25-0.50% per trade',
        'entry': 'Close outside ORB at 00:35+',
        'stop': 'ORB midpoint',
        'target': '1R'
    }
]

# CORRELATION STRATEGIES (Session-dependent edges)
CORRELATION_STRATEGIES = [
    {
        'name': '10:00 UP after 09:00 WIN',
        'win_rate': 0.579,
        'expectancy': 0.16,
        'trades': 114,
        'base_session': '1000',
        'filter': 'Requires 09:00 WIN',
        'direction': 'UP',
        'tier': 'S',
        'description': 'BEST CORRELATION. Momentum continuation from Asia open.'
    },
    {
        'name': '11:00 UP after 09:00 WIN + 10:00 WIN',
        'win_rate': 0.574,
        'expectancy': 0.15,
        'trades': 68,
        'base_session': '1100',
        'filter': 'Requires 09:00 WIN AND 10:00 WIN UP',
        'direction': 'UP',
        'tier': 'A',
        'description': 'Strong momentum continuation. Triple confirmation.'
    },
    {
        'name': '11:00 DOWN after 09:00 LOSS + 10:00 WIN',
        'win_rate': 0.577,
        'expectancy': 0.15,
        'trades': 71,
        'base_session': '1100',
        'filter': 'Requires 09:00 LOSS AND 10:00 WIN DOWN',
        'direction': 'DOWN',
        'tier': 'A',
        'description': 'Reversal setup after failed start.'
    },
    {
        'name': '10:00 UP standalone (no filter)',
        'win_rate': 0.555,
        'expectancy': 0.11,
        'trades': 247,
        'base_session': '1000',
        'filter': 'No filter - standalone',
        'direction': 'UP',
        'tier': 'A',
        'description': 'Best standalone directional ORB. UP strongly preferred.'
    }
]

def get_tradeable_strategies():
    """Return only strategies with positive expectancy"""
    return {k: v for k, v in VALIDATED_MGC_STRATEGIES.items() if v['tradeable']}

def get_top_setups():
    """Return S and A tier strategies only"""
    return [s for s in TOP_STRATEGIES if s['tier'] in ['S', 'A']]
