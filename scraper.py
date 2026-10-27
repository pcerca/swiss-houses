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

# Common NPAs for each city
CITY_NPA = {
    "Nyon": ["1260"],
    "Rolle": ["1180"],
    "Gland": ["1196"],
    "Lausanne": ["1003", "1004", "1005", "1006", "1007", "1010", "1011", "1012"],
    "Morges": ["1110"],
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
                    
                    # Extract NPA from title
                    npa_match = re.search(r'\b(\d{4})\b', title)
                    npa = npa_match.group(1) if npa_match else ''
                    if not npa and city_name in CITY_NPA:
                        npa = CITY_NPA[city_name][0]
                    
                    all_listings.append({
                        'City': city_name,
                        'NPA': npa,
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
                
                # Extract address with NPA
                addr_match = re.search(r'(\d{4}\s+\w[\w\s,.-]+?)(?:\n|$)', body)
                if addr_match:
                    full_addr = addr_match.group(1).strip()
                    listing['Address'] = full_addr
                    npa_match = re.search(r'\b(\d{4})\b', full_addr)
                    if npa_match:
                        listing['NPA'] = npa_match.group(1)
                
                # ===== LOCATION VERIFICATION =====
                # Step 1: NPA → city (authoritative)
                NPA_TO_CITY = {
                    '1260': 'Nyon', '1261': 'Nyon', '1262': 'Nyon', '1263': 'Nyon',
                    '1180': 'Rolle', '1181': 'Rolle',
                    '1196': 'Gland', '1197': 'Gland',
                    '1003': 'Lausanne', '1004': 'Lausanne', '1005': 'Lausanne',
                    '1006': 'Lausanne', '1007': 'Lausanne', '1008': 'Lausanne',
                    '1009': 'Lausanne', '1010': 'Lausanne', '1011': 'Lausanne',
                    '1012': 'Lausanne', '1014': 'Lausanne', '1015': 'Lausanne',
                    '1017': 'Lausanne', '1018': 'Lausanne',
                    '1110': 'Morges', '1111': 'Morges', '1112': 'Morges',
                }
                TARGET_CITIES = {'Nyon', 'Rolle', 'Gland', 'Lausanne', 'Morges'}
                npa = listing.get('NPA', '')
                if npa and npa in NPA_TO_CITY:
                    actual_city = NPA_TO_CITY[npa]
                    if actual_city != listing['City']:
                        print(f"    [!] City corrected: {listing['City']} -> {actual_city} (NPA {npa})")
                        listing['City'] = actual_city
                elif npa and npa not in NPA_TO_CITY:
                    # NPA doesn't belong to any target city — skip this listing
                    listing['City'] = f'UNKNOWN (NPA {npa})'

                # Step 2: Check description for "Located in X" / "in Le Brassus" etc.
                # Known non-target communes that leak into search results
                NON_TARGET = {
                    'le brassus': 'Le Brassus (Vallée de Joux)',
                    'brassus': 'Le Brassus (Vallée de Joux)',
                    'vallée de joux': 'Vallée de Joux',
                    'vallee de joux': 'Vallée de Joux',
                    'joux': 'Vallée de Joux',
                    'saint-cergue': 'Saint-Cergue',
                    'marchairuz': 'Marchairuz',
                    'les rousses': 'Les Rousses',
                    'morez': 'Morez',
                    'gex': 'Gex',
                    'ferney': 'Ferney-Voltaire',
                    'annecy': 'Annecy',
                    'évian': 'Évian',
                    'evian': 'Évian',
                    'thônex': 'Thônex',
                    'thônex': 'Thônex',
                    'carouge': 'Carouge',
                    'vernier': 'Vernier',
                    'meyrin': 'Meyrin',
                    'lancy': 'Lancy',
                    'onetwothree': None,  # placeholder
                }

                body_lower = body.lower()
                # Look for "Located in X" or "in X" near property description
                located_match = re.search(r'(?:located in|situé à|située à|situated in|found in|in the (?:commune|locality) of)\s+([A-Za-zÀ-ÿ\s\-\'()]+)', body, re.IGNORECASE)
                if located_match:
                    mentioned = located_match.group(1).strip().lower()[:30]
                    for key, real_city in NON_TARGET.items():
                        if key in mentioned and real_city:
                            print(f"    [!] Location mismatch: tagged '{listing['City']}' but description says '{real_city}'")
                            listing['City'] = f'MISLOCATED ({real_city})'
                            break

                # Also check URL slug for non-target communes
                slug_lower = url.lower()
                for key, real_city in NON_TARGET.items():
                    if real_city and key.replace(' ', '-') in slug_lower or key in slug_lower:
                        if listing['City'] not in TARGET_CITIES or real_city not in listing['City']:
                            # Only flag if slug clearly names a different commune
                            if key in slug_lower and listing['City'].lower() not in slug_lower:
                                print(f"    [!] URL slug suggests '{real_city}' but tagged '{listing['City']}'")
                                if 'MISLOCATED' not in listing['City'] and 'UNKNOWN' not in listing['City']:
                                    listing['City'] = f'MISLOCATED ({real_city})'
                                break
                
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
                
                # Occupancy detection (life annuity, tenant, age)
                occupancy = ''
                age_match = re.search(r'(\d{2,3})\s*[-\s]?\s*(?:year|ans|jahre|jährig)', body, re.IGNORECASE)
                if re.search(r'(?:life annuity|annuity|usufruit|bail.*vie|vie.*duration)', body, re.IGNORECASE):
                    if age_match:
                        occupancy = f'Life annuity - occupied until {age_match.group(1)}yo dies'
                    else:
                        occupancy = 'Life annuity - occupied'
                elif re.search(r'(?:currently rented|is rented|rented to|rented furnished|rented vacant|loué|locataire|vermietet)', body, re.IGNORECASE):
                    occupancy = 'Rented - tenant in place'
                elif re.search(r'(?:sold with tenant|with tenant|occupied by|currently occupied|bewohnt)', body, re.IGNORECASE):
                    occupancy = 'Occupied'
                elif age_match and int(age_match.group(1)) >= 70:
                    occupancy = f'Occupant {age_match.group(1)}yo'
                listing['Occupancy'] = occupancy
                
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
    
    # Filter out mislocated and unknown listings
    valid_listings = []
    excluded = []
    for l in all_listings:
        city = l.get('City', '')
        if 'MISLOCATED' in city or 'UNKNOWN' in city:
            excluded.append(l)
        else:
            valid_listings.append(l)
    
    if excluded:
        print(f"\n[!] Excluded {len(excluded)} mislocated/unknown listings:")
        for l in excluded:
            print(f"    {l['City']} | CHF {l.get('Price (CHF)', '?')} | {l.get('URL', '')[-50:]}")
    
    all_listings = valid_listings
    
    print("\n" + "=" * 60)
    print(f"STEP 4: Saving {len(all_listings)} valid listings")
    print("=" * 60)
    
    headers = [
        'City', 'NPA', 'Property Type', 'Rooms', 'Size (m2)',
        'Price (CHF)', 'Price/m2 (CHF)', 'Address', 'Year Built',
        'Parking', 'Floor', 'Cave/Cellar', 'Balcony', 'Terrace',
        'Garden', 'Elevator', 'View', 'Renovated', 'New Construction',
        'Energy Class', 'Latitude', 'Longitude', 'Description',
        'Images', 'Source', 'URL', 'Occupancy'
    ]
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(all_listings)
    
    print(f"Done! Saved to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
