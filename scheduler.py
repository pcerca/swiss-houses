import schedule
import time
import subprocess
import sys
import os
from datetime import datetime

SCRIPT_DIR = "C:\\Users\\pedroc\\Documents\\swiss_houses"
SCRAPER_SCRIPT = os.path.join(SCRIPT_DIR, "scraper.py")
ANALYZE_SCRIPT = os.path.join(SCRIPT_DIR, "analyze_images.py")
LOG_FILE = os.path.join(SCRIPT_DIR, "scheduler_log.txt")


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def run_scrapers():
    log("Starting daily scrape...")
    
    try:
        # Run scraper
        log("Running scraper.py...")
        result = subprocess.run(
            [sys.executable, SCRAPER_SCRIPT],
            capture_output=True, text=True, timeout=900,
            cwd=SCRIPT_DIR
        )
        if result.returncode == 0:
            log("Scraper completed successfully")
        else:
            log(f"Scraper error: {result.stderr[:200]}")
    except Exception as e:
        log(f"Scraper exception: {e}")
    
    try:
        # Run image analysis
        log("Running analyze_images.py...")
        result = subprocess.run(
            [sys.executable, ANALYZE_SCRIPT],
            capture_output=True, text=True, timeout=600,
            cwd=SCRIPT_DIR
        )
        if result.returncode == 0:
            log("Image analysis completed successfully")
        else:
            log(f"Image analysis error: {result.stderr[:200]}")
    except Exception as e:
        log(f"Image analysis exception: {e}")
    
    log("Daily scrape finished\n")


def main():
    log("=" * 50)
    log("Scheduler started")
    log("Will run scrapers daily at 08:00")
    log("=" * 50)
    
    # Schedule daily at 8:00 AM
    schedule.every().day.at("08:00").do(run_scrapers)
    
    # Also run once on startup
    log("Running initial scrape on startup...")
    run_scrapers()
    
    log("Waiting for next scheduled run...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == '__main__':
    main()
