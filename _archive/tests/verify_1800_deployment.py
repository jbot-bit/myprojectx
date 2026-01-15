"""
Verify 1800 ORB Deployment
Tests that the corrected configuration is working as expected.
"""

import sys
import os

# Add trading_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'trading_app'))

def test_config_loads():
    """Test that config loads with correct 1800 parameters"""
    try:
        from config import ORB_CONFIGS, ORB_SIZE_FILTERS, ORB_TIMES

        # Check 1800 in ORB_TIMES
        orb_1800_time = [t for t in ORB_TIMES if t['name'] == '1800']
        assert len(orb_1800_time) == 1, "1800 not found in ORB_TIMES"
        assert orb_1800_time[0]['hour'] == 18, "1800 hour incorrect"
        assert orb_1800_time[0]['min'] == 0, "1800 min incorrect"

        # Check 1800 in ORB_CONFIGS
        assert '1800' in ORB_CONFIGS, "1800 not found in ORB_CONFIGS"
        config_1800 = ORB_CONFIGS['1800']
        assert config_1800['rr'] == 1.0, f"1800 RR incorrect: {config_1800['rr']}"
        assert config_1800['sl_mode'] == 'HALF', f"1800 SL mode incorrect: {config_1800['sl_mode']} (CRITICAL: Must be HALF)"
        assert config_1800['tier'] == 'DAY', f"1800 tier incorrect: {config_1800['tier']}"

        # Check 1800 filter is None
        assert '1800' in ORB_SIZE_FILTERS, "1800 not found in ORB_SIZE_FILTERS"
        assert ORB_SIZE_FILTERS['1800'] is None, f"1800 filter should be None: {ORB_SIZE_FILTERS['1800']}"

        print("[PASS] Config loads correctly")
        print(f"  - 1800 ORB_CONFIG: RR={config_1800['rr']}, SL={config_1800['sl_mode']}, TIER={config_1800['tier']}")
        print(f"  - 1800 Filter: {ORB_SIZE_FILTERS['1800']} (None = No filter, correct)")
        return True

    except Exception as e:
        print(f"[FAIL] Config test failed: {e}")
        return False

def test_existing_filters_intact():
    """Verify existing filters remain unchanged"""
    try:
        from config import ORB_SIZE_FILTERS

        expected_filters = {
            '2300': 0.155,
            '0030': 0.112,
            '1100': 0.095,
            '1000': 0.088,
            '0900': None
        }

        for orb, expected_threshold in expected_filters.items():
            actual = ORB_SIZE_FILTERS.get(orb)
            assert actual == expected_threshold, f"{orb} filter mismatch: expected {expected_threshold}, got {actual}"

        print("[PASS] Existing filters intact")
        for orb, threshold in expected_filters.items():
            if threshold is not None:
                print(f"  - {orb}: {threshold} (active)")
            else:
                print(f"  - {orb}: None (no filter)")
        return True

    except Exception as e:
        print(f"[FAIL] Filter integrity test failed: {e}")
        return False

def test_filter_logic_simulation():
    """Simulate filter logic for 1800 vs filtered ORBs"""
    try:
        from config import ORB_SIZE_FILTERS, ENABLE_ORB_SIZE_FILTERS

        # Simulate 1800 with large ORB
        orb_name = '1800'
        threshold = ORB_SIZE_FILTERS[orb_name]

        if threshold is None:
            should_pass_1800 = True
            reason_1800 = "No filter for this ORB"
        else:
            should_pass_1800 = False
            reason_1800 = "Would be filtered"

        # Simulate 2300 with large ORB
        orb_name_2300 = '2300'
        threshold_2300 = ORB_SIZE_FILTERS[orb_name_2300]
        orb_size_norm = 0.5  # Extremely large relative to ATR

        if threshold_2300 is None:
            should_pass_2300 = True
        else:
            should_pass_2300 = (orb_size_norm <= threshold_2300)  # 0.5 > 0.155, so should fail

        print("[PASS] Filter logic simulation")
        print(f"  - 1800 with large ORB (size=0.5*ATR): {should_pass_1800} ({reason_1800})")
        print(f"  - 2300 with large ORB (size=0.5*ATR): {should_pass_2300} (correctly filtered)")

        assert should_pass_1800 == True, "1800 should always pass (no filter)"
        assert should_pass_2300 == False, "2300 should filter large ORBs"

        return True

    except Exception as e:
        print(f"[FAIL] Filter logic simulation failed: {e}")
        return False

def main():
    print("="*70)
    print("1800 ORB DEPLOYMENT VERIFICATION")
    print("="*70)
    print()

    results = []

    print("Test 1: Configuration Loading")
    print("-" * 70)
    results.append(test_config_loads())
    print()

    print("Test 2: Existing Filters Integrity")
    print("-" * 70)
    results.append(test_existing_filters_intact())
    print()

    print("Test 3: Filter Logic Simulation")
    print("-" * 70)
    results.append(test_filter_logic_simulation())
    print()

    print("="*70)
    if all(results):
        print("VERIFICATION: [PASS] All tests passed")
        print()
        print("CRITICAL VERIFICATION:")
        from config import ORB_CONFIGS
        print(f"  - 1800 SL Mode: {ORB_CONFIGS['1800']['sl_mode']} (MUST BE 'HALF' - matches research)")
        print()
        print("DEPLOYMENT STATUS: Ready for paper trading")
        print("  - Config uses HALF SL (matches research)")
        print("  - Config uses RR=1.0 (only tested value)")
        print("  - No size filter applied")
        print("  - Existing filters intact (2300, 0030, 1100, 1000)")
        print()
        print("NEXT STEPS:")
        print("  1. Paper trade for 2 weeks minimum (20+ trades)")
        print("  2. Monitor: Win rate (~71%), Avg R (~+0.425), Frequency (~5/week)")
        print("  3. Compare actual vs expected performance")
        print("  4. Build proper bar-by-bar simulator for validation")
    else:
        print("VERIFICATION: [FAIL] Some tests failed")
        print("DO NOT PROCEED to paper trading until issues are resolved")
    print("="*70)

if __name__ == "__main__":
    main()
