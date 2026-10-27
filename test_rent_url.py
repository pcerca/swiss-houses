from playwright.sync_api import sync_playwright
import re
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    
    # Test the correct rental URL format (same as buy but /rent/)
    url = "https://www.immobilier.ch/en/rent/apartment/vaud/lausanne/page-1"
    page.goto(url, wait_until='domcontentloaded', timeout=20000)
    page.wait_for_timeout(3000)
    
    print(f"URL: {page.url}")
    
    # Get JSON-LD
    json_ld = page.evaluate("""() => {
        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
        const results = [];
        for (const s of scripts) {
            try {
                results.push(JSON.parse(s.textContent));
            } catch(e) {}
        }
        return results;
    }""")
    
    for jld in json_ld:
        t = jld.get('@type', '')
        print(f"\nJSON-LD type: {t}")
        if t == 'ItemList':
            items = jld.get('itemListElement', [])
            print(f"  Items: {len(items)}")
            for item in items[:3]:
                print(f"  URL: {item.get('url', 'N/A')}")
                print(f"  Name: {item.get('name', 'N/A')}")
        else:
            print(f"  {json.dumps(jld, indent=2)[:500]}")
    
    browser.close()
