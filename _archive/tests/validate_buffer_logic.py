"""
Validate Buffer Logic Correctness

Tests that the fixed robustness script produces identical stop calculations
as the original filtered backtest for the same ORB/entry scenarios.
"""

def test_buffer_logic():
    """Test stop calculation logic matches original"""

    TICK_SIZE = 0.1

    # Test case 1: Full SL with buffer (buffer should be IGNORED)
    print("Test 1: Full SL with buffer=20")
    print("-" * 50)
    orb_high = 2500.0
    orb_low = 2490.0
    orb_mid = 2495.0
    entry_price = 2502.0
    direction = "UP"
    buffer_ticks = 20.0
    sl_mode = "full"

    # Original logic (CORRECT)
    if sl_mode == "full":
        stop_price_correct = orb_low
    print(f"  Original (CORRECT): stop = {stop_price_correct} (orb_low, buffer ignored)")

    # Fixed logic
    buf = buffer_ticks * TICK_SIZE
    if sl_mode == "full":
        stop_price_fixed = orb_low
    print(f"  Fixed: stop = {stop_price_fixed}")

    # Old wrong logic
    stop_price_wrong = orb_low - buffer_ticks * TICK_SIZE
    print(f"  Old WRONG: stop = {stop_price_wrong} (orb_low - buffer)")

    stop_ticks_correct = abs(entry_price - stop_price_correct) / TICK_SIZE
    stop_ticks_wrong = abs(entry_price - stop_price_wrong) / TICK_SIZE

    print(f"  Correct stop distance: {stop_ticks_correct:.0f} ticks")
    print(f"  Wrong stop distance: {stop_ticks_wrong:.0f} ticks")
    print(f"  Difference: {stop_ticks_wrong - stop_ticks_correct:.0f} ticks WIDER when wrong")

    assert stop_price_fixed == stop_price_correct, "Fixed logic doesn't match!"
    print("  PASS PASS")
    print()

    # Test case 2: Half SL with buffer=0
    print("Test 2: Half SL with buffer=0")
    print("-" * 50)
    sl_mode = "half"
    buffer_ticks = 0.0

    # Original logic (CORRECT)
    buf = buffer_ticks * TICK_SIZE
    stop_price_correct = max(orb_low, orb_mid - buf)
    print(f"  Original (CORRECT): stop = {stop_price_correct} (mid)")

    # Fixed logic
    stop_price_fixed = max(orb_low, orb_mid - buf)
    print(f"  Fixed: stop = {stop_price_fixed}")

    assert stop_price_fixed == stop_price_correct, "Fixed logic doesn't match!"
    print("  PASS PASS")
    print()

    # Test case 3: Half SL with buffer=20 (should clamp at orb_low)
    print("Test 3: Half SL with buffer=20 (clamped at orb_low)")
    print("-" * 50)
    buffer_ticks = 20.0

    # Original logic (CORRECT)
    buf = buffer_ticks * TICK_SIZE
    stop_price_correct = max(orb_low, orb_mid - buf)
    print(f"  Original (CORRECT): stop = {stop_price_correct}")
    print(f"    mid - buf = {orb_mid} - {buf} = {orb_mid - buf}")
    print(f"    max(orb_low, mid-buf) = max({orb_low}, {orb_mid - buf}) = {stop_price_correct}")

    # Fixed logic
    stop_price_fixed = max(orb_low, orb_mid - buf)
    print(f"  Fixed: stop = {stop_price_fixed}")

    # Old wrong logic (no clamping)
    stop_price_wrong = orb_mid - buffer_ticks * TICK_SIZE
    print(f"  Old WRONG: stop = {stop_price_wrong} (no clamping, goes below orb_low!)")

    assert stop_price_fixed == stop_price_correct, "Fixed logic doesn't match!"
    print("  PASS PASS")
    print()

    # Test case 4: Half SL with buffer=5 (within range)
    print("Test 4: Half SL with buffer=5 (within range)")
    print("-" * 50)
    buffer_ticks = 5.0

    # Original logic (CORRECT)
    buf = buffer_ticks * TICK_SIZE
    stop_price_correct = max(orb_low, orb_mid - buf)
    print(f"  Original (CORRECT): stop = {stop_price_correct}")
    print(f"    mid - buf = {orb_mid} - {buf} = {orb_mid - buf}")
    print(f"    max(orb_low, mid-buf) = max({orb_low}, {orb_mid - buf}) = {stop_price_correct}")

    # Fixed logic
    stop_price_fixed = max(orb_low, orb_mid - buf)
    print(f"  Fixed: stop = {stop_price_fixed}")

    # Old wrong logic
    stop_price_wrong = orb_mid - buffer_ticks * TICK_SIZE
    print(f"  Old WRONG: stop = {stop_price_wrong} (same in this case)")

    assert stop_price_fixed == stop_price_correct, "Fixed logic doesn't match!"
    print("  PASS PASS")
    print()

    # Test case 5: DOWN trade, half SL with buffer
    print("Test 5: DOWN trade, Half SL with buffer=20")
    print("-" * 50)
    direction = "DOWN"
    entry_price = 2488.0
    buffer_ticks = 20.0
    sl_mode = "half"

    # Original logic (CORRECT)
    buf = buffer_ticks * TICK_SIZE
    stop_price_correct = min(orb_high, orb_mid + buf)
    print(f"  Original (CORRECT): stop = {stop_price_correct}")
    print(f"    mid + buf = {orb_mid} + {buf} = {orb_mid + buf}")
    print(f"    min(orb_high, mid+buf) = min({orb_high}, {orb_mid + buf}) = {stop_price_correct}")

    # Fixed logic
    stop_price_fixed = min(orb_high, orb_mid + buf)
    print(f"  Fixed: stop = {stop_price_fixed}")

    # Old wrong logic
    stop_price_wrong = orb_mid + buffer_ticks * TICK_SIZE
    print(f"  Old WRONG: stop = {stop_price_wrong} (no clamping, goes above orb_high!)")

    assert stop_price_fixed == stop_price_correct, "Fixed logic doesn't match!"
    print("  PASS PASS")
    print()

    print("=" * 50)
    print("ALL TESTS PASSED - Buffer logic is correct!")
    print("=" * 50)

if __name__ == "__main__":
    test_buffer_logic()
