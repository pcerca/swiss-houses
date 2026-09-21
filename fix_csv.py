import csv

INPUT_FILE = "C:\\Users\\pedroc\\Documents\\swiss_houses\\vaud_apartments_immobilier_ch_v2.csv"

def main():
    rows = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    print(f"Before: {len(rows)} rows")
    
    # Fix #3: Gland size 772 -> 72
    for row in rows:
        if row.get('Size (m2)') == '772':
            row['Size (m2)'] = '72'
            price = int(row.get('Price (CHF)', '0'))
            row['Price/m2 (CHF)'] = str(round(price / 72))
            print(f"Fixed Gland size: 772 -> 72")
    
    # Remove #20: Morges listing that's actually in Chene-Bougeries
    rows = [r for r in rows if '1564103' not in r.get('URL', '')]
    print(f"Removed Chene-Bougeries listing")
    
    print(f"After: {len(rows)} rows")
    
    headers = list(rows[0].keys())
    with open(INPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Saved to {INPUT_FILE}")
    
    # Print final summary
    print("\nFinal listings:")
    for i, r in enumerate(rows):
        print(f"  {i+1}. {r.get('City', '')} | CHF {r.get('Price (CHF)', '')} | {r.get('Size (m2)', '?')}m2 | {r.get('Rooms', '?')} rooms")

if __name__ == '__main__':
    main()
