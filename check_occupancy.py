import csv

with open('vaud_apartments_immobilier_ch_v2.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print("=== Occupancy flags ===")
for i, r in enumerate(rows):
    occ = r.get('Occupancy', '')
    if occ:
        print(f"  {i+1}. [{r.get('City')}] CHF {r.get('Price (CHF)')} - {occ}")
print(f"\nTotal: {sum(1 for r in rows if r.get('Occupancy',''))} listings with occupancy flags out of {len(rows)}")
