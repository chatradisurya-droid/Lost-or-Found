from rapidfuzz import fuzz
import imagehash
from PIL import Image
import io

# --- 1. SENSITIVITY MASKING ---
def mask_sensitive_data(text, sensitivity):
    if sensitivity == "High":
        return "🔒 [Hidden Content] - Contact Owner to view."
    return text

# --- 2. IMAGE HASHING ---
def get_image_hash(uploaded_file):
    if uploaded_file is None: return None
    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        return str(imagehash.phash(img))
    except: return None

# --- 3. AUTO-DESCRIPTION ---
def generate_ai_description(name, loc, time, type):
    return f"Urgent: I {type.lower()} a {name} at {loc} around {time}. Please contact me."

# --- 4. SENSITIVITY ---
def analyze_sensitivity(desc):
    keywords = ["phone", "aadhaar", "passport", "credit", "card", "id"]
    return "High" if any(k in desc.lower() for k in keywords) else "Normal"

# ==========================================
# 🧠 CORE MATCHING ENGINE
# ==========================================
def check_matches(target_name, target_loc, target_desc, target_img_hash, target_type, all_items_df):
    matches = []
    if all_items_df.empty: return matches

    # 1. SWAP TYPE: If I found it, look for who lost it.
    search_type = "LOST" if target_type == "FOUND" else "FOUND"
    
    # 2. Filter DB: Only look at the OPPOSITE report type
    candidates = all_items_df[all_items_df['report_type'] == search_type]

    # 3. Parse My Location
    try:
        t_parts = target_loc.split(',')
        t_state = t_parts[-1].strip().lower()
        t_city = t_parts[-2].strip().lower()
    except:
        t_state, t_city = "", ""

    for index, row in candidates.iterrows():
        score = 0
        
        # --- A. STRICT LOCATION CHECK ---
        # If State or City is different -> BLOCK MATCH
        try:
            c_parts = row['location'].split(',')
            c_state = c_parts[-1].strip().lower()
            c_city = c_parts[-2].strip().lower()
        except:
            c_state, c_city = "", ""

        if t_state and c_state and t_state != c_state: continue
        if t_city and c_city and t_city != c_city: continue

        # --- B. NAME MATCHING ---
        name_score = fuzz.token_set_ratio(target_name.lower(), row['item_name'].lower())
        score += (name_score * 0.6) # Name is 60% of value

        # --- C. IMAGE MATCHING ---
        if target_img_hash and row['image_hash']:
            try:
                h1 = imagehash.hex_to_hash(target_img_hash)
                h2 = imagehash.hex_to_hash(row['image_hash'])
                if (h1 - h2) <= 10: # Very similar image
                    score += 40 
                elif (h1 - h2) <= 20: 
                    score += 20
            except: pass
        
        # --- D. DESCRIPTION MATCH ---
        desc_score = fuzz.token_set_ratio(target_desc, row['description'])
        score += (desc_score * 0.1) # Small boost for description

        # --- FINAL THRESHOLD (> 80%) ---
        if score > 80:
            matches.append({
                "id": row['id'],
                "email": row['email'],
                "contact_info": row['contact_info'],
                "item_name": row['item_name'],
                "description": row['description'],
                "location": row['location'],
                "score": int(score)
            })

    return sorted(matches, key=lambda x: x['score'], reverse=True)
