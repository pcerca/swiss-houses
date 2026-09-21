@echo off
echo Starting Property Scraper Scheduler...
echo Will run daily at 08:00
echo Press Ctrl+C to stop
echo.
cd /d "C:\Users\pedroc\Documents\swiss_houses"
"C:\Users\pedroc\AppData\Local\Programs\Python\Python312\python.exe" scheduler.py
pause
