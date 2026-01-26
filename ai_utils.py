import pandas as pd
from rapidfuzz import fuzz
import imagehash
from PIL import Image
import io

# --- 1. SENSITIVITY MASKING ---
def mask_sensitive_data(text, sensitivity):
    if sensitivity == "High":
        return "🔒 [Hidden Content] - Contact Owner to view."
    return text

# --- 2. ADVANCED IMAGE HASHING ---
def get_image_hash(uploaded_file):
    """
    Generates a perceptual hash. 
    Unlike MD5, this allows finding 'similar' images (resized, cropped).
    """
    if uploaded_file is None:
        return None
    try:
        # Reset file pointer to beginning
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        # Calculate Perceptual Hash
        phash = imagehash.phash(img)
        return str(phash)
    except Exception as e:
        return None

# --- 3. AUTO-DESCRIPTION ---
def generate_ai_description(name, loc, time, type):
    return f"I {type.lower()} a {name} at {loc} around {time}. Please contact me if it belongs to you."

# --- 4. SENSITIVITY ANALYSIS ---
def analyze_sensitivity(desc):
    sensitive_keywords = ["phone", "aadhaar", "passport", "credit card", "password", "id card"]
    desc_lower = desc.lower()
    for word in sensitive_keywords:
        if word in desc_lower:
            return "High"
    return "Normal"

# ==========================================
# 🧠 CORE MATCHING ENGINE (TEXT + IMAGE)
# ==========================================
def check_matches(target_name, target_loc, target_desc, target_img_hash, target_type, all_items_df):
    matches = []
    if all_items_df.empty: return matches

    # 1. Look for the opposite type (Found <-> Lost)
    search_type = "LOST" if target_type == "FOUND" else "FOUND"
    candidates = all_items_df[all_items_df['report_type'] == search_type]

    # 2. Parse Target Location
    try:
        t_parts = target_loc.split(',')
        t_state = t_parts[-1].strip().lower()
        t_city = t_parts[-2].strip().lower()
        t_area = t_parts[-3].strip().lower()
    except:
        t_state, t_city, t_area = "", "", ""

    for index, row in candidates.iterrows():
        score = 0
        
        # --- A. STRICT LOCATION FILTER ---
        try:
            c_parts = row['location'].split(',')
            c_state = c_parts[-1].strip().lower()
            c_city = c_parts[-2].strip().lower()
        except:
            continue # Skip if location format is bad

        # If State or City is different, INSTANT REJECT
        if t_state and c_state and t_state != c_state: continue
        if t_city and c_city and t_city != c_city: continue
            
        # --- B. TEXT MATCHING (Base Score) ---
        name_score = fuzz.partial_ratio(target_name.lower(), row['item_name'].lower())
        desc_score = fuzz.token_sort_ratio(target_desc, row['description'])
        
        # Weighted Text Score
        text_score = (name_score * 0.6) + (desc_score * 0.4)
        
        # --- C. IMAGE MATCHING (Bonus Score) ---
        img_score = 0
        has_image_match = False
        
        if target_img_hash and row['image_hash']:
            try:
                # Calculate Hamming Distance between hashes
                # 0 = Exact Match, < 10 = Very Similar, > 20 = Different
                h1 = imagehash.hex_to_hash(target_img_hash)
                h2 = imagehash.hex_to_hash(row['image_hash'])
                diff = h1 - h2 
                
                if diff == 0: img_score = 100
                elif diff < 10: img_score = 80
                elif diff < 20: img_score = 50
                
                if img_score > 60: has_image_match = True
            except:
                pass

        # --- D. FINAL SCORE CALCULATION ---
        if has_image_match:
            # If images match, it boosts confidence significantly
            final_score = (text_score * 0.5) + (img_score * 0.5)
        else:
            final_score = text_score

        # --- THRESHOLD ---
        if final_score > 65:
            matches.append({
                "id": row['id'],
                "email": row['email'], # Needed for notification
                "contact_info": row['contact_info'], # Needed for sharing
                "item_name": row['item_name'],
                "description": row['description'],
                "location": row['location'],
                "score": int(final_score)
            })

    return sorted(matches, key=lambda x: x['score'], reverse=True)
