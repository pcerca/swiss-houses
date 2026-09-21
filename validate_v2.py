import csv
import requests
import re
import time

INPUT_FILE = "C:\\Users\\pedroc\\Documents\\swiss_houses\\vaud_apartments_immobilier_ch_v2.csv"
MAX_PRICE = 800000

def main():
    rows = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    print(f"Validating {len(rows)} listings...\n")
    
    valid = []
    invalid = []
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    })
    
    for i, row in enumerate(rows):
        url = row.get('URL', '')
        scraped_price = int(row.get('Price (CHF)', '0').replace("'", ""))
        city = row.get('City', '')
        size = row.get('Size (m2)', '')
        
        try:
            resp = session.get(url, timeout=15)
            title_match = re.search(r'CHF[\s]*([\d\']+)', resp.text[:2000])
            if title_match:
                actual_price = int(title_match.group(1).replace("'", ""))
            else:
                actual_price = scraped_price
            
            if actual_price > MAX_PRICE:
                print(f"#{i+1} [{city}] CHF {scraped_price} -> ACTUAL CHF {actual_price} - REMOVE (over 800k)")
                invalid.append(i)
            elif actual_price != scraped_price:
                print(f"#{i+1} [{city}] CHF {scraped_price} -> ACTUAL CHF {actual_price} - FIX PRICE")
                row['Price (CHF)'] = str(actual_price)
                if size:
                    try:
                        row['Price/m2 (CHF)'] = str(round(actual_price / int(size)))
                    except:
                        pass
                valid.append(row)
            else:
                print(f"#{i+1} [{city}] CHF {scraped_price} - OK")
                valid.append(row)
        except Exception as e:
            print(f"#{i+1} [{city}] CHF {scraped_price} - ERROR: {str(e)[:50]}")
            valid.append(row)
        
        time.sleep(0.5)
    
    print(f"\nValid: {len(valid)}, Removed: {len(invalid)}")
    
    if invalid or len(valid) != len(rows):
        headers = list(rows[0].keys())
        with open(INPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(valid)
        print(f"Saved {len(valid)} listings")

if __name__ == '__main__':
    main()
