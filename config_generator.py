"""
config_generator.py

AUTO-GENERATES configuration from validated_setups database.

This is the NEW single source of truth for strategy configurations.
Instead of manually maintaining MGC_ORB_CONFIGS and MGC_ORB_SIZE_FILTERS
in config.py, we now read directly from the validated_setups table.

Benefits:
- Eliminates manual sync between database and config.py
- Zero chance of mismatch errors
- Single source of truth (database)
- test_app_sync.py no longer needed

Usage:
    from config_generator import load_instrument_configs

    mgc_configs, mgc_filters = load_instrument_configs('MGC')
    nq_configs, nq_filters = load_instrument_configs('NQ')
"""

import duckdb
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Database path (relative to project root)
DB_PATH = Path(__file__).parent / "gold.db"


def load_instrument_configs(
    instrument: str,
    db_path: Optional[Path] = None
) -> Tuple[Dict[str, Dict[str, any]], Dict[str, Optional[float]]]:
    """
    Load ORB configurations and size filters for an instrument from database.

    Args:
        instrument: Instrument symbol (e.g., 'MGC', 'NQ', 'MPL')
        db_path: Optional path to database (defaults to gold.db in project root)

    Returns:
        Tuple of (orb_configs, orb_size_filters)

        orb_configs: Dict mapping ORB time to config
            Example: {"0900": {"rr": 6.0, "sl_mode": "FULL"}, ...}

        orb_size_filters: Dict mapping ORB time to filter value (or None)
            Example: {"0900": None, "2300": 0.155, ...}

    Example:
        >>> mgc_configs, mgc_filters = load_instrument_configs('MGC')
        >>> mgc_configs["1000"]
        {"rr": 8.0, "sl_mode": "FULL"}
        >>> mgc_filters["1000"]
        None
    """
    if db_path is None:
        db_path = DB_PATH

    # Handle missing database gracefully
    if not db_path.exists():
        logger.warning(f"Database not found at {db_path}. Returning empty configs.")
        return {}, {}

    try:
        conn = duckdb.connect(str(db_path), read_only=True)

        # Query validated_setups for this instrument
        query = """
            SELECT
                orb_time,
                rr,
                sl_mode,
                orb_size_filter
            FROM validated_setups
            WHERE instrument = ?
            ORDER BY orb_time
        """

        results = conn.execute(query, [instrument]).fetchall()
        conn.close()

        # Build config dictionaries
        orb_configs = {}
        orb_size_filters = {}

        for orb_time, rr, sl_mode, filter_val in results:
            # Skip if RR is None (means SKIP this ORB)
            if rr is None:
                orb_configs[orb_time] = None
                orb_size_filters[orb_time] = None
                continue

            # Build config dict
            orb_configs[orb_time] = {
                "rr": float(rr),
                "sl_mode": sl_mode
            }

            # Filter value (None or float)
            orb_size_filters[orb_time] = float(filter_val) if filter_val is not None else None

        logger.info(f"Loaded {len(orb_configs)} ORB configs for {instrument}")
        return orb_configs, orb_size_filters

    except Exception as e:
        logger.error(f"Error loading configs for {instrument}: {e}")
        return {}, {}


def load_all_instrument_configs(
    db_path: Optional[Path] = None
) -> Dict[str, Tuple[Dict, Dict]]:
    """
    Load configurations for all instruments in validated_setups.

    Returns:
        Dict mapping instrument name to (orb_configs, orb_size_filters)

        Example:
            {
                'MGC': (mgc_configs, mgc_filters),
                'NQ': (nq_configs, nq_filters),
                'MPL': (mpl_configs, mpl_filters)
            }
    """
    if db_path is None:
        db_path = DB_PATH

    if not db_path.exists():
        logger.warning(f"Database not found at {db_path}")
        return {}

    try:
        conn = duckdb.connect(str(db_path), read_only=True)

        # Get list of all instruments
        instruments = conn.execute(
            "SELECT DISTINCT instrument FROM validated_setups ORDER BY instrument"
        ).fetchall()
        conn.close()

        # Load configs for each instrument
        all_configs = {}
        for (instrument,) in instruments:
            configs, filters = load_instrument_configs(instrument, db_path)
            all_configs[instrument] = (configs, filters)

        return all_configs

    except Exception as e:
        logger.error(f"Error loading all instrument configs: {e}")
        return {}


def get_orb_config(
    instrument: str,
    orb_time: str,
    db_path: Optional[Path] = None
) -> Optional[Dict[str, any]]:
    """
    Get configuration for a specific ORB.

    Args:
        instrument: Instrument symbol (e.g., 'MGC')
        orb_time: ORB time string (e.g., '1000')
        db_path: Optional path to database

    Returns:
        Config dict with 'rr' and 'sl_mode', or None if ORB should be skipped

    Example:
        >>> get_orb_config('MGC', '1000')
        {"rr": 8.0, "sl_mode": "FULL"}
    """
    configs, _ = load_instrument_configs(instrument, db_path)
    return configs.get(orb_time)


def get_orb_size_filter(
    instrument: str,
    orb_time: str,
    db_path: Optional[Path] = None
) -> Optional[float]:
    """
    Get ORB size filter for a specific ORB.

    Args:
        instrument: Instrument symbol (e.g., 'MGC')
        orb_time: ORB time string (e.g., '2300')
        db_path: Optional path to database

    Returns:
        Filter value (float) or None if no filter

    Example:
        >>> get_orb_size_filter('MGC', '2300')
        0.155
        >>> get_orb_size_filter('MGC', '1000')
        None
    """
    _, filters = load_instrument_configs(instrument, db_path)
    return filters.get(orb_time)


def print_all_configs():
    """
    Print all instrument configurations (useful for debugging).
    """
    all_configs = load_all_instrument_configs()

    for instrument, (configs, filters) in all_configs.items():
        print(f"\n{instrument} ORB Configurations:")
        print("=" * 60)

        for orb_time in sorted(configs.keys()):
            config = configs[orb_time]
            filter_val = filters[orb_time]

            if config is None:
                print(f"  {orb_time}: SKIP (not suitable)")
            else:
                rr = config['rr']
                sl_mode = config['sl_mode']
                filter_str = f"{filter_val:.3f}" if filter_val else "None"
                print(f"  {orb_time}: RR={rr}, SL={sl_mode}, Filter={filter_str}")


if __name__ == "__main__":
    """
    Test the config generator.
    """
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("CONFIG GENERATOR - Testing Auto-Generated Configurations")
    print("=" * 70)

    # Load MGC configs
    print("\n1. Loading MGC configurations:")
    mgc_configs, mgc_filters = load_instrument_configs('MGC')
    print(f"   MGC ORB Configs: {mgc_configs}")
    print(f"   MGC Size Filters: {mgc_filters}")

    # Load NQ configs
    print("\n2. Loading NQ configurations:")
    nq_configs, nq_filters = load_instrument_configs('NQ')
    print(f"   NQ ORB Configs: {nq_configs}")
    print(f"   NQ Size Filters: {nq_filters}")

    # Load all configs
    print("\n3. Loading all instrument configurations:")
    print_all_configs()

    # Test specific ORB lookup
    print("\n4. Testing specific ORB lookup:")
    mgc_1000_config = get_orb_config('MGC', '1000')
    print(f"   MGC 1000 ORB config: {mgc_1000_config}")

    mgc_2300_filter = get_orb_size_filter('MGC', '2300')
    print(f"   MGC 2300 ORB filter: {mgc_2300_filter}")

    print("\n" + "=" * 70)
    print("✅ Config generator working correctly!")
    print("=" * 70)
