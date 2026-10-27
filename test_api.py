import requests
import re
import json

# Try API endpoints and alternative approaches
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.homegate.ch/',
}

# 1. Try Homegate API (they use an internal API)
print("=== Homegate API ===")
try:
    r = requests.get('https://www.homegate.ch/bff/api/search/listings', 
        params={'city': 'Lausanne', 'priceMax': 800000, 'type': 'SALE', 'limit': 10},
        headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Results: {len(data.get('listings', data.get('results', [])))}")
        print(json.dumps(data, indent=2)[:500])
except Exception as e:
    print(f"Error: {e}")

# 2. Try ImmoScout24 API
print("\n=== ImmoScout24 API ===")
try:
    r = requests.get('https://api.immoscout24.ch/v1/listings',
        params={'city': 'Lausanne', 'priceMax': 800000},
        headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    print(r.text[:300])
except Exception as e:
    print(f"Error: {e}")

# 3. Try NewHome API
print("\n=== NewHome API ===")
try:
    r = requests.get('https://www.newhome.ch/api/search/listings',
        params={'cities': 'Lausanne', 'priceMax': 800000},
        headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    print(r.text[:300])
except Exception as e:
    print(f"Error: {e}")

# 4. Try Comparis API
print("\n=== Comparis API ===")
try:
    r = requests.get('https://api.comparis.ch/immobilien/search',
        params={'city': 'Lausanne', 'maxPrice': 800000},
        headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    print(r.text[:300])
except Exception as e:
    print(f"Error: {e}")

# 5. Try immobilier.ch rent section
print("\n=== immobilier.ch RENT ===")
try:
    r = requests.get('https://www.immobilier.ch/en/rent/apartment/canton-vaud',
        headers={**headers, 'Referer': 'https://www.immobilier.ch/'}, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        prices = re.findall(r'CHF\s*[\d\s\']+', r.text)
        print(f"Prices found: {len(prices)}")
except Exception as e:
    print(f"Error: {e}")
