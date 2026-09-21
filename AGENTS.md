# AGENTS.md - Swiss Houses Project

## Quick Start

Python is installed but NOT on PATH. Every bash command needs:
```
$env:PATH = "C:\Users\pedroc\AppData\Local\Programs\Python\Python312\;C:\Users\pedroc\AppData\Local\Programs\Python\Python312\Scripts\" + $env:PATH
```

## Data Pipeline (run in order)

1. `python scraper.py` → scrapes immobilier.ch, outputs `vaud_apartments_immobilier_ch_v2.csv`
2. `python analyze_images.py` → downloads images, runs color analysis, outputs `vaud_apartments_final.csv`
3. `python create_excel.py` → creates styled `vaud_apartments.xlsx` with two sheets

## Key Facts

- **Source**: immobilier.ch only (homegate, comparis, immoscout24 all block scraping)
- **Cities**: Nyon, Rolle, Gland, Lausanne, Morges (Vaud canton)
- **Filter**: Apartments under CHF 800,000
- **Python**: 3.12.10 at `C:\Users\pedroc\AppData\Local\Programs\Python\Python312\`

## Dependencies (no requirements.txt)

```
playwright      # browser automation (Chromium installed)
requests        # HTTP requests
Pillow          # image analysis
openpyxl        # Excel creation
schedule        # daily scheduler
beautifulsoup4  # HTML parsing
```

Install with: `python -m pip install playwright requests Pillow openpyxl schedule beautifulsoup4`

## Gotchas

- **Price mismatch bug fixed**: The scraper now verifies prices from page titles, not search results. If you modify the card extraction logic, re-validate all prices.
- **immobilier.ch blocks HEAD requests**: Use GET with browser user-agent for validation.
- **Image URLs in HTML**: Extract via regex from page source (`/Medias/.../images/full/`), not from DOM `img` tags (returns base64 data URIs instead).
- **Excel lock file**: `~$vaud_apartments.xlsx` means the file is open; close Excel before regenerating.
- **CSV files may be locked**: If you get PermissionError, close the file in Excel/other program first.

## Scheduler

Run `start_scheduler.bat` or `python scheduler.py` to scrape daily at 08:00 AM. Keep the window open. Logs to `scheduler_log.txt`.

## Output Files

| File | Description |
|------|-------------|
| `vaud_apartments_immobilier_ch_v2.csv` | Raw scraped data |
| `vaud_apartments_final.csv` | Enriched with image analysis (29 columns) |
| `vaud_apartments.xlsx` | Styled Excel with "All Listings" + "By Price per m2" sheets |
| `property_images/` | Downloaded listing images (3 per property) |
