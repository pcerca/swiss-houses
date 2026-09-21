from playwright.sync_api import sync_playwright
import re
import time

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        page = context.new_page()
        
        # Check Lausanne page 2 as test case
        url = "https://www.immobilier.ch/en/buy/apartment/vaud/lausanne/page-2"
        page.goto(url, wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(5000)
        
        # Get JSON-LD
        json_ld = page.evaluate("""() => {
            const scripts = document.querySelectorAll('script[type="application/ld+json"]');
            for (const s of scripts) {
                try {
                    const d = JSON.parse(s.textContent);
                    if (d['@type'] === 'ItemList') return d;
                } catch(e) {}
            }
            return null;
        }""")
        
        if json_ld:
            print(f"JSON-LD ItemList found with {len(json_ld.get('itemListElement', []))} items")
            for item in json_ld.get('itemListElement', [])[:5]:
                print(f"  URL: {item.get('url', '')[:100]}")
        else:
            print("No JSON-LD ItemList found")
        
        # Get all listing cards
        print("\n--- Looking for listing cards ---")
        
        # Try to find listing containers
        cards = page.evaluate("""() => {
            // Look for common listing card patterns
            const results = [];
            
            // Method 1: Look for links that contain listing URLs
            const links = document.querySelectorAll('a[href*="/buy/apartment/"]');
            for (const link of links) {
                const href = link.href;
                const text = link.textContent.trim();
                if (text.length > 10 && text.length < 500) {
                    results.push({
                        href: href,
                        text: text.substring(0, 200),
                        parent: link.parentElement ? link.parentElement.className : ''
                    });
                }
            }
            
            return results;
        }""")
        
        print(f"Found {len(cards)} listing links")
        for i, card in enumerate(cards[:10]):
            print(f"\n  {i+1}. href: {card['href'][:100]}")
            print(f"     text: {card['text'][:150]}")
            print(f"     parent class: {card['parent'][:80]}")
        
        browser.close()

if __name__ == '__main__':
    main()
