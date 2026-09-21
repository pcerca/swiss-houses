from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    url = 'https://www.immobilier.ch/en/buy/apartment/vaud/lausanne/sunimmo-1578/appartement-lausanne-avenue-rumine-1574747'
    page.goto(url, wait_until='networkidle', timeout=60000)
    page.wait_for_timeout(5000)
    
    title = page.title()
    print(f"Title: {title}")
    
    body = page.inner_text('body')
    print(f"\nBody text (first 500):")
    print(body[:500])
    
    import re
    prices = re.findall(r'CHF[\s]*[\d\x27]+', body)
    print(f"\nPrices found: {prices[:5]}")
    
    browser.close()
