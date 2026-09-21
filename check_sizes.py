from playwright.sync_api import sync_playwright
import re

urls = [
    ('#14 Lausanne', 'https://www.immobilier.ch/en/buy/apartment/vaud/lausanne/properti-ag-2229/exceptional-duplex-in-mousquines-verdeil-with-garden-and-lake-1577734'),
    ('#11 Lausanne', 'https://www.immobilier.ch/en/buy/apartment/vaud/lausanne/properti-ag-2229/contemporary-address-in-the-heart-of-lausanne-1578013'),
    ('#18 Lausanne', 'https://www.immobilier.ch/en/buy/apartment/vaud/lausanne/rockwell-properties-2501/exceptional-apartment-at-an-exceptional-address-1569123'),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent='Mozilla/5.0')
    page = context.new_page()
    
    for label, url in urls:
        page.goto(url, wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)
        title = page.title()
        print(f'{label}: {title}')
    
    browser.close()
