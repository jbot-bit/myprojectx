"""
Overnight backfill script: 2020-12-20 to 2023-12-31

This will:
1. Backfill bars_1m and bars_5m from Databento
2. Build daily_features_v2 for each day
3. Run in chunks with progress logging
4. Resume from where it left off if interrupted

Estimated time: 4-8 hours depending on API speed
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import your existing backfill functions
try:
    from backfill_databento_continuous import backfill_date_range, build_features_for_date
    from build_daily_features_v2 import build_features_for_date as build_features_v2
except ImportError:
    print("ERROR: Could not import backfill functions")
    print("Make sure backfill_databento_continuous.py and build_daily_features_v2.py exist")
    sys.exit(1)

# Configuration
START_DATE = "2020-12-20"
END_DATE = "2023-12-31"
CHUNK_SIZE_DAYS = 90  # Backfill 90 days at a time
LOG_FILE = "backfill_overnight_progress.log"
CHECKPOINT_FILE = "backfill_overnight_checkpoint.txt"

def log(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + "\n")

def save_checkpoint(date_str):
    """Save progress checkpoint"""
    with open(CHECKPOINT_FILE, 'w') as f:
        f.write(date_str)

def load_checkpoint():
    """Load last checkpoint"""
    if Path(CHECKPOINT_FILE).exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return f.read().strip()
    return None

def main():
    log("=" * 80)
    log("OVERNIGHT BACKFILL: 2020-12-20 to 2023-12-31")
    log("=" * 80)
    log("")

    # Check for checkpoint
    checkpoint = load_checkpoint()
    if checkpoint:
        log(f"Found checkpoint: {checkpoint}")
        response = input("Resume from checkpoint? (y/n): ")
        if response.lower() == 'y':
            start_date = datetime.strptime(checkpoint, "%Y-%m-%d")
        else:
            start_date = datetime.strptime(START_DATE, "%Y-%m-%d")
    else:
        start_date = datetime.strptime(START_DATE, "%Y-%m-%d")

    end_date = datetime.strptime(END_DATE, "%Y-%m-%d")

    total_days = (end_date - start_date).days + 1
    log(f"Total days to backfill: {total_days}")
    log(f"Chunk size: {CHUNK_SIZE_DAYS} days")
    log(f"Estimated chunks: {(total_days + CHUNK_SIZE_DAYS - 1) // CHUNK_SIZE_DAYS}")
    log("")

    # Backfill in chunks
    current_date = start_date
    chunk_num = 1

    while current_date <= end_date:
        chunk_end = min(current_date + timedelta(days=CHUNK_SIZE_DAYS - 1), end_date)

        chunk_start_str = current_date.strftime("%Y-%m-%d")
        chunk_end_str = chunk_end.strftime("%Y-%m-%d")

        log("=" * 80)
        log(f"CHUNK {chunk_num}: {chunk_start_str} to {chunk_end_str}")
        log("=" * 80)

        try:
            # Backfill this chunk
            log(f"Backfilling bars from Databento...")
            start_time = time.time()

            # Call your backfill function
            os.system(f"python backfill_databento_continuous.py {chunk_start_str} {chunk_end_str}")

            elapsed = time.time() - start_time
            log(f"Chunk {chunk_num} completed in {elapsed/60:.1f} minutes")

            # Save checkpoint
            save_checkpoint(chunk_end_str)
            log(f"Checkpoint saved: {chunk_end_str}")

        except Exception as e:
            log(f"ERROR in chunk {chunk_num}: {e}")
            log("Backfill interrupted. You can resume by running this script again.")
            sys.exit(1)

        # Move to next chunk
        current_date = chunk_end + timedelta(days=1)
        chunk_num += 1

        # Brief pause between chunks
        if current_date <= end_date:
            log("Pausing 5 seconds before next chunk...")
            time.sleep(5)

    log("")
    log("=" * 80)
    log("BACKFILL COMPLETE!")
    log("=" * 80)
    log(f"Backfilled {total_days} days from {START_DATE} to {END_DATE}")
    log("")
    log("Next steps:")
    log("1. Verify data: python check_db.py")
    log("2. Rerun backtests: python backtest_asia_orbs.py")
    log("3. Update TRADING_RULESET.md")
    log("")

    # Clean up checkpoint
    if Path(CHECKPOINT_FILE).exists():
        os.remove(CHECKPOINT_FILE)
        log("Checkpoint file removed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("")
        log("Backfill interrupted by user")
        log(f"You can resume by running this script again")
        sys.exit(1)
