# Property Scraper Scheduler

## How to Start

### Option 1: Double-click the batch file
- Run `start_scheduler.bat`
- Keep the window open

### Option 2: Run from command prompt
```
cd "C:\Users\pedroc\Documents\swiss_houses"
python scheduler.py
```

## What It Does
- Runs the scraper once on startup
- Then runs daily at 08:00 AM
- Logs all activity to `scheduler_log.txt`

## To Stop
- Press `Ctrl+C` in the command window

## Files
- `scheduler.py` - Main scheduler script
- `start_scheduler.bat` - Easy start script
- `scheduler_log.txt` - Activity log
