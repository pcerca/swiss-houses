import csv
import requests
import time

INPUT_FILE = "C:\\Users\\pedroc\\Documents\\swiss_houses\\vaud_apartments_immobilier_ch.csv"

def main():
    rows = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    print(f"Validating {len(rows)} URLs with GET requests...\n")
    
    bad_urls = []
    good_urls = []
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    })
    
    for i, row in enumerate(rows):
        url = row.get('URL', '')
        city = row.get('City', '')
        price = row.get('Price (CHF)', '')
        
        if not url:
            print(f"{i+1}. [{city}] CHF {price} - NO URL")
            bad_urls.append((i+1, city, price, url, 'No URL'))
            continue
        
        try:
            resp = session.get(url, timeout=15, allow_redirects=True)
            status = resp.status_code
            content_len = len(resp.text)
            has_404 = '404' in resp.text[:500] or 'not found' in resp.text[:500].lower()
            
            if status == 200 and not has_404 and content_len > 1000:
                print(f"{i+1}. [{city}] CHF {price} - OK ({status}, {content_len} bytes)")
                good_urls.append((i+1, city, price, url))
            elif has_404:
                print(f"{i+1}. [{city}] CHF {price} - 404 PAGE ({status})")
                bad_urls.append((i+1, city, price, url, '404 page'))
            else:
                print(f"{i+1}. [{city}] CHF {price} - SUSPECT ({status}, {content_len} bytes)")
                bad_urls.append((i+1, city, price, url, f'Status {status}, {content_len}b'))
        except Exception as e:
            print(f"{i+1}. [{city}] CHF {price} - ERROR: {str(e)[:50]}")
            bad_urls.append((i+1, city, price, url, str(e)[:50]))
        
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"Results: {len(good_urls)} good, {len(bad_urls)} bad/suspect")
    
    if bad_urls:
        print(f"\nBad/Suspect URLs:")
        for num, city, price, url, reason in bad_urls:
            print(f"  #{num} [{city}] CHF {price}: {reason}")
            print(f"    URL: {url}")

if __name__ == '__main__':
    main()
