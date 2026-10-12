import csv
import json

INPUT_FILE = "C:\\Users\\pedroc\\Documents\\swiss_houses\\vaud_apartments_final.csv"

rows = []
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vaud Apartments Under CHF 800k</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; }
        .header h1 { font-size: 2rem; margin-bottom: 0.5rem; }
        .header p { opacity: 0.9; }
        .container { max-width: 1400px; margin: 0 auto; padding: 1rem; }
        .controls { background: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; }
        .controls select, .controls input { padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; }
        .controls input { flex: 1; min-width: 200px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1rem; }
        .stat-card { background: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-card .value { font-size: 1.5rem; font-weight: bold; color: #667eea; }
        .stat-card .label { font-size: 0.875rem; color: #666; margin-top: 0.25rem; }
        .listings { display: grid; gap: 1rem; }
        .listing { background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: transform 0.2s, box-shadow 0.2s; }
        .listing:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }
        .listing-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem; }
        .listing-title { font-size: 1.25rem; font-weight: bold; color: #333; }
        .listing-price { font-size: 1.5rem; font-weight: bold; color: #667eea; }
        .listing-details { display: flex; gap: 1.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
        .detail { display: flex; align-items: center; gap: 0.5rem; }
        .detail-icon { color: #667eea; }
        .badges { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }
        .badge { padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; font-weight: 500; }
        .badge-excellent { background: #d4edda; color: #155724; }
        .badge-very-good { background: #d4edda; color: #155724; }
        .badge-good { background: #fff3cd; color: #856404; }
        .badge-fair { background: #ffeaa7; color: #856404; }
        .badge-poor { background: #f8d7da; color: #721c24; }
        .badge-warning { background: #f8d7da; color: #721c24; font-weight: bold; }
        .badge-info { background: #d1ecf1; color: #0c5460; }
        .badge-amenity { background: #e2e3e5; color: #383d41; }
        .listing-reasons { background: #f8f9fa; padding: 1rem; border-radius: 4px; margin-top: 1rem; font-size: 0.9rem; color: #555; }
        .listing-url { display: inline-block; margin-top: 1rem; color: #667eea; text-decoration: none; font-weight: 500; }
        .listing-url:hover { text-decoration: underline; }
        .score-badge { display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; font-weight: bold; color: white; font-size: 0.9rem; }
        .score-excellent { background: #28a745; }
        .score-very-good { background: #20c997; }
        .score-good { background: #ffc107; }
        .score-fair { background: #fd7e14; }
        .score-poor { background: #dc3545; }
        @media (min-width: 768px) { .listings { grid-template-columns: repeat(2, 1fr); } }
        @media (min-width: 1200px) { .listings { grid-template-columns: repeat(3, 1fr); } }
    </style>
</head>
<body>
    <div class="header">
        <h1>Vaud Apartments Under CHF 800k</h1>
        <p>Investment analysis from immobilier.ch | Updated: __DATE__</p>
    </div>
    <div class="container">
        <div class="stats" id="stats"></div>
        <div class="controls">
            <input type="text" id="search" placeholder="Search by city, NPA..." oninput="filterListings()">
            <select id="cityFilter" onchange="filterListings()">
                <option value="">All Cities</option>
                <option value="Nyon">Nyon</option>
                <option value="Rolle">Rolle</option>
                <option value="Gland">Gland</option>
                <option value="Lausanne">Lausanne</option>
                <option value="Morges">Morges</option>
            </select>
            <select id="sortFilter" onchange="filterListings()">
                <option value="score">Sort by Investment Score</option>
                <option value="price">Sort by Price (low to high)</option>
                <option value="ppm">Sort by Price/m2 (low to high)</option>
                <option value="size">Sort by Size (high to low)</option>
            </select>
            <select id="statusFilter" onchange="filterListings()">
                <option value="">All Status</option>
                <option value="vacant">Vacant Only</option>
                <option value="flagged">Flagged Only</option>
            </select>
        </div>
        <div class="listings" id="listings"></div>
    </div>

    <script>
        const listings = __DATA__;

        function getScoreClass(score) {
            if (score >= 70) return 'excellent';
            if (score >= 55) return 'very-good';
            if (score >= 40) return 'good';
            if (score >= 25) return 'fair';
            return 'poor';
        }

        function getRating(score) {
            if (score >= 70) return 'Excellent';
            if (score >= 55) return 'Very Good';
            if (score >= 40) return 'Good';
            if (score >= 25) return 'Fair';
            return 'Poor';
        }

        function renderStats() {
            const total = listings.length;
            const avgPrice = Math.round(listings.reduce((s, l) => s + l.price, 0) / total);
            const avgPPM = Math.round(listings.reduce((s, l) => s + l.ppm, 0) / total);
            const vacant = listings.filter(l => !l.occupancy).length;
            const excellent = listings.filter(l => l.score >= 70).length;

            document.getElementById('stats').innerHTML = `
                <div class="stat-card"><div class="value">${total}</div><div class="label">Total Listings</div></div>
                <div class="stat-card"><div class="value">CHF ${avgPrice.toLocaleString()}</div><div class="label">Avg Price</div></div>
                <div class="stat-card"><div class="value">CHF ${avgPPM.toLocaleString()}/m2</div><div class="label">Avg Price/m2</div></div>
                <div class="stat-card"><div class="value">${vacant}</div><div class="label">Vacant (Usable Now)</div></div>
                <div class="stat-card"><div class="value">${excellent}</div><div class="label">Excellent Investments</div></div>
            `;
        }

        function renderListings(filtered) {
            const container = document.getElementById('listings');
            container.innerHTML = filtered.map(l => {
                const scoreClass = getScoreClass(l.score);
                const rating = getRating(l.score);
                const occBadge = l.occupancy ? `<span class="badge badge-warning">⚠ ${l.occupancy}</span>` : '<span class="badge badge-info">Vacant</span>';
                const amenityBadges = l.amenities.map(a => `<span class="badge badge-amenity">${a}</span>`).join('');
                return `
                    <div class="listing">
                        <div class="listing-header">
                            <div>
                                <div class="listing-title">${l.city}${l.npa ? ' (' + l.npa + ')' : ''}</div>
                                <div class="listing-details">
                                    <span class="detail">🛏 ${l.rooms} rooms</span>
                                    <span class="detail">📐 ${l.size}m2</span>
                                    <span class="detail">💰 CHF ${l.ppm.toLocaleString()}/m2</span>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div class="listing-price">CHF ${l.price.toLocaleString()}</div>
                                <div class="score-badge score-${scoreClass}" title="Investment Score">${l.score}</div>
                            </div>
                        </div>
                        <div class="badges">
                            <span class="badge badge-${scoreClass}">${rating}</span>
                            ${occBadge}
                            ${amenityBadges}
                        </div>
                        <div class="listing-reasons">${l.reasons}</div>
                        <a href="${l.url}" target="_blank" class="listing-url">View on immobilier.ch →</a>
                    </div>
                `;
            }).join('');
        }

        function filterListings() {
            const search = document.getElementById('search').value.toLowerCase();
            const city = document.getElementById('cityFilter').value;
            const sort = document.getElementById('sortFilter').value;
            const status = document.getElementById('statusFilter').value;

            let filtered = listings.filter(l => {
                if (search && !l.city.toLowerCase().includes(search) && !l.npa.includes(search)) return false;
                if (city && l.city !== city) return false;
                if (status === 'vacant' && l.occupancy) return false;
                if (status === 'flagged' && !l.occupancy) return false;
                return true;
            });

            filtered.sort((a, b) => {
                if (sort === 'score') return b.score - a.score;
                if (sort === 'price') return a.price - b.price;
                if (sort === 'ppm') return a.ppm - b.ppm;
                if (sort === 'size') return b.size - a.size;
                return 0;
            });

            renderListings(filtered);
        }

        renderStats();
        filterListings();
    </script>
</body>
</html>"""

from datetime import date
today = date.today().strftime("%B %d, %Y")

# Prepare data for JS
js_data = []
for r in rows:
    try:
        price = int(r.get('Price (CHF)', 0) or 0)
        size = int(r.get('Size (m2)', 0) or 0)
        ppm = int(r.get('Price/m2 (CHF)', 0) or 0)
    except:
        continue

    # Calculate score (same logic as investment_ranking.py)
    score = 0
    reasons = []

    if ppm > 0:
        if ppm < 8000: score += 35; reasons.append(f"Excellent value: CHF {ppm}/m2")
        elif ppm < 10000: score += 30; reasons.append(f"Great value: CHF {ppm}/m2")
        elif ppm < 12000: score += 25; reasons.append(f"Good value: CHF {ppm}/m2")
        elif ppm < 14000: score += 18; reasons.append(f"Fair value: CHF {ppm}/m2")
        elif ppm < 16000: score += 12; reasons.append(f"Average value: CHF {ppm}/m2")
        else: score += 5; reasons.append(f"Expensive: CHF {ppm}/m2")

    if size >= 100: score += 15; reasons.append(f"Large ({size}m2)")
    elif size >= 75: score += 12; reasons.append(f"Good size ({size}m2)")
    elif size >= 50: score += 8; reasons.append(f"Medium ({size}m2)")
    elif size >= 30: score += 5
    else: score += 2

    cond = r.get('Image_Condition', '')
    if cond == 'renovated_modern': score += 15; reasons.append("Renovated/modern")
    elif cond == 'well_lit': score += 10; reasons.append("Bright")
    elif cond == 'needs_work': score += 3; reasons.append("Needs work")

    amenities = []
    for key, name in [('Parking','Parking'), ('Cave/Cellar','Cellar'), ('Balcony','Balcony'),
                      ('Terrace','Terrace'), ('Garden','Garden'), ('Elevator','Elevator'),
                      ('View','View'), ('Renovated','Renovated')]:
        if r.get(key, ''):
            score += 2
            amenities.append(name)

    view = r.get('Image_View_Estimate', '')
    if view == 'open_view': score += 10; reasons.append("Open view")
    elif view == 'garden_view': score += 5; reasons.append("Garden view")

    try:
        rooms = float(r.get('Rooms', '0') or '0')
        if 2.5 <= rooms <= 4.5: score += 5; reasons.append(f"{rooms} rooms - optimal")
        elif rooms > 4.5: score += 3; reasons.append(f"{rooms} rooms")
        else: score += 1
    except:
        rooms = r.get('Rooms', '')

    occ = r.get('Occupancy', '')
    if occ:
        if 'life annuity' in occ.lower():
            score -= 40; reasons.append(f"WARNING: {occ}")
        elif 'rented' in occ.lower():
            score -= 15; reasons.append(f"Note: {occ}")
        elif 'occupied' in occ.lower():
            score -= 20; reasons.append(f"WARNING: {occ}")

    score = max(0, min(100, score))

    js_data.append({
        'city': r.get('City', ''),
        'npa': r.get('NPA', ''),
        'rooms': r.get('Rooms', ''),
        'size': size,
        'price': price,
        'ppm': ppm,
        'score': score,
        'occupancy': occ,
        'amenities': amenities,
        'reasons': '; '.join(reasons),
        'url': r.get('URL', ''),
    })

html = html.replace('__DATA__', json.dumps(js_data))
html = html.replace('__DATE__', today)

with open('docs/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Generated docs/index.html with {len(js_data)} listings")
