import csv
import re
import base64
import io

INPUT_FILE = "C:\\Users\\pedroc\\Documents\\swiss_houses\\vaud_apartments_immobilier_ch.csv"
OUTPUT_FILE = "C:\\Users\\pedroc\\Documents\\swiss_houses\\vaud_apartments_immobilier_ch.csv"

HEADERS = [
    'City', 'NPA', 'Property Type', 'Rooms', 'Size (m2)',
    'Price (CHF)', 'Price/m2 (CHF)', 'Address', 'Year Built',
    'Parking', 'Floor', 'Cave/Cellar', 'Balcony', 'Terrace',
    'Garden', 'Elevator', 'View', 'Renovated', 'New Construction',
    'Energy Class', 'Latitude', 'Longitude', 'Description',
    'Images', 'Source', 'URL'
]


def clean_text(text):
    if not text:
        return text
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def is_base64_data(s):
    s = s.strip()
    return s.startswith('data:image/') or s.startswith('base64,')


def clean_images(images_str):
    if not images_str:
        return ''
    parts = [p.strip() for p in images_str.split(';')]
    clean_parts = []
    for p in parts:
        p = p.strip()
        if p and not is_base64_data(p) and p.startswith('http'):
            clean_parts.append(p)
    return '; '.join(clean_parts[:5])


def main():
    rows = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    print(f"Read {len(rows)} rows")
    
    cleaned = 0
    for row in rows:
        for key in ['Address', 'Description']:
            if row.get(key):
                original = row[key]
                row[key] = clean_text(row[key])
                if row[key] != original:
                    cleaned += 1
        
        if row.get('Images'):
            original_imgs = row['Images']
            row['Images'] = clean_images(row['Images'])
            if row['Images'] != original_imgs:
                cleaned += 1
        
        price = row.get('Price (CHF)', '').replace("'", "")
        size = row.get('Size (m2)', '')
        if price and size:
            try:
                row['Price/m2 (CHF)'] = str(round(int(price) / int(size)))
            except:
                row['Price/m2 (CHF)'] = ''
        elif price and not size:
            row['Price/m2 (CHF)'] = ''
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Cleaned {cleaned} fields")
    print(f"Saved to {OUTPUT_FILE}")
    
    print("\nSample cleaned rows:")
    for i, row in enumerate(rows[:5]):
        print(f"  {i+1}. {row['City']} | CHF {row.get('Price (CHF)','')} | {row.get('Size (m2)','')}m2 | Address: {row.get('Address','')[:60]}")
        print(f"     Images: {row.get('Images','')[:80]}")
        print(f"     Description: {row.get('Description','')[:80]}...")


if __name__ == '__main__':
    main()
