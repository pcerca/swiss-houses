import csv

with open('vaud_apartments_final.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print("NPA data:")
for i, r in enumerate(rows):
    print(f"  {i+1}. {r.get('City')} | NPA: '{r.get('NPA', '')}' | Address: {r.get('Address', '')[:50]}")
