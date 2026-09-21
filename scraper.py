import csv
import re
import time
from playwright.sync_api import sync_playwright

OUTPUT_FILE = "C:\\Users\\pedroc\\Documents\\swiss_houses\\vaud_apartments_immobilier_ch_v2.csv"
MAX_PRICE = 800000

CITIES = {
    "Nyon": "nyon",
    "Rolle": "rolle",
    "Gland": "gland",
    "Lausanne": "lausanne",
    "Morges": "morges",
}


def main():
    all_urls = {}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        print("=" * 60)
        print("STEP 1: Collecting listing URLs")
        print("=" * 60)
        
        for city_name, city_slug in CITIES.items():
            print(f"\n--- {city_name} ---")
            page_num = 1
            city_urls = []
            
            while True:
                url = f"https://www.immobilier.ch/en/buy/apartment/vaud/{city_slug}/page-{page_num}"
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    page.wait_for_timeout(3000)
                    
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
                    
                    page_urls = [item['url'] for item in json_ld['itemListElement']]
                    city_urls.extend(page_urls)
                    
                    has_next = page.query_selector('a:has-text("Next")')
                    if not has_next:
                        break
                    page_num += 1
                    page.wait_for_timeout(1000)
                    
                except Exception as e:
                    print(f"    Error: {e}")
                    break
            
            all_urls[city_name] = city_urls
            print(f"  Found {len(city_urls)} URLs")
        
        total = sum(len(v) for v in all_urls.values())
        print(f"\nTotal URLs: {total}")
        
        print("\n" + "=" * 60)
        print("STEP 2: Checking each listing (title only = fast)")
        print("=" * 60)
        
        all_listings = []
        seen = set()
        
        for city_name, urls in all_urls.items():
            print(f"\n--- {city_name} ---")
            kept = 0
            skipped = 0
            
            for url in urls:
                if url in seen:
                    continue
                seen.add(url)
                
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=20000)
                    page.wait_for_timeout(2000)
                    
                    title = page.title()
                    
                    price_match = re.search(r'CHF[\s]*([\d\']+)', title)
                    if not price_match:
                        skipped += 1
                        continue
                    
                    price = int(price_match.group(1).replace("'", ""))
                    
                    if price >= MAX_PRICE:
                        skipped += 1
                        continue
                    
                    size_match = re.search(r'(\d+)\s*m[²2]', title)
                    size = size_match.group(1) if size_match else ''
                    
                    rooms_match = re.search(r'([\d.]+)\s*rms', title)
                    rooms = rooms_match.group(1) if rooms_match else ''
                    
                    prop_type = 'Apartment'
                    for t in ['Duplex', 'Attic flat', 'Terrace flat', 'Studio', 'Loft', 'Penthouse']:
                        if t.lower() in title.lower():
                            prop_type = t
                            break
                    
                    addr_match = re.search(r'(?:in|à)\s+(.*?)(?:\s*\||$)', title)
                    address = addr_match.group(1).strip() if addr_match else ''
                    
                    price_per_m2 = ''
                    if size:
                        try:
                            price_per_m2 = str(round(price / int(size)))
                        except:
                            pass
                    
                    all_listings.append({
                        'City': city_name,
                        'NPA': '',
                        'Property Type': prop_type,
                        'Rooms': rooms,
                        'Size (m2)': size,
                        'Price (CHF)': price,
                        'Price/m2 (CHF)': price_per_m2,
                        'Address': address,
                        'Year Built': '',
                        'Parking': '',
                        'Floor': '',
                        'Cave/Cellar': '',
                        'Balcony': '',
                        'Terrace': '',
                        'Garden': '',
                        'Elevator': '',
                        'View': '',
                        'Renovated': '',
                        'New Construction': '',
                        'Energy Class': '',
                        'Latitude': '',
                        'Longitude': '',
                        'Description': '',
                        'Images': '',
                        'Source': 'immobilier.ch',
                        'URL': url,
                    })
                    kept += 1
                    
                except Exception as e:
                    skipped += 1
            
            print(f"  Kept: {kept}, Skipped: {skipped}")
        
        print(f"\nTotal under 800k: {len(all_listings)}")
        
        print("\n" + "=" * 60)
        print("STEP 3: Getting details for each listing")
        print("=" * 60)
        
        for i, listing in enumerate(all_listings):
            url = listing['URL']
            slug = url.split('/')[-1][:50]
            print(f"  [{i+1}/{len(all_listings)}] {slug}...")
            
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=20000)
                page.wait_for_timeout(2000)
                
                body = page.inner_text('body')[:8000]
                
                year_match = re.search(r'(?:Year of construction|Built in|Année de construction)[:\s]*(\d{4})', body, re.IGNORECASE)
                if year_match:
                    listing['Year Built'] = year_match.group(1)
                
                parking_match = re.search(r'(\d+)\s*(?:parking|garage|place de parc|place\(s\))', body, re.IGNORECASE)
                if parking_match:
                    listing['Parking'] = parking_match.group(1)
                
                floor_match = re.search(r'(?:Floor|Étage|Etage)[:\s]*(\d+)', body, re.IGNORECASE)
                if floor_match:
                    listing['Floor'] = floor_match.group(1)
                
                energy_match = re.search(r'(?:Energy class|Classe énergétique|DPE)[:\s]*([A-G])', body, re.IGNORECASE)
                if energy_match:
                    listing['Energy Class'] = energy_match.group(1)
                
                if re.search(r'\bcave\b', body, re.IGNORECASE):
                    listing['Cave/Cellar'] = 'Yes'
                if re.search(r'\bbalcon\b', body, re.IGNORECASE):
                    listing['Balcony'] = 'Yes'
                if re.search(r'\bterrasse\b', body, re.IGNORECASE):
                    listing['Terrace'] = 'Yes'
                if re.search(r'\bjardin\b', body, re.IGNORECASE):
                    listing['Garden'] = 'Yes'
                if re.search(r'\bascenseur\b', body, re.IGNORECASE):
                    listing['Elevator'] = 'Yes'
                if re.search(r'vue.*(?:lac|lake|panoramique)', body, re.IGNORECASE):
                    listing['View'] = 'Yes'
                if re.search(r'(?:rénové|renovated)', body, re.IGNORECASE):
                    listing['Renovated'] = 'Yes'
                if re.search(r'(?:neuf|new construction|neuve)', body, re.IGNORECASE):
                    listing['New Construction'] = 'Yes'
                
                html = page.content()
                img_urls = list(set(re.findall(r'https://www\.immobilier\.ch/Medias/[^\s"<>\']+/images/(?:full|gridbig)/[^\s"<>\']+\.(?:jpg|jpeg|png|webp)', html)))
                if img_urls:
                    listing['Images'] = '; '.join(img_urls[:5])
                
                desc_match = re.search(r'(?:Description|Beschreibung)[:\s]*\n(.{100,800})', body, re.DOTALL)
                if desc_match:
                    listing['Description'] = desc_match.group(1)[:500]
                
                print(f"    -> CHF {listing['Price (CHF)']}, {listing['Size (m2)']}m2")
                
            except Exception as e:
                print(f"    Error: {e}")
            
            time.sleep(1)
        
        browser.close()
    
    print("\n" + "=" * 60)
    print(f"STEP 4: Saving {len(all_listings)} listings")
    print("=" * 60)
    
    headers = [
        'City', 'NPA', 'Property Type', 'Rooms', 'Size (m2)',
        'Price (CHF)', 'Price/m2 (CHF)', 'Address', 'Year Built',
        'Parking', 'Floor', 'Cave/Cellar', 'Balcony', 'Terrace',
        'Garden', 'Elevator', 'View', 'Renovated', 'New Construction',
        'Energy Class', 'Latitude', 'Longitude', 'Description',
        'Images', 'Source', 'URL'
    ]
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(all_listings)
    
    print(f"Done! Saved to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
