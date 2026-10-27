from playwright.sync_api import sync_playwright
import re

# Try the homepages directly and navigate from there
tests = [
    ("Homegate", "https://www.homegate.ch/"),
    ("ImmoScout24", "https://www.immoscout24.ch/en"),
    ("NewHome", "https://www.newhome.ch/en/"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080}
    )
    page = context.new_page()

    for name, url in tests:
        try:
            resp = page.goto(url, wait_until='networkidle', timeout=20000)
            page.wait_for_timeout(3000)
            status = resp.status if resp else 'N/A'
            title = page.title()
            body = page.inner_text('body')[:2000]
            
            # Try to find search input
            search_inputs = page.query_selector_all('input[type="text"], input[type="search"], input[placeholder*="city"], input[placeholder*="ort"]')
            print(f"\n{name}: HTTP {status} | Title: {title}")
            print(f"  Search inputs: {len(search_inputs)}")
            if search_inputs:
                for si in search_inputs[:3]:
                    ph = si.get_attribute('placeholder') or ''
                    print(f"    placeholder: '{ph}'")
            
            # Get the actual page URL after redirects
            print(f"  Final URL: {page.url}")
            print(f"  Preview: {body[:200].replace(chr(10), ' ')}")
        except Exception as e:
            print(f"\n{name}: FAILED - {str(e)[:120]}")

    browser.close()
