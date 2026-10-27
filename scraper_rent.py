"""Scrape rental listings from immobilier.ch for yield estimation"""
from playwright.sync_api import sync_playwright
import re
import json
import time

CITIES = {
    'Nyon': 'nyon',
    'Rolle': 'rolle',
    'Gland': 'gland',
    'Lausanne': 'lausanne',
    'Morges': 'morges',
}

def get_listing_urls(page, city_slug, max_pages=3):
    """Collect rental listing URLs via JSON-LD"""
    urls = []
    for page_num in range(1, max_pages + 1):
        url = f"https://www.immobilier.ch/en/rent/apartment/vaud/{city_slug}/page-{page_num}"
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=20000)
            page.wait_for_timeout(2500)
            
            json_ld = page.evaluate("""() => {
                const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                for (const s of scripts) {
                    try {
                        const d = JSON.parse(s.textContent);
                        if (d['@type'] === 'ItemList') return d;
                    } catch(e) {}
                }
                return null;
            }""")
            
            if not json_ld or 'itemListElement' not in json_ld:
                break
            
            for item in json_ld['itemListElement']:
                urls.append(item['url'])
            
            print(f"  Page {page_num}: {len(json_ld['itemListElement'])} listings")
            
        except Exception as e:
            print(f"  Error page {page_num}: {e}")
            break
    
    return urls


def get_listing_details(page, url):
    """Visit a rental listing and extract price, size, rooms"""
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=15000)
        page.wait_for_timeout(1500)
        
        body = page.inner_text('body')
        
        # Price from title
        title = page.title()
        price_m = re.search(r"CHF\s*([\d']+)", title)
        if not price_m:
            price_m = re.search(r"CHF\s*([\d']+)", body)
        
        if not price_m:
            return None
        
        price = int(price_m.group(1).replace("'", ""))
        
        # Size
        size_m = re.search(r"(\d+)\s*m[²2]", body)
        size = int(size_m.group(1)) if size_m else None
        
        # Rooms
        room_m = re.search(r"([\d.]+)\s*(?:rooms|pièces|Zimmer)", body)
        rooms = float(room_m.group(1)) if room_m else None
        
        # Only keep reasonable rental listings
        if not size or size < 15 or size > 500:
            return None
        if price < 400 or price > 15000:
            return None
        
        return {'price': price, 'size': size, 'rooms': rooms, 'url': url}
        
    except:
        return None


def main():
    print("=" * 60)
    print("SCRAPING RENTAL LISTINGS FROM IMMOBILIER.CH")
    print("=" * 60)
    
    all_rentals = {}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        for city_name, city_slug in CITIES.items():
            print(f"\n--- {city_name} ---")
            
            urls = get_listing_urls(page, city_slug, max_pages=2)
            print(f"  Total URLs: {len(urls)}")
            
            # Visit first 15 listings to get details
            rentals = []
            for i, url in enumerate(urls[:15]):
                detail = get_listing_details(page, url)
                if detail:
                    rentals.append(detail)
                    print(f"  [{i+1}] CHF {detail['price']}/mo, {detail['size']}m2, {detail['rooms']} rooms")
                time.sleep(0.8)
            
            all_rentals[city_name] = rentals
            print(f"  Got {len(rentals)} rental details for {city_name}")
        
        browser.close()
    
    # Calculate rent per m2 statistics
    print("\n" + "=" * 60)
    print("RENT STATISTICS")
    print("=" * 60)
    
    stats = {}
    for city, rentals in all_rentals.items():
        if not rentals:
            continue
        
        rent_per_m2 = []
        for r in rentals:
            rpm = r['price'] / r['size']
            if 15 <= rpm <= 60:
                rent_per_m2.append(rpm)
        
        if rent_per_m2:
            rent_per_m2.sort()
            median = rent_per_m2[len(rent_per_m2) // 2]
            avg = sum(rent_per_m2) / len(rent_per_m2)
            stats[city] = {
                'median_rent_m2': round(median, 2),
                'avg_rent_m2': round(avg, 2),
                'count': len(rent_per_m2),
                'listings': rentals,
            }
            print(f"\n{city}:")
            print(f"  Median: CHF {median:.2f}/m2/month")
            print(f"  Average: CHF {avg:.2f}/m2/month")
            print(f"  Based on {len(rent_per_m2)} listings")
    
    # Save
    output = {
        'stats': stats,
        'generated': time.strftime('%Y-%m-%d'),
    }
    
    with open('rent_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved to rent_data.json")


if __name__ == '__main__':
    main()
