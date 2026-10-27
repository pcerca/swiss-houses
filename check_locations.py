import csv

with open('vaud_apartments_immobilier_ch_v2.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

print("Listings with suspicious locations:\n")
for i, row in enumerate(rows):
    url = row['URL'].lower()
    npa = row['NPA']
    suspicious = ('brassus' in url or 'joux' in url or 'vallee' in url or
                  'le-brassus' in url or npa.startswith('13') or npa.startswith('14'))
    if suspicious:
        print(f"{i+1}. [{row['City']}] NPA:{npa} | {row['Address']}")
        print(f"   URL: ...{row['URL'][-65:]}")
        print(f"   CHF {row['Price (CHF)']} / {row['Size (m2)']}m2\n")
