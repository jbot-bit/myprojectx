"""
Robust Overnight Backfill Manager
==================================
Handles long-running backfills with automatic retry, reconnection, and resume.

Features:
- Automatic retry on connection errors
- Resume from last successful date
- Progress tracking to file
- Detailed logging
- Safe to interrupt (Ctrl+C) and resume later

Usage:
  python backfill_overnight.py 2024-01-01 2026-01-10

Resume after interruption:
  python backfill_overnight.py --resume

Check progress:
  python backfill_overnight.py --status
"""

import sys
import os
import time
import json
import subprocess
from datetime import date, timedelta, datetime
from pathlib import Path
from typing import Optional, Tuple


# Configuration
PROGRESS_FILE = Path("backfill_progress.json")
LOG_FILE = Path("backfill_log.txt")
MAX_RETRIES_PER_DAY = 5
RETRY_DELAY_SECONDS = 30
CHECKPOINT_INTERVAL = 5  # Save progress every N days


class BackfillManager:
    """Manages robust overnight backfilling with retry and resume"""

    def __init__(self):
        self.progress = self.load_progress()
        self.log_file = open(LOG_FILE, "a", encoding="utf-8")

    def log(self, message: str):
        """Write to both console and log file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        self.log_file.write(log_msg + "\n")
        self.log_file.flush()

    def load_progress(self) -> dict:
        """Load progress from checkpoint file"""
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        return {
            "start_date": None,
            "end_date": None,
            "last_successful_date": None,
            "completed_dates": [],
            "failed_dates": [],
            "total_days_completed": 0,
            "total_days_failed": 0,
            "started_at": None,
            "last_updated": None,
        }

    def save_progress(self):
        """Save progress to checkpoint file"""
        self.progress["last_updated"] = datetime.now().isoformat()
        with open(PROGRESS_FILE, "w") as f:
            json.dump(self.progress, f, indent=2)

    def backfill_single_day(self, d: date, retry_count: int = 0) -> bool:
        """
        Backfill a single day using the existing backfill script.
        Returns True if successful, False if failed after retries.
        """
        date_str = d.isoformat()

        try:
            self.log(f"Backfilling {date_str} (attempt {retry_count + 1}/{MAX_RETRIES_PER_DAY})...")

            # Run backfill for single day
            result = subprocess.run(
                [sys.executable, "backfill_databento_continuous.py", date_str, date_str],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per day
            )

            # Check if successful
            if result.returncode == 0:
                # Look for success indicators
                if "OK: bars_1m upsert total" in result.stdout or "inserted/replaced 0 rows (no data" in result.stdout:
                    self.log(f"[OK] {date_str} completed successfully")
                    return True
                else:
                    self.log(f"[WARN] {date_str} returned 0 but unexpected output")
                    if retry_count < MAX_RETRIES_PER_DAY - 1:
                        self.log(f"Retrying in {RETRY_DELAY_SECONDS}s...")
                        time.sleep(RETRY_DELAY_SECONDS)
                        return self.backfill_single_day(d, retry_count + 1)
                    return False
            else:
                # Check for specific errors
                error_output = result.stderr + result.stdout

                # Connection errors - always retry
                if any(err in error_output.lower() for err in ["connection", "timeout", "network", "temporary"]):
                    self.log(f"[FAIL] {date_str} connection error")
                    if retry_count < MAX_RETRIES_PER_DAY - 1:
                        self.log(f"Retrying in {RETRY_DELAY_SECONDS}s...")
                        time.sleep(RETRY_DELAY_SECONDS)
                        return self.backfill_single_day(d, retry_count + 1)

                # Databento warnings (no data) - this is OK
                if "BentoWarning: No data found" in error_output:
                    self.log(f"[INFO] {date_str} no data available (weekend/holiday)")
                    return True

                # Other errors
                self.log(f"[FAIL] {date_str} failed: {result.stderr[:200]}")
                if retry_count < MAX_RETRIES_PER_DAY - 1:
                    self.log(f"Retrying in {RETRY_DELAY_SECONDS}s...")
                    time.sleep(RETRY_DELAY_SECONDS)
                    return self.backfill_single_day(d, retry_count + 1)

                return False

        except subprocess.TimeoutExpired:
            self.log(f"[FAIL] {date_str} timeout")
            if retry_count < MAX_RETRIES_PER_DAY - 1:
                self.log(f"Retrying in {RETRY_DELAY_SECONDS}s...")
                time.sleep(RETRY_DELAY_SECONDS)
                return self.backfill_single_day(d, retry_count + 1)
            return False

        except Exception as e:
            self.log(f"[FAIL] {date_str} exception: {str(e)}")
            if retry_count < MAX_RETRIES_PER_DAY - 1:
                self.log(f"Retrying in {RETRY_DELAY_SECONDS}s...")
                time.sleep(RETRY_DELAY_SECONDS)
                return self.backfill_single_day(d, retry_count + 1)
            return False

    def backfill_range(self, start_date: date, end_date: date, resume: bool = False):
        """Backfill a date range with automatic retry and checkpoint"""

        # Initialize progress if new run
        if not resume:
            self.progress["start_date"] = start_date.isoformat()
            self.progress["end_date"] = end_date.isoformat()
            self.progress["started_at"] = datetime.now().isoformat()
            self.progress["completed_dates"] = []
            self.progress["failed_dates"] = []
            self.progress["total_days_completed"] = 0
            self.progress["total_days_failed"] = 0
            self.save_progress()

        # Determine which dates to process
        current_date = start_date
        if resume and self.progress.get("last_successful_date"):
            # Resume from day after last successful
            last_date = date.fromisoformat(self.progress["last_successful_date"])
            current_date = last_date + timedelta(days=1)
            self.log(f"Resuming from {current_date.isoformat()}")

        # Calculate total days
        total_days = (end_date - start_date).days + 1
        days_already_done = len(self.progress.get("completed_dates", []))

        self.log("="*80)
        self.log(f"Starting backfill: {start_date.isoformat()} to {end_date.isoformat()}")
        self.log(f"Total days: {total_days}")
        if resume:
            self.log(f"Already completed: {days_already_done} days")
            self.log(f"Remaining: {total_days - days_already_done} days")
        self.log("="*80)

        checkpoint_counter = 0

        # Process each day
        while current_date <= end_date:
            # Skip if already completed
            date_str = current_date.isoformat()
            if date_str in self.progress.get("completed_dates", []):
                self.log(f"Skipping {date_str} (already completed)")
                current_date += timedelta(days=1)
                continue

            # Backfill this day
            success = self.backfill_single_day(current_date)

            # Update progress
            if success:
                self.progress["completed_dates"].append(date_str)
                self.progress["total_days_completed"] = len(self.progress["completed_dates"])
                self.progress["last_successful_date"] = date_str

                # Remove from failed list if it was there
                if date_str in self.progress.get("failed_dates", []):
                    self.progress["failed_dates"].remove(date_str)
                    self.progress["total_days_failed"] = len(self.progress["failed_dates"])
            else:
                if date_str not in self.progress.get("failed_dates", []):
                    self.progress["failed_dates"].append(date_str)
                    self.progress["total_days_failed"] = len(self.progress["failed_dates"])
                self.log(f"[WARN] {date_str} failed after {MAX_RETRIES_PER_DAY} attempts - continuing with next date")

            # Checkpoint every N days
            checkpoint_counter += 1
            if checkpoint_counter >= CHECKPOINT_INTERVAL:
                self.save_progress()
                checkpoint_counter = 0
                self.print_summary()

            # Move to next day
            current_date += timedelta(days=1)

        # Final save and summary
        self.save_progress()
        self.log("="*80)
        self.log("BACKFILL COMPLETE")
        self.log("="*80)
        self.print_summary()

        if self.progress["total_days_failed"] > 0:
            self.log("\n[WARN] Some days failed. You can retry failed dates with:")
            self.log("  python backfill_overnight.py --retry-failed")

    def print_summary(self):
        """Print progress summary"""
        completed = self.progress.get("total_days_completed", 0)
        failed = self.progress.get("total_days_failed", 0)
        total = completed + failed

        self.log(f"\nProgress Summary:")
        self.log(f"  Completed: {completed} days")
        self.log(f"  Failed: {failed} days")
        if total > 0:
            self.log(f"  Success rate: {completed/total*100:.1f}%")

        if self.progress.get("started_at"):
            started = datetime.fromisoformat(self.progress["started_at"])
            elapsed = datetime.now() - started
            self.log(f"  Elapsed time: {elapsed}")

    def retry_failed_dates(self):
        """Retry all dates that previously failed"""
        failed_dates = self.progress.get("failed_dates", [])

        if not failed_dates:
            self.log("No failed dates to retry.")
            return

        self.log(f"Retrying {len(failed_dates)} failed dates...")

        for date_str in failed_dates[:]:  # Copy list to modify during iteration
            d = date.fromisoformat(date_str)
            success = self.backfill_single_day(d)

            if success:
                self.progress["failed_dates"].remove(date_str)
                self.progress["completed_dates"].append(date_str)
                self.progress["total_days_completed"] = len(self.progress["completed_dates"])
                self.progress["total_days_failed"] = len(self.progress["failed_dates"])
                self.progress["last_successful_date"] = date_str

        self.save_progress()
        self.print_summary()

    def show_status(self):
        """Display current backfill status"""
        if not self.progress.get("start_date"):
            print("No backfill in progress.")
            return

        print("="*80)
        print("BACKFILL STATUS")
        print("="*80)
        print(f"Range: {self.progress['start_date']} to {self.progress['end_date']}")
        print(f"Started: {self.progress.get('started_at', 'N/A')}")
        print(f"Last updated: {self.progress.get('last_updated', 'N/A')}")
        print(f"Last successful: {self.progress.get('last_successful_date', 'N/A')}")
        print()
        self.print_summary()

        if self.progress.get("failed_dates"):
            print(f"\nFailed dates ({len(self.progress['failed_dates'])}):")
            for date_str in sorted(self.progress["failed_dates"])[:10]:
                print(f"  - {date_str}")
            if len(self.progress["failed_dates"]) > 10:
                print(f"  ... and {len(self.progress['failed_dates']) - 10} more")

    def close(self):
        """Clean up resources"""
        self.log_file.close()


def main():
    if len(sys.argv) == 1 or "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return

    manager = BackfillManager()

    try:
        # Handle special commands
        if "--status" in sys.argv:
            manager.show_status()
            return

        if "--resume" in sys.argv:
            if not manager.progress.get("start_date"):
                print("ERROR: No backfill to resume. Start a new one first.")
                return
            start_date = date.fromisoformat(manager.progress["start_date"])
            end_date = date.fromisoformat(manager.progress["end_date"])
            manager.backfill_range(start_date, end_date, resume=True)
            return

        if "--retry-failed" in sys.argv:
            manager.retry_failed_dates()
            return

        # Normal backfill
        if len(sys.argv) < 3:
            print("ERROR: Provide start and end dates")
            print("Usage: python backfill_overnight.py YYYY-MM-DD YYYY-MM-DD")
            return

        start_date = date.fromisoformat(sys.argv[1])
        end_date = date.fromisoformat(sys.argv[2])

        if start_date > end_date:
            print("ERROR: Start date must be before end date")
            return

        manager.backfill_range(start_date, end_date)

    except KeyboardInterrupt:
        manager.log("\n\n[WARN] Interrupted by user (Ctrl+C)")
        manager.log("Progress saved. Resume with: python backfill_overnight.py --resume")
        manager.save_progress()
    except Exception as e:
        manager.log(f"\n\n[FATAL] Error: {str(e)}")
        manager.save_progress()
        raise
    finally:
        manager.close()


if __name__ == "__main__":
    main()
