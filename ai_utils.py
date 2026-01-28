from rapidfuzz import fuzz
import imagehash
from PIL import Image
import io

# --- 1. SMART TEXT NORMALIZER ---
def normalize_text(text):
    """
    Cleans text to make matching easier.
    Ex: "Dark Black Wallet" -> "dark black wallet"
    """
    if not text: return ""
    return text.lower().strip()

# --- 2. GENERATE DESCRIPTION ---
def generate_ai_description(name, loc, time, type):
    action = "lost" if type == "LOST" else "found"
    time_str = f" around {time}" if time else ""
    return f"Urgent: I {action} a {name} at {loc}{time_str}. Please contact me."

# --- 3. IMAGE HASHING ---
def get_image_hash(uploaded_file):
    if uploaded_file is None: return None
    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        # Average hash is best for similar-looking objects
        return str(imagehash.average_hash(img))
    except: return None

# --- 4. SENSITIVITY ---
def mask_sensitive_data(text, sensitivity):
    if sensitivity == "High": return "🔒 [Hidden Content]"
    return text

def analyze_sensitivity(desc):
    keywords = ["aadhaar", "passport", "pan", "card", "password"]
    return "High" if any(k in desc.lower() for k in keywords) else "Normal"

# ==========================================
# 🧠 SMART MATCHING LOGIC
# ==========================================
def check_matches(target_name, target_loc, target_desc, target_img_hash, target_type, all_items_df):
    matches = []
    if all_items_df.empty: return matches

    # 1. SWAP LOGIC: If I reported LOST, look for FOUND (and vice versa)
    search_type = "FOUND" if target_type == "LOST" else "LOST"
    
    # 2. Filter Database
    candidates = all_items_df[all_items_df['report_type'] == search_type]

    # 3. Clean Inputs
    my_name = normalize_text(target_name)
    my_city = target_loc.split(',')[-2].strip().lower() if ',' in target_loc else ""

    for index, row in candidates.iterrows():
        score = 0
        
        # --- A. LOCATION CHECK ---
        # If the City is totally different, skip it.
        db_loc = row['location'].lower()
        if my_city and my_city not in db_loc:
            continue 

        # --- B. TEXT MATCHING (The "Dark Black Wallet" Fix) ---
        db_name = normalize_text(row['item_name'])
        
        # token_set_ratio is perfect here. 
        # It matches "Black Wallet" inside "Dark Black Wallet" as 100% match.
        name_score = fuzz.token_set_ratio(my_name, db_name)
        
        # Description check
        desc_score = fuzz.token_set_ratio(my_name, normalize_text(row['description']))
        
        # Use the best text score
        final_text_score = max(name_score, desc_score)
        
        score += (final_text_score * 0.7) # Text is 70% of score

        # --- C. IMAGE CHECK ---
        img_score = 0
        if target_img_hash and row['image_hash']:
            try:
                h1 = imagehash.hex_to_hash(target_img_hash)
                h2 = imagehash.hex_to_hash(row['image_hash'])
                if (h1 - h2) <= 5: img_score = 100  # Identical image
                elif (h1 - h2) <= 15: img_score = 80 # Similar image
            except: pass
        
        if img_score > 0:
            # If image matches, recalculate score with image weight
            score = (final_text_score * 0.4) + (img_score * 0.6)

        # --- FINAL THRESHOLD ---
        if score > 75: # Any match above 75% is worth showing
            matches.append({
                "id": row['id'],
                "email": row['email'],
                "contact_info": row['contact_info'],
                "item_name": row['item_name'],
                "description": row['description'],
                "location": row['location'],
                "score": int(score)
            })

    # Sort: Highest match first
    return sorted(matches, key=lambda x: x['score'], reverse=True)
