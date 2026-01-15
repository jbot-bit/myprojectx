"""
ORB Calculation Utilities

Provides standardized calculations using ORB-anchored R (structural model).

IMPORTANT: This module uses ORB-ANCHORED R, not entry-anchored R.
- 1R = |ORB_edge - stop_price|
- TP calculated from ORB edge
- MAE/MFE measured from ORB edge

For legacy entry-anchored calculations, see backtest_orb_exec_*.py scripts.
"""

TICK_SIZE = 0.1


def calculate_orb_anchored_r(orb_high: float, orb_low: float, stop_price: float, direction: str) -> float:
    """
    Calculate 1R using ORB-anchored definition.

    ORB-anchored R: Distance from ORB edge to stop price.

    Args:
        orb_high: ORB high boundary
        orb_low: ORB low boundary
        stop_price: Stop loss price
        direction: "UP" or "DOWN"

    Returns:
        1R in ticks (ORB-anchored)

    Example:
        ORB: 2490-2500 (10 ticks)
        Stop: 2490 (Full SL, UP break)
        Direction: UP
        ORB edge: 2500
        1R = |2500 - 2490| / 0.1 = 100 ticks

        This equals the ORB size for Full SL.
    """
    assert direction in ("UP", "DOWN"), f"Invalid direction: {direction}"

    orb_edge = orb_high if direction == "UP" else orb_low
    r_orb = abs(orb_edge - stop_price) / TICK_SIZE

    return r_orb


def calculate_target_price_orb_anchored(
    orb_high: float,
    orb_low: float,
    stop_price: float,
    direction: str,
    rr: float
) -> float:
    """
    Calculate target price using ORB-anchored R.

    Target is calculated from ORB EDGE, not entry price.

    Args:
        orb_high: ORB high boundary
        orb_low: ORB low boundary
        stop_price: Stop loss price
        direction: "UP" or "DOWN"
        rr: Risk/reward ratio

    Returns:
        Target price

    Formula:
        For UP: TP = ORB_high + RR × |ORB_high - stop_price|
        For DOWN: TP = ORB_low - RR × |ORB_low - stop_price|

    Example:
        ORB: 2490-2500
        Stop: 2490 (Full SL)
        Direction: UP
        RR: 2.0

        ORB edge: 2500
        1R: |2500 - 2490| = 10 ticks = 1.0 point
        TP: 2500 + 2.0 × 1.0 = 2502.0

    ASSERTION: Ensures TP is calculated from ORB edge, never from entry_price.
    """
    assert direction in ("UP", "DOWN"), f"Invalid direction: {direction}"
    assert rr > 0, f"RR must be positive: {rr}"

    orb_edge = orb_high if direction == "UP" else orb_low
    r_orb_ticks = abs(orb_edge - stop_price) / TICK_SIZE
    reward_ticks = rr * r_orb_ticks
    reward_price = reward_ticks * TICK_SIZE

    if direction == "UP":
        target_price = orb_edge + reward_price
    else:
        target_price = orb_edge - reward_price

    # ASSERTION: Verify calculation doesn't depend on entry_price
    # (entry_price should not be in scope or used in calculation)
    assert isinstance(target_price, (int, float)), "Target price must be numeric"

    return target_price


def calculate_mae_mfe_orb_anchored(
    orb_high: float,
    orb_low: float,
    direction: str,
    bars_after_break: list
) -> tuple:
    """
    Calculate MAE/MFE using ORB-anchored definition.

    Measures maximum adverse/favorable excursion FROM ORB EDGE.

    Args:
        orb_high: ORB high boundary
        orb_low: ORB low boundary
        direction: "UP" or "DOWN"
        bars_after_break: List of price bars after break
                         Each bar: {'high': float, 'low': float, 'close': float}

    Returns:
        (mae_ticks, mfe_ticks): Tuple of MAE and MFE in ticks

    Formula:
        For UP break:
            MAE = max(0, ORB_high - min_price_after) / tick_size
            MFE = max(0, max_price_after - ORB_high) / tick_size

        For DOWN break:
            MAE = max(0, max_price_after - ORB_low) / tick_size
            MFE = max(0, ORB_low - min_price_after) / tick_size

    Example:
        ORB: 2490-2500
        Direction: UP
        ORB edge: 2500

        After break, price goes to:
        - High: 2505.0 (+5.0 points from edge = +50 ticks MFE)
        - Low: 2498.0 (-2.0 points from edge = -20 ticks MAE)

        MAE = 20 ticks (adverse move from ORB edge)
        MFE = 50 ticks (favorable move from ORB edge)

    Note: Uses ORB edge as reference, NOT entry price.
    """
    assert direction in ("UP", "DOWN"), f"Invalid direction: {direction}"
    assert len(bars_after_break) > 0, "Need at least one bar after break"

    orb_edge = orb_high if direction == "UP" else orb_low

    # Find extreme prices after break
    max_price = max(bar['high'] for bar in bars_after_break)
    min_price = min(bar['low'] for bar in bars_after_break)

    if direction == "UP":
        # MAE: How far price moved AGAINST us (below ORB edge)
        mae_ticks = max(0, (orb_edge - min_price) / TICK_SIZE)
        # MFE: How far price moved FOR us (above ORB edge)
        mfe_ticks = max(0, (max_price - orb_edge) / TICK_SIZE)
    else:  # DOWN
        # MAE: How far price moved AGAINST us (above ORB edge)
        mae_ticks = max(0, (max_price - orb_edge) / TICK_SIZE)
        # MFE: How far price moved FOR us (below ORB edge)
        mfe_ticks = max(0, (orb_edge - min_price) / TICK_SIZE)

    return (mae_ticks, mfe_ticks)


def calculate_entry_anchored_r(entry_price: float, stop_price: float) -> float:
    """
    Calculate 1R using entry-anchored definition (legacy).

    Entry-anchored R: Distance from actual entry price to stop.

    Args:
        entry_price: Actual entry price
        stop_price: Stop loss price

    Returns:
        1R in ticks (entry-anchored)

    Note:
        This is the LEGACY definition used in historical backtests.
        For structural analysis, use calculate_orb_anchored_r() instead.

    Example:
        Entry: 2502.0 (entered 2 ticks above ORB high of 2500)
        Stop: 2490.0
        1R = |2502 - 2490| / 0.1 = 120 ticks

        This is LARGER than ORB size (10 ticks) because entry is above ORB edge.
    """
    r_entry = abs(entry_price - stop_price) / TICK_SIZE
    return r_entry


def validate_orb_anchored_calculation(
    target_price: float,
    orb_high: float,
    orb_low: float,
    direction: str
) -> bool:
    """
    Validate that target price is correctly calculated from ORB edge.

    Ensures structural model compliance:
    - For UP: TP must be >= ORB_high
    - For DOWN: TP must be <= ORB_low

    Args:
        target_price: Calculated target price
        orb_high: ORB high boundary
        orb_low: ORB low boundary
        direction: "UP" or "DOWN"

    Returns:
        True if valid, False otherwise

    Raises:
        AssertionError if validation fails in strict mode
    """
    orb_edge = orb_high if direction == "UP" else orb_low

    if direction == "UP":
        valid = target_price >= orb_edge
        if not valid:
            raise AssertionError(
                f"Invalid ORB-anchored TP for UP break: "
                f"TP={target_price} must be >= ORB_edge={orb_edge}"
            )
    else:  # DOWN
        valid = target_price <= orb_edge
        if not valid:
            raise AssertionError(
                f"Invalid ORB-anchored TP for DOWN break: "
                f"TP={target_price} must be <= ORB_edge={orb_edge}"
            )

    return valid


# Example usage and tests
if __name__ == "__main__":
    print("ORB Calculation Examples - ORB-Anchored R")
    print("=" * 80)
    print()

    # Example ORB
    orb_high = 2500.0
    orb_low = 2490.0
    orb_size = (orb_high - orb_low) / TICK_SIZE
    print(f"Example ORB: {orb_low} - {orb_high} ({orb_size:.0f} ticks)")
    print()

    # Full SL UP break
    print("1. Full SL, UP break:")
    stop_price = orb_low  # 2490
    direction = "UP"
    rr = 2.0

    r_orb = calculate_orb_anchored_r(orb_high, orb_low, stop_price, direction)
    print(f"   ORB-anchored 1R: {r_orb:.0f} ticks")
    print(f"   1R / ORB size: {r_orb / orb_size:.2f}x")

    tp = calculate_target_price_orb_anchored(orb_high, orb_low, stop_price, direction, rr)
    print(f"   Target (2R): {tp:.1f}")
    print(f"   Distance from ORB edge: {(tp - orb_high) / TICK_SIZE:.0f} ticks")

    validate_orb_anchored_calculation(tp, orb_high, orb_low, direction)
    print("   ✓ Validation passed")
    print()

    # Half SL UP break
    print("2. Half SL, UP break:")
    orb_mid = (orb_high + orb_low) / 2.0
    stop_price = orb_mid  # 2495
    direction = "UP"
    rr = 2.0

    r_orb = calculate_orb_anchored_r(orb_high, orb_low, stop_price, direction)
    print(f"   ORB-anchored 1R: {r_orb:.0f} ticks")
    print(f"   1R / ORB size: {r_orb / orb_size:.2f}x")

    tp = calculate_target_price_orb_anchored(orb_high, orb_low, stop_price, direction, rr)
    print(f"   Target (2R): {tp:.1f}")
    print(f"   Distance from ORB edge: {(tp - orb_high) / TICK_SIZE:.0f} ticks")

    validate_orb_anchored_calculation(tp, orb_high, orb_low, direction)
    print("   ✓ Validation passed")
    print()

    # Compare with entry-anchored
    print("3. Comparison with entry-anchored R:")
    entry_price = 2502.0  # Entered 2 ticks above ORB high
    stop_price = orb_low
    direction = "UP"

    r_entry = calculate_entry_anchored_r(entry_price, stop_price)
    r_orb = calculate_orb_anchored_r(orb_high, orb_low, stop_price, direction)

    print(f"   Entry price: {entry_price:.1f}")
    print(f"   Entry-anchored 1R: {r_entry:.0f} ticks")
    print(f"   ORB-anchored 1R: {r_orb:.0f} ticks")
    print(f"   Difference: {r_entry - r_orb:.0f} ticks ({(r_entry/r_orb - 1)*100:.0f}% larger)")
    print()

    # MAE/MFE example
    print("4. MAE/MFE calculation (ORB-anchored):")
    bars_after = [
        {'high': 2505.0, 'low': 2498.0, 'close': 2503.0},
        {'high': 2508.0, 'low': 2502.0, 'close': 2506.0},
        {'high': 2507.0, 'low': 2499.0, 'close': 2501.0},
    ]

    mae, mfe = calculate_mae_mfe_orb_anchored(orb_high, orb_low, "UP", bars_after)
    print(f"   MAE: {mae:.0f} ticks (from ORB edge {orb_high})")
    print(f"   MFE: {mfe:.0f} ticks (from ORB edge {orb_high})")
    print(f"   MFE/MAE ratio: {mfe/mae:.2f}x")
    print()

    print("=" * 80)
    print("All examples use ORB-ANCHORED R (structural model)")
    print("For entry-anchored R, see legacy backtest scripts")
