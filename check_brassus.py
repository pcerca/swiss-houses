from playwright.sync_api import sync_playwright
import re

url = "https://www.immobilier.ch/en/buy/apartment/vaud/nyon/cologny-properties-3110/available-for-foreigner-brassus-vallee-joux-1600728"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36').new_page()
    page.goto(url, wait_until='domcontentloaded', timeout=20000)
    page.wait_for_timeout(4000)

    title = page.title()
    print(f"Title: {title}")

    # Get JSON-LD
    json_ld = page.evaluate("""() => {
        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
        for (const s of scripts) {
            try { return JSON.parse(s.textContent); } catch(e) {}
        }
        return null;
    }""")
    if json_ld:
        import json
        # Show location-related fields
        for key in ['address', 'name', 'description', 'areaServed', 'geo']:
            if key in json_ld:
                print(f"\n{key}: {json.dumps(json_ld[key], indent=2)[:300]}")

    body = page.inner_text('body')[:6000]
    print(f"\nBody length: {len(body)}")
    print(f"\nFirst 1500 chars:\n{body[:1500]}")

    browser.close()
