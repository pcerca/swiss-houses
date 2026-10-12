import csv
import json
from datetime import date

INPUT_FILE = "C:\\Users\\pedroc\\Documents\\swiss_houses\\vaud_apartments_final.csv"

rows = []
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

items = []
for r in rows:
    try:
        price = int(r.get('Price (CHF)', 0) or 0)
        size = int(r.get('Size (m2)', 0) or 0)
        ppm = int(r.get('Price/m2 (CHF)', 0) or 0)
    except:
        continue

    score = 0
    reasons = []

    if ppm > 0:
        if ppm < 8000: score += 35; reasons.append(f"Excellent value CHF {ppm}/m2")
        elif ppm < 10000: score += 30; reasons.append(f"Great value CHF {ppm}/m2")
        elif ppm < 12000: score += 25; reasons.append(f"Good value CHF {ppm}/m2")
        elif ppm < 14000: score += 18; reasons.append(f"Fair value CHF {ppm}/m2")
        elif ppm < 16000: score += 12; reasons.append(f"Avg value CHF {ppm}/m2")
        else: score += 5; reasons.append(f"Expensive CHF {ppm}/m2")

    if size >= 100: score += 15; reasons.append(f"Large {size}m2")
    elif size >= 75: score += 12; reasons.append(f"Good size {size}m2")
    elif size >= 50: score += 8; reasons.append(f"Medium {size}m2")
    elif size >= 30: score += 5
    else: score += 2

    cond = r.get('Image_Condition', '')
    if cond == 'renovated_modern': score += 15; reasons.append("Renovated")
    elif cond == 'well_lit': score += 10; reasons.append("Bright")
    elif cond == 'needs_work': score += 3; reasons.append("Needs work")

    amenities = []
    for key, name in [('Parking','parking'), ('Cave/Cellar','cellar'), ('Balcony','balcony'),
                      ('Terrace','terrace'), ('Garden','garden'), ('Elevator','elevator'),
                      ('View','view'), ('Renovated','renovated')]:
        if r.get(key, ''):
            score += 2
            amenities.append(name)

    view = r.get('Image_View_Estimate', '')
    if view == 'open_view': score += 10; reasons.append("Open view")
    elif view == 'garden_view': score += 5; reasons.append("Garden view")

    try:
        rooms = float(r.get('Rooms', '0') or '0')
        if 2.5 <= rooms <= 4.5: score += 5; reasons.append(f"{rooms}rm ideal")
        elif rooms > 4.5: score += 3
        else: score += 1
    except:
        rooms = r.get('Rooms', '')

    occ = r.get('Occupancy', '')
    flag = ''
    if occ:
        if 'life annuity' in occ.lower():
            score -= 40; flag = 'LIFE ANNUITY'; reasons.append("Cannot use now")
        elif 'rented' in occ.lower():
            score -= 15; flag = 'RENTED'; reasons.append("Tenant in place")
        elif 'occupied' in occ.lower():
            score -= 20; flag = 'OCCUPIED'; reasons.append("Occupied")

    score = max(0, min(100, score))

    title = r.get('Title', '')
    url = r.get('URL', '')

    items.append({
        'city': r.get('City', ''),
        'npa': r.get('NPA', ''),
        'addr': r.get('Address', ''),
        'rooms': r.get('Rooms', ''),
        'size': size,
        'price': price,
        'ppm': ppm,
        'score': score,
        'flag': flag,
        'amenities': amenities,
        'reasons': '; '.join(reasons),
        'url': url,
    })

items.sort(key=lambda x: x['score'], reverse=True)

data = {
    'generated': date.today().strftime('%Y-%m-%d'),
    'count': len(items),
    'items': items,
}

import os
os.makedirs('docs/data', exist_ok=True)

with open('docs/data/listings.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print(f"Generated docs/data/listings.json with {len(items)} listings")
