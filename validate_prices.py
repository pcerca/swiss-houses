from playwright.sync_api import sync_playwright
import csv
import re
import time

INPUT_FILE = "C:\\Users\\pedroc\\Documents\\swiss_houses\\vaud_apartments_immobilier_ch.csv"
MAX_PRICE = 800000

def main():
    rows = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    print(f"Checking {len(rows)} listings for price mismatches...\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        page = context.new_page()
        
        bad_listings = []
        
        for i, row in enumerate(rows):
            url = row.get('URL', '')
            scraped_price = row.get('Price (CHF)', '')
            city = row.get('City', '')
            
            if not url:
                continue
            
            print(f"[{i+1}/{len(rows)}] Checking {city} - scraped CHF {scraped_price}...")
            
            try:
                page.goto(url, wait_until='networkidle', timeout=60000)
                page.wait_for_timeout(5000)
                
                title = page.title()
                body = page.inner_text('body')
                
                # Extract price from page title
                title_price_match = re.search(r"CHF[\s]*([\d']+)", title)
                title_price = None
                if title_price_match:
                    title_price = int(title_price_match.group(1).replace("'", ""))
                
                # Extract price from body
                body_prices = re.findall(r"CHF[\s]*([\d']+)", body)
                body_prices = [int(p.replace("'", "")) for p in body_prices if len(p) > 5]
                
                actual_price = title_price or (body_prices[0] if body_prices else None)
                
                if actual_price and int(scraped_price) != actual_price:
                    print(f"  MISMATCH! Scraped: CHF {scraped_price}, Actual: CHF {actual_price}")
                    bad_listings.append({
                        'row': i+1,
                        'city': city,
                        'scraped_price': scraped_price,
                        'actual_price': actual_price,
                        'url': url,
                        'over_800k': actual_price > MAX_PRICE
                    })
                else:
                    print(f"  OK (CHF {actual_price or scraped_price})")
                
            except Exception as e:
                print(f"  ERROR: {str(e)[:50]}")
            
            time.sleep(2)
        
        browser.close()
    
    print(f"\n{'='*60}")
    print(f"Found {len(bad_listings)} price mismatches:")
    
    for bad in bad_listings:
        over = "OVER 800k!" if bad['over_800k'] else "under 800k"
        print(f"  #{bad['row']} [{bad['city']}] Scraped: CHF {bad['scraped_price']}, Actual: CHF {bad['actual_price']} ({over})")
        print(f"    URL: {bad['url'][:100]}")
    
    # Remove bad listings
    if bad_listings:
        remove_rows = [bad['row']-1 for bad in bad_listings if bad['over_800k']]
        keep_rows = [r for i, r in enumerate(rows) if i not in remove_rows]
        
        print(f"\nRemoving {len(remove_rows)} listings over 800k...")
        
        headers = list(rows[0].keys())
        with open(INPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(keep_rows)
        
        print(f"Saved {len(keep_rows)} listings to {INPUT_FILE}")

if __name__ == '__main__':
    main()
