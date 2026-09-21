from playwright.sync_api import sync_playwright
import re
import time

CITIES = {
    "Nyon": "nyon",
    "Rolle": "rolle",
    "Gland": "gland",
    "Lausanne": "lausanne",
    "Morges": "morges",
}

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        page = context.new_page()
        
        for city_name, city_slug in CITIES.items():
            print(f"\n=== {city_name} ===")
            
            page_num = 1
            total_under_800k = 0
            
            while True:
                url = f"https://www.immobilier.ch/en/buy/apartment/vaud/{city_slug}/page-{page_num}"
                print(f"  Page {page_num}: {url}")
                
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    page.wait_for_timeout(3000)
                    
                    text = page.inner_text('body')
                    
                    # Find all prices
                    prices = re.findall(r"CHF\s*([\d']+)\.-", text)
                    prices_int = []
                    for p_str in prices:
                        try:
                            prices_int.append(int(p_str.replace("'", "")))
                        except:
                            pass
                    
                    under_800k = [p for p in prices_int if p < 800000]
                    total_under_800k += len(under_800k)
                    
                    print(f"    Prices found: {len(prices_int)}, Under 800k: {len(under_800k)}")
                    if under_800k:
                        print(f"    Under 800k prices: {under_800k}")
                    
                    # Check if there's a next page
                    has_next = page.query_selector('a:has-text("Next")')
                    if not has_next:
                        break
                    
                    page_num += 1
                    page.wait_for_timeout(1500)
                    
                except Exception as e:
                    print(f"    Error: {e}")
                    break
            
            print(f"  TOTAL under 800k in {city_name}: {total_under_800k}")
        
        browser.close()

if __name__ == '__main__':
    main()
