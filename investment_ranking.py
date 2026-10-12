import csv
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

INPUT_FILE = "C:\\Users\\pedroc\\Documents\\swiss_houses\\vaud_apartments_final.csv"
OUTPUT_FILE = "C:\\Users\\pedroc\\Documents\\swiss_houses\\vaud_apartments.xlsx"


def calc_investment_score(row):
    score = 0
    reasons = []

    # 1. Value per m2 (lower = better) - up to 35 points
    try:
        ppm = int(row.get('Price/m2 (CHF)', '0') or '0')
        if ppm > 0:
            if ppm < 8000:
                score += 35
                reasons.append(f"Excellent value: CHF {ppm}/m2 (way below average)")
            elif ppm < 10000:
                score += 30
                reasons.append(f"Great value: CHF {ppm}/m2")
            elif ppm < 12000:
                score += 25
                reasons.append(f"Good value: CHF {ppm}/m2")
            elif ppm < 14000:
                score += 18
                reasons.append(f"Fair value: CHF {ppm}/m2")
            elif ppm < 16000:
                score += 12
                reasons.append(f"Average value: CHF {ppm}/m2")
            else:
                score += 5
                reasons.append(f"Expensive: CHF {ppm}/m2")
    except:
        pass

    # 2. Size (larger = better for rental potential) - up to 15 points
    try:
        size = int(row.get('Size (m2)', '0') or '0')
        if size >= 100:
            score += 15
            reasons.append(f"Large apartment ({size}m2) - high rental appeal")
        elif size >= 75:
            score += 12
            reasons.append(f"Good size ({size}m2)")
        elif size >= 50:
            score += 8
            reasons.append(f"Medium size ({size}m2)")
        elif size >= 30:
            score += 5
        else:
            score += 2
    except:
        pass

    # 3. Condition - up to 15 points
    condition = row.get('Image_Condition', '')
    if condition == 'renovated_modern':
        score += 15
        reasons.append("Renovated/modern - no work needed")
    elif condition == 'well_lit':
        score += 10
        reasons.append("Bright and well-lit")
    elif condition == 'needs_work':
        score += 3
        reasons.append("Needs work - renovation costs")

    # 4. Amenities - up to 20 points
    amenity_names = {
        'Parking': 'Parking included',
        'Cave/Cellar': 'Cellar/storage',
        'Balcony': 'Balcony',
        'Terrace': 'Terrace',
        'Garden': 'Garden',
        'Elevator': 'Elevator',
        'View': 'Lake/panoramic view',
        'Renovated': 'Renovated',
    }
    found_amenities = []
    for key, name in amenity_names.items():
        if row.get(key, ''):
            score += 2
            found_amenities.append(name)
    if found_amenities:
        reasons.append(f"Amenities: {', '.join(found_amenities)}")

    # 5. View bonus - up to 10 points
    view = row.get('Image_View_Estimate', '')
    if view == 'open_view':
        score += 10
        reasons.append("Open view from images")
    elif view == 'garden_view':
        score += 5
        reasons.append("Garden view from images")

    # 6. Rooms - up to 5 points
    try:
        rooms = float(row.get('Rooms', '0') or '0')
        if 2.5 <= rooms <= 4.5:
            score += 5
            reasons.append(f"{rooms} rooms - optimal rental size")
        elif rooms > 4.5:
            score += 3
            reasons.append(f"{rooms} rooms - family rental appeal")
        else:
            score += 1
    except:
        pass

    # 7. Occupancy status - PENALTY (life annuity = can't use property)
    occupancy = row.get('Occupancy', '')
    if occupancy:
        occ_lower = occupancy.lower()
        if 'life annuity' in occ_lower:
            score -= 40
            reasons.append(f"WARNING: {occupancy} - property NOT usable now!")
        elif 'rented' in occ_lower:
            score -= 15
            reasons.append(f"Note: {occupancy} - income but not usable")
        elif 'occupied' in occ_lower:
            score -= 20
            reasons.append(f"WARNING: {occupancy} - property NOT usable now!")
        elif 'occupant' in occ_lower:
            score -= 15
            reasons.append(f"Note: {occupancy}")

    # Clamp score to 0-100
    score = max(0, min(100, score))

    return score, reasons


def get_rating(score):
    if score >= 70:
        return "Excellent"
    elif score >= 55:
        return "Very Good"
    elif score >= 40:
        return "Good"
    elif score >= 25:
        return "Fair"
    else:
        return "Poor"


def main():
    rows = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    for row in rows:
        score, reasons = calc_investment_score(row)
        row['_score'] = score
        row['_rating'] = get_rating(score)
        row['_reasons'] = '; '.join(reasons)

    scored_rows = sorted(rows, key=lambda r: r['_score'], reverse=True)

    # Load existing workbook
    try:
        wb = openpyxl.load_workbook(OUTPUT_FILE)
        if "Investment Ranking" in wb.sheetnames:
            del wb["Investment Ranking"]
    except:
        wb = openpyxl.Workbook()
        if "Sheet" in wb.sheetnames:
            del wb["Sheet"]

    ws = wb.create_sheet("Investment Ranking")

    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    rating_colors = {
        "Excellent": "00B050",
        "Very Good": "92D050",
        "Good": "FFEB9C",
        "Fair": "FFC000",
        "Poor": "FF0000",
    }

    investment_headers = ["#", "City", "NPA", "Rooms", "Size (m2)", "Price (CHF)",
                          "Price/m2 (CHF)", "Score", "Rating", "Occupancy", "Why this is a good investment", "URL"]

    for col, header in enumerate(investment_headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    for row_idx, row in enumerate(scored_rows, 2):
        rating = row['_rating']
        rating_color = rating_colors.get(rating, "FFFFFF")
        row_fill = PatternFill(start_color=rating_color, end_color=rating_color, fill_type="solid")

        values = [
            row_idx - 1,
            row.get('City', ''),
            row.get('NPA', ''),
            row.get('Rooms', ''),
            int(row.get('Size (m2)', 0) or 0),
            int(row.get('Price (CHF)', 0) or 0),
            int(row.get('Price/m2 (CHF)', 0) or 0),
            row['_score'],
            rating,
            row.get('Occupancy', ''),
            row['_reasons'],
            row.get('URL', ''),
        ]

        for col_idx, value in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = thin_border
            cell.fill = row_fill

            if col_idx in [5, 6, 7]:
                cell.number_format = '#,##0'
            if col_idx == 1:
                cell.alignment = Alignment(horizontal="center")
            if col_idx == 8:
                cell.alignment = Alignment(horizontal="center")
                cell.font = Font(bold=True, size=12)
            if col_idx == 9:
                cell.alignment = Alignment(horizontal="center")
                cell.font = Font(bold=True)
            if col_idx == 10:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                if value:
                    cell.font = Font(bold=True, color="FF0000")
            if col_idx == 11:
                cell.alignment = Alignment(wrap_text=True, vertical="top")

    widths = [5, 14, 8, 8, 10, 14, 14, 8, 12, 30, 65, 50]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    ws.freeze_panes = 'A2'

    if "Sheet" in wb.sheetnames and len(wb.sheetnames) > 1:
        del wb["Sheet"]

    wb.save(OUTPUT_FILE)
    print(f"Saved to {OUTPUT_FILE}")

    print("\nInvestment Ranking with reasons:")
    for i, row in enumerate(scored_rows, 1):
        print(f"\n{i}. [{row['_rating']}] {row.get('City','')} CHF {row.get('Price (CHF)','')} - Score: {row['_score']}")
        print(f"   {row['_reasons']}")


if __name__ == '__main__':
    main()
