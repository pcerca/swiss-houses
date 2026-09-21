from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    url = 'https://www.immobilier.ch/en/buy/apartment/vaud/rolle/bernard-nicod-yverdon-456/new-45-room-penthouse-with-rooftop-terrace-1292372'
    page.goto(url, wait_until='networkidle', timeout=60000)
    page.wait_for_timeout(8000)
    
    # Check for any image URLs in the HTML
    import re
    html = page.content()
    img_urls = re.findall(r'https?://[^\s"<>]+\.(?:jpg|jpeg|png|webp)', html)
    print(f"Image URLs found in HTML: {len(img_urls)}")
    for u in img_urls[:10]:
        print(f"  {u[:200]}")
    
    # Check for lazy-loaded images
    imgs = page.evaluate("""() => {
        const all = document.querySelectorAll('*');
        const results = [];
        for (const el of all) {
            for (const attr of el.attributes) {
                if (attr.value && attr.value.includes('pic') || attr.value.includes('photo') || attr.value.includes('image')) {
                    if (attr.value.startsWith('http') || attr.value.startsWith('//')) {
                        results.push({tag: el.tagName, attr: attr.name, val: attr.value.substring(0,200)});
                    }
                }
            }
        }
        return results;
    }""")
    print(f"\nLazy-loaded image elements: {len(imgs)}")
    for i in imgs[:10]:
        print(f"  {i['tag']} [{i['attr']}]: {i['val']}")
    
    browser.close()
