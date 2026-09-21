import csv
import os
import re
import time
import requests
from io import BytesIO
from PIL import Image
from collections import Counter

INPUT_FILE = "C:\\Users\\pedroc\\Documents\\swiss_houses\\vaud_apartments_immobilier_ch_v2.csv"
OUTPUT_FILE = "C:\\Users\\pedroc\\Documents\\swiss_houses\\vaud_apartments_final.csv"
IMAGES_DIR = "C:\\Users\\pedroc\\Documents\\swiss_houses\\property_images"

os.makedirs(IMAGES_DIR, exist_ok=True)


def download_image(url, save_path):
    try:
        resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(resp.content)
            return True
    except:
        pass
    return False


def analyze_image(img_path):
    try:
        img = Image.open(img_path)
        width, height = img.size
        
        # Resize for analysis
        img_small = img.resize((100, 100))
        pixels = list(img_small.getdata())
        
        # Color analysis
        r_avg = sum(p[0] for p in pixels) / len(pixels)
        g_avg = sum(p[1] for p in pixels) / len(pixels)
        b_avg = sum(p[2] for p in pixels) / len(pixels)
        
        # Brightness
        brightness = (r_avg + g_avg + b_avg) / 3
        
        # Detect dominant colors
        color_ranges = {
            'blue_sky': 0,
            'green_vegetation': 0,
            'brown_wood': 0,
            'white_wall': 0,
            'gray_concrete': 0,
            'red_roof': 0,
        }
        
        for r, g, b in pixels:
            if b > 150 and b > r and b > g:
                color_ranges['blue_sky'] += 1
            if g > 100 and g > r and g > b:
                color_ranges['green_vegetation'] += 1
            if r > 100 and g > 60 and b < 80 and r > g:
                color_ranges['brown_wood'] += 1
            if r > 200 and g > 200 and b > 200:
                color_ranges['white_wall'] += 1
            if 80 < r < 150 and 80 < g < 150 and 80 < b < 150:
                color_ranges['gray_concrete'] += 1
            if r > 150 and g < 100 and b < 100:
                color_ranges['red_roof'] += 1
        
        total = len(pixels)
        analysis = {
            'width': width,
            'height': height,
            'brightness': round(brightness, 1),
            'is_bright': brightness > 140,
            'has_blue': color_ranges['blue_sky'] / total > 0.15,
            'has_green': color_ranges['green_vegetation'] / total > 0.1,
            'has_wood': color_ranges['brown_wood'] / total > 0.1,
            'dominant_wall': color_ranges['white_wall'] / total > 0.3,
            'is_dark_interior': brightness < 100,
            'blue_ratio': round(color_ranges['blue_sky'] / total, 3),
            'green_ratio': round(color_ranges['green_vegetation'] / total, 3),
        }
        
        return analysis
    except Exception as e:
        return None


def infer_floor_from_images(images_analysis):
    if not images_analysis:
        return '', '', ''
    
    floors_detected = []
    view_type = []
    condition_clues = []
    
    for analysis in images_analysis:
        if analysis is None:
            continue
        
        # High brightness + blue sky = likely upper floor or good view
        if analysis['has_blue'] and analysis['blue_ratio'] > 0.2:
            view_type.append('sky_view')
        
        # Green vegetation visible = lower floor or garden view
        if analysis['has_green'] and analysis['green_ratio'] > 0.15:
            view_type.append('garden_view')
        
        # Very bright = lots of natural light (upper floor, south-facing)
        if analysis['is_bright']:
            condition_clues.append('bright')
        
        # Dark interior = possibly basement or ground floor
        if analysis['is_dark_interior']:
            condition_clues.append('dark_interior')
        
        # Wood detected = possibly renovated with wood floors
        if analysis['has_wood']:
            condition_clues.append('wood_floors')
    
    # Infer floor
    floor_estimate = ''
    if 'sky_view' in view_type and 'garden_view' not in view_type:
        floor_estimate = 'upper_floor'
    elif 'garden_view' in view_type and 'sky_view' not in view_type:
        floor_estimate = 'lower_floor'
    elif 'sky_view' in view_type and 'garden_view' in view_type:
        floor_estimate = 'middle_floor'
    
    # Infer view
    view_estimate = ''
    if 'sky_view' in view_type:
        view_estimate = 'open_view'
    if 'garden_view' in view_type:
        view_estimate = 'garden_view'
    
    # Infer condition
    condition = ''
    if 'bright' in condition_clues and 'wood_floors' in condition_clues:
        condition = 'renovated_modern'
    elif 'bright' in condition_clues:
        condition = 'well_lit'
    elif 'dark_interior' in condition_clues:
        condition = 'needs_work'
    
    return floor_estimate, view_estimate, condition


def main():
    # Read CSV
    rows = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    print(f"Analyzing images for {len(rows)} listings...\n")
    
    for i, row in enumerate(rows):
        images_str = row.get('Images', '')
        if not images_str:
            continue
        
        urls = [u.strip() for u in images_str.split(';') if u.strip()]
        if not urls:
            continue
        
        print(f"[{i+1}/{len(rows)}] {row.get('City', '')} - {len(urls)} images")
        
        # Download and analyze first 3 images
        analyses = []
        for j, url in enumerate(urls[:3]):
            img_path = os.path.join(IMAGES_DIR, f"listing_{i+1}_img_{j+1}.jpg")
            
            if download_image(url, img_path):
                analysis = analyze_image(img_path)
                if analysis:
                    analyses.append(analysis)
                    print(f"  Image {j+1}: {analysis['width']}x{analysis['height']}, brightness={analysis['brightness']}")
            
            time.sleep(0.5)
        
        # Infer properties from images
        floor_est, view_est, condition = infer_floor_from_images(analyses)
        
        if floor_est and not row.get('Floor'):
            row['Image_Floor_Estimate'] = floor_est
        else:
            row['Image_Floor_Estimate'] = ''
        
        if view_est:
            row['Image_View_Estimate'] = view_est
        else:
            row['Image_View_Estimate'] = ''
        
        if condition:
            row['Image_Condition'] = condition
        else:
            row['Image_Condition'] = ''
        
        # Check if images show lake view (lots of blue)
        has_lake_view = any(a['blue_ratio'] > 0.25 for a in analyses if a)
        if has_lake_view and not row.get('View'):
            row['View'] = 'Yes (from images)'
    
    # Save updated CSV
    headers = list(rows[0].keys())
    if 'Image_Floor_Estimate' not in headers:
        headers.extend(['Image_Floor_Estimate', 'Image_View_Estimate', 'Image_Condition'])
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nDone! Saved to {OUTPUT_FILE}")
    
    # Summary
    print("\nImage Analysis Summary:")
    floor_estimates = sum(1 for r in rows if r.get('Image_Floor_Estimate'))
    view_estimates = sum(1 for r in rows if r.get('Image_View_Estimate'))
    condition_estimates = sum(1 for r in rows if r.get('Image_Condition'))
    print(f"  Floor estimates: {floor_estimates}/{len(rows)}")
    print(f"  View estimates: {view_estimates}/{len(rows)}")
    print(f"  Condition estimates: {condition_estimates}/{len(rows)}")


if __name__ == '__main__':
    main()
