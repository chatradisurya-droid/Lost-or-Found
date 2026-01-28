from rapidfuzz import fuzz
import imagehash
from PIL import Image
import io

# --- 1. CLEAN TEXT ---
def normalize_text(text):
    """
    Standardizes text.
    "Dark Black Wallet" -> "dark black wallet"
    "Mobile Phone" -> "phone"
    """
    if not text: return ""
    text = text.lower().strip()
    
    # Synonyms mapping
    synonyms = {
        "mobile": "phone", "cellphone": "phone", "iphone": "phone",
        "purse": "wallet", "pouch": "wallet", "moneybag": "wallet",
        "bag": "backpack", "laptop": "computer", "macbook": "computer"
    }
    
    words = text.split()
    fixed_words = [synonyms.get(w, w) for w in words]
    return " ".join(fixed_words)

# --- 2. LOCATION MATCHER (FIXED) ---
def check_location_match(loc1, loc2):
    """
    Checks if locations match even if written differently.
    Ex: "Benz Circle" matches "Benz Circle, Vijayawada"
    """
    l1 = normalize_text(loc1)
    l2 = normalize_text(loc2)
    
    # 1. Fuzzy Token Match (Handles "Benz Circle" inside "Benz Circle, Vja")
    ratio = fuzz.token_set_ratio(l1, l2)
    
    # If match is > 70%, we consider it the same place
    return ratio > 70

# --- 3. AUTO DESCRIPTION ---
def generate_ai_description(name, loc, time, type):
    action = "lost" if type == "LOST" else "found"
    t_str = f" around {time}" if time else ""
    return f"Urgent: I {action} a {name} at {loc}{t_str}. Please contact me."

# --- 4. IMAGE HASH ---
def get_image_hash(uploaded_file):
    if uploaded_file is None: return None
    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        return str(imagehash.average_hash(img))
    except: return None

# --- 5. SENSITIVITY ---
def analyze_sensitivity(desc):
    keywords = ["aadhaar", "pan", "passport", "credit", "debit", "pin"]
    return "High" if any(k in desc.lower() for k in keywords) else "Normal"
    
def mask_sensitive_data(text, sens):
    return "🔒 [Hidden]" if sens == "High" else text

# ==========================================
# 🧠 CORE MATCHING ENGINE
# ==========================================
def check_matches(target_name, target_loc, target_desc, target_img_hash, target_type, all_items_df):
    matches = []
    if all_items_df.empty: return matches

    # 1. Look for OPPOSITE type
    # If I am LOST, look for FOUND. If I am FOUND, look for LOST.
    search_type = "FOUND" if target_type == "LOST" else "LOST"
    candidates = all_items_df[all_items_df['report_type'] == search_type]

    # 2. My Data
    my_name = normalize_text(target_name)
    
    for index, row in candidates.iterrows():
        score = 0
        
        # --- STEP A: LOCATION CHECK ---
        # If locations are totally different, skip immediately
        if not check_location_match(target_loc, row['location']):
            continue 

        # --- STEP B: NAME MATCHING ("Dark Black Wallet" vs "Black Wallet") ---
        db_name = normalize_text(row['item_name'])
        
        # token_set_ratio handles subsets. 
        # "black wallet" is a subset of "dark black wallet" -> Score 100
        name_score = fuzz.token_set_ratio(my_name, db_name)
        
        # Description check (backup)
        desc_score = fuzz.token_set_ratio(my_name, normalize_text(row['description']))
        
        # Take best text score
        final_text_score = max(name_score, desc_score)
        
        # Weight: Text is 70% of the match
        score += (final_text_score * 0.7)

        # --- STEP C: IMAGE MATCHING ---
        img_score = 0
        if target_img_hash and row['image_hash']:
            try:
                h1 = imagehash.hex_to_hash(target_img_hash)
                h2 = imagehash.hex_to_hash(row['image_hash'])
                if (h1 - h2) <= 5: img_score = 100
                elif (h1 - h2) <= 15: img_score = 80
            except: pass
        
        if img_score > 0:
            score = (final_text_score * 0.4) + (img_score * 0.6)

        # --- MATCH THRESHOLD ---
        # Any score > 75 is a valid match to show
        if score > 75:
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
