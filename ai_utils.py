from rapidfuzz import fuzz
import imagehash
from PIL import Image
import io

# --- 1. AUTO-DESCRIPTION GENERATOR (NEW) ---
def generate_ai_description(name, loc, time, type):
    """
    Automatically creates a description based on inputs.
    """
    if not name or not loc:
        return "Please fill in the Item Name and Location to generate a description."
    
    action = "lost" if type == "LOST" else "found"
    time_str = f" around {time}" if time else ""
    
    if type == "LOST":
        return f"Urgent: I lost my {name} at {loc}{time_str}. It is very important to me. Please contact me if found."
    else:
        return f"I found a {name} at {loc}{time_str}. It is currently safe with me. Please contact me to claim it."

# --- 2. SENSITIVITY MASKING ---
def mask_sensitive_data(text, sensitivity):
    if sensitivity == "High":
        return "🔒 [Hidden Content] - Contact Owner to view."
    return text

# --- 3. IMAGE HASHING ---
def get_image_hash(uploaded_file):
    if uploaded_file is None: return None
    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        return str(imagehash.phash(img))
    except: return None

# --- 4. SENSITIVITY ANALYSIS ---
def analyze_sensitivity(desc):
    keywords = ["phone", "aadhaar", "passport", "credit", "card", "id", "password"]
    return "High" if any(k in desc.lower() for k in keywords) else "Normal"

# ==========================================
# 🧠 CORE MATCHING ENGINE
# ==========================================
def check_matches(target_name, target_loc, target_desc, target_img_hash, target_type, all_items_df):
    matches = []
    if all_items_df.empty: return matches

    # 1. Look for OPPOSITE type (Found <-> Lost)
    search_type = "LOST" if target_type == "FOUND" else "FOUND"
    candidates = all_items_df[all_items_df['report_type'] == search_type]

    # 2. Parse My Location
    try:
        t_parts = target_loc.split(',')
        t_state = t_parts[-1].strip().lower()
        t_city = t_parts[-2].strip().lower()
    except:
        t_state, t_city = "", ""

    for index, row in candidates.iterrows():
        score = 0
        
        # --- A. STRICT LOCATION CHECK ---
        try:
            c_parts = row['location'].split(',')
            c_state = c_parts[-1].strip().lower()
            c_city = c_parts[-2].strip().lower()
        except:
            c_state, c_city = "", ""

        # Reject if State or City doesn't match
        if t_state and c_state and t_state != c_state: continue
        if t_city and c_city and t_city != c_city: continue

        # --- B. NAME MATCHING ---
        name_score = fuzz.token_set_ratio(target_name.lower(), row['item_name'].lower())
        score += (name_score * 0.6)

        # --- C. IMAGE MATCHING ---
        if target_img_hash and row['image_hash']:
            try:
                h1 = imagehash.hex_to_hash(target_img_hash)
                h2 = imagehash.hex_to_hash(row['image_hash'])
                if (h1 - h2) <= 10: score += 40 
                elif (h1 - h2) <= 20: score += 20
            except: pass
        
        # --- D. DESCRIPTION MATCH ---
        desc_score = fuzz.token_set_ratio(target_desc, row['description'])
        score += (desc_score * 0.1)

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
