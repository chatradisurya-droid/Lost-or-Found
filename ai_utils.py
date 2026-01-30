from rapidfuzz import fuzz
import imagehash
from PIL import Image
import io

# --- 1. CLEAN TEXT ---
def normalize_text(text):
    if not text: return ""
    # Remove punctuation for better matching (a.p. vs ap)
    text = text.lower().replace(".", "").replace(",", " ").strip()
    
    synonyms = {
        "mobile": "phone", "cellphone": "phone", "iphone": "phone",
        "purse": "wallet", "pouch": "wallet", "moneybag": "wallet",
        "bag": "backpack", "laptop": "computer"
    }
    words = text.split()
    fixed_words = [synonyms.get(w, w) for w in words]
    return " ".join(fixed_words)

# --- 2. GENERATE DESCRIPTION ---
def generate_ai_description(name, loc, time, type):
    action = "lost" if type == "LOST" else "found"
    t_str = f" around {time}" if time else ""
    return f"Urgent: I {action} a {name} at {loc}{t_str}. Please contact me."

# --- 3. IMAGE HASH ---
def get_image_hash(uploaded_file):
    if uploaded_file is None: return None
    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        return str(imagehash.average_hash(img))
    except: return None

# --- 4. SENSITIVITY ---
def analyze_sensitivity(desc):
    keywords = ["aadhaar", "pan", "passport", "credit", "debit", "pin"]
    return "High" if any(k in desc.lower() for k in keywords) else "Normal"

def mask_sensitive_data(text, sens):
    return "🔒 [Hidden]" if sens == "High" else text

# ==========================================
# 🧠 ROBUST MATCHING ENGINE (WEIGHTED)
# ==========================================
def check_matches(target_name, target_loc, target_desc, target_img_hash, target_type, all_items_df):
    matches = []
    if all_items_df.empty: return matches

    # 1. Look for OPPOSITE type
    search_type = "FOUND" if target_type == "LOST" else "LOST"
    candidates = all_items_df[all_items_df['report_type'] == search_type]

    # 2. Normalize Inputs
    my_name = normalize_text(target_name)
    my_loc = normalize_text(target_loc)
    my_desc = normalize_text(target_desc)

    for index, row in candidates.iterrows():
        # Normalize DB Data
        db_name = normalize_text(row['item_name'])
        db_loc = normalize_text(row['location'])
        db_desc = normalize_text(row['description'])
        
        # --- SCORING WEIGHTS ---
        
        # A. NAME (60%) - Uses token_set_ratio (Handles "Black Wallet" inside "Dark Black Wallet")
        name_score = fuzz.token_set_ratio(my_name, db_name)
        
        # B. LOCATION (25%) - Uses token_set_ratio (Handles "Benz Circle" inside "Benz Circle, Vijayawada")
        # Even if "enz circle", score will be decent (e.g. 80-90)
        loc_score = fuzz.token_set_ratio(my_loc, db_loc)
        
        # C. DESCRIPTION (5%)
        desc_score = fuzz.token_set_ratio(my_desc, db_desc)
        
        # D. IMAGE (10% Bonus)
        img_score = 0
        if target_img_hash and row['image_hash']:
            try:
                h1 = imagehash.hex_to_hash(target_img_hash)
                h2 = imagehash.hex_to_hash(row['image_hash'])
                if (h1 - h2) <= 10: img_score = 100
            except: pass

        # --- CALCULATE FINAL WEIGHTED SCORE ---
        # Formula: Name(0.6) + Loc(0.25) + Desc(0.05) + Img(0.1)
        final_score = (name_score * 0.6) + (loc_score * 0.25) + (desc_score * 0.05) + (img_score * 0.1)
        
        # --- SMART BOOST ---
        # If Name is PERFECT (100), ensure score is high even if location is bad
        if name_score == 100:
            final_score = max(final_score, 85)

        # --- THRESHOLD ---
        # Show anything above 60%
        if final_score > 60:
            matches.append({
                "id": row['id'],
                "email": row['email'],
                "contact_info": row['contact_info'],
                "item_name": row['item_name'],
                "description": row['description'],
                "location": row['location'],
                "score": int(final_score)
            })

    return sorted(matches, key=lambda x: x['score'], reverse=True)
