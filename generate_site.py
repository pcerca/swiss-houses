import csv
import json
from datetime import date

INPUT_FILE = "vaud_apartments_final.csv"
RENT_FILE = "rent_data.json"

# Load rent data
with open(RENT_FILE, 'r', encoding='utf-8') as f:
    rent_data = json.load(f)

rent_stats = rent_data.get('stats', {})

# Mortgage constants (Swiss system)
MORTGAGE_RATE = 0.02       # 2.0% fixed
DOWN_PAYMENT_PCT = 0.20    # 20% minimum
OPERATING_COST_PCT = 0.01  # ~1% of property value/year (maintenance, insurance, taxes)
AMORT_YEARS = 15           # amortize to 65% LTV in 15 years
LTV_TARGET = 0.65          # 65% loan-to-value target
INCOME_RATIO = 0.33        # max 33% of gross income for housing

def calc_mortgage(price):
    """Calculate Swiss mortgage details"""
    down_payment = price * DOWN_PAYMENT_PCT
    loan = price - down_payment
    
    # Monthly interest
    monthly_interest = loan * MORTGAGE_RATE / 12
    
    # Monthly amortization (to reach 65% LTV in 15 years)
    target_loan = price * LTV_TARGET
    total_amort = loan - target_loan
    monthly_amort = total_amort / (AMORT_YEARS * 12) if total_amort > 0 else 0
    
    # Monthly operating costs (1% of property value / year)
    monthly_operating = price * OPERATING_COST_PCT / 12
    
    # Total monthly housing cost
    monthly_total = monthly_interest + monthly_amort + monthly_operating
    
    # Minimum gross annual income (33% rule)
    min_annual_income = (monthly_total * 12) / INCOME_RATIO
    
    return {
        'down_payment': round(down_payment),
        'loan': round(loan),
        'monthly_interest': round(monthly_interest),
        'monthly_amort': round(monthly_amort),
        'monthly_operating': round(monthly_operating),
        'monthly_total': round(monthly_total),
        'min_annual_income': round(min_annual_income),
        'min_monthly_income': round(min_annual_income / 12),
    }


def estimate_rent(city, size, condition=''):
    """Estimate monthly rent based on city median rent/m2"""
    city_key = city  # exact match
    if city_key not in rent_stats:
        # Fallback to overall average
        all_medians = [s['median_rent_m2'] for s in rent_stats.values()]
        if all_medians:
            rpm = sum(all_medians) / len(all_medians)
        else:
            rpm = 28  # default
    else:
        rpm = rent_stats[city_key]['median_rent_m2']
    
    # Adjust for condition
    if condition == 'renovated_modern':
        rpm *= 1.10  # +10% for renovated
    elif condition == 'needs_work':
        rpm *= 0.85  # -15% for needs work
    
    est_rent = round(rpm * size)
    return est_rent, round(rpm, 2)


def classify_listing(r):
    """Enhanced classification based on description/URL"""
    url = r.get('URL', '')
    occ = r.get('Occupancy', '')
    desc = r.get('Description', '')
    
    # Combine all text for analysis
    text = f"{url} {occ} {desc}".lower()
    
    status = 'vacant'
    flags = []
    
    # Life annuity / usufruit
    if any(w in text for w in ['life annuity', 'annuity', 'usufruit', 'bail.*vie']):
        status = 'life_annuity'
        flags.append('Life annuity')
    
    # Rented / tenant
    elif any(w in text for w in ['rented', 'tenant', 'locataire', 'loué', 'vermietet', 'occupied by']):
        status = 'rented'
        flags.append('Tenant in place')
    
    # Needs renovation
    if any(w in text for w in ['to renovate', 'needs renovation', 'à rénover', 'renovierung']):
        flags.append('Needs renovation')
        if 'needs_work' not in status:
            status = 'needs_work' if status == 'vacant' else status
    
    # New / under construction
    if any(w in text for w in ['new construction', 'neuf', 'neuve', 'under construction', 'en construction']):
        flags.append('New construction')
    
    return status, ', '.join(flags)


def calc_investment_score(price, size, ppm, rooms, condition, amenities, view_est, status):
    """Calculate investment score 0-100"""
    score = 0
    reasons = []
    
    # 1. Price/m2 value (35 pts)
    if ppm > 0:
        if ppm < 8000: score += 35; reasons.append(f"Excellent value CHF {ppm}/m2")
        elif ppm < 10000: score += 30; reasons.append(f"Great value CHF {ppm}/m2")
        elif ppm < 12000: score += 25; reasons.append(f"Good value CHF {ppm}/m2")
        elif ppm < 14000: score += 18; reasons.append(f"Fair value CHF {ppm}/m2")
        elif ppm < 16000: score += 12; reasons.append(f"Avg value CHF {ppm}/m2")
        else: score += 5; reasons.append(f"Expensive CHF {ppm}/m2")
    
    # 2. Size (15 pts)
    if size >= 100: score += 15; reasons.append(f"Large {size}m2")
    elif size >= 75: score += 12; reasons.append(f"Good size {size}m2")
    elif size >= 50: score += 8; reasons.append(f"Medium {size}m2")
    elif size >= 30: score += 5
    else: score += 2
    
    # 3. Condition (15 pts)
    if condition == 'renovated_modern': score += 15; reasons.append("Renovated")
    elif condition == 'well_lit': score += 10; reasons.append("Bright")
    elif condition == 'needs_work': score += 3; reasons.append("Needs work")
    
    # 4. Amenities (20 pts)
    if amenities: score += min(20, len(amenities) * 2)
    
    # 5. View (10 pts)
    if view_est == 'open_view': score += 10; reasons.append("Open view")
    elif view_est == 'garden_view': score += 5; reasons.append("Garden view")
    
    # 6. Rooms (5 pts)
    try:
        r = float(rooms)
        if 2.5 <= r <= 4.5: score += 5; reasons.append(f"{r}rm ideal")
        elif r > 4.5: score += 3
        else: score += 1
    except:
        pass
    
    # 7. Status penalty
    if status == 'life_annuity': score -= 40; reasons.append("CANNOT USE NOW")
    elif status == 'rented': score -= 15; reasons.append("Tenant in place")
    elif status == 'needs_work': score -= 5; reasons.append("Needs work")
    
    return max(0, min(100, score)), '; '.join(reasons)


def main():
    # Read sale listings
    rows = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    items = []
    for r in rows:
        try:
            price = int(r.get('Price (CHF)', 0) or 0)
            size = int(r.get('Size (m2)', 0) or 0)
            ppm = int(r.get('Price/m2 (CHF)', 0) or 0)
        except:
            continue
        
        if price == 0 or size == 0:
            continue
        
        city = r.get('City', '')
        rooms = r.get('Rooms', '')
        cond = r.get('Image_Condition', '')
        view = r.get('Image_View_Estimate', '')
        
        # Classify
        status, flags = classify_listing(r)
        
        # Occupancy override from scraper
        occ = r.get('Occupancy', '')
        if 'life annuity' in occ.lower():
            status = 'life_annuity'
        elif 'rented' in occ.lower():
            status = 'rented'
        
        # Amenities
        amenities = []
        for key, name in [('Parking','parking'), ('Cave/Cellar','cellar'), ('Balcony','balcony'),
                          ('Terrace','terrace'), ('Garden','garden'), ('Elevator','elevator'),
                          ('View','view'), ('Renovated','renovated')]:
            if r.get(key, ''):
                amenities.append(name)
        
        # Investment score
        score, reasons = calc_investment_score(price, size, ppm, rooms, cond, amenities, view, status)
        
        # Rent estimation
        est_rent, rent_m2 = estimate_rent(city, size, cond)
        
        # Yield
        gross_yield = round((est_rent * 12) / price * 100, 2) if price > 0 else 0
        
        # Mortgage
        mortgage = calc_mortgage(price)
        
        # Comparable rentals (same city, similar size)
        comparables = []
        if city in rent_stats:
            for rl in rent_stats[city].get('listings', []):
                if abs(rl['size'] - size) <= 20:  # within 20m2
                    comparables.append({
                        'price': rl['price'],
                        'size': rl['size'],
                        'rooms': rl.get('rooms', ''),
                    })
        
        items.append({
            'city': city,
            'npa': r.get('NPA', ''),
            'rooms': rooms,
            'size': size,
            'price': price,
            'ppm': ppm,
            'score': score,
            'status': status,
            'flags': flags,
            'amenities': amenities,
            'reasons': reasons,
            'est_rent': est_rent,
            'rent_m2': rent_m2,
            'gross_yield': gross_yield,
            'down_payment': mortgage['down_payment'],
            'loan': mortgage['loan'],
            'monthly_total': mortgage['monthly_total'],
            'min_annual_income': mortgage['min_annual_income'],
            'min_monthly_income': mortgage['min_monthly_income'],
            'comparables': comparables[:3],
            'url': r.get('URL', ''),
        })
    
    # Sort by score descending
    items.sort(key=lambda x: x['score'], reverse=True)
    
    data = {
        'generated': date.today().strftime('%Y-%m-%d'),
        'count': len(items),
        'rent_stats': {city: {'median': s['median_rent_m2'], 'avg': s['avg_rent_m2'], 'count': s['count']} 
                       for city, s in rent_stats.items()},
        'mortgage': {
            'rate': MORTGAGE_RATE,
            'down_pct': DOWN_PAYMENT_PCT,
            'operating_pct': OPERATING_COST_PCT,
            'amort_years': AMORT_YEARS,
            'income_ratio': INCOME_RATIO,
        },
        'items': items,
    }
    
    with open('docs/data/listings.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    
    print(f"Generated docs/data/listings.json with {len(items)} listings")
    print(f"\nRent stats by city:")
    for city, s in sorted(rent_stats.items()):
        print(f"  {city}: CHF {s['median_rent_m2']}/m2/month (median, {s['count']} listings)")
    
    print(f"\nTop 5 by investment score:")
    for i, item in enumerate(items[:5], 1):
        print(f"  {i}. {item['city']} CHF {item['price']} ({item['size']}m2) score={item['score']}")
        print(f"     Rent: CHF {item['est_rent']}/mo | Yield: {item['gross_yield']}%")
        print(f"     Down payment: CHF {item['down_payment']} | Monthly: CHF {item['monthly_total']}")
        print(f"     Min salary: CHF {item['min_annual_income']}/year")


if __name__ == '__main__':
    main()
