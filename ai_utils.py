from rapidfuzz import fuzz
import imagehash
from PIL import Image
import io

# --- 1. SMART TEXT NORMALIZER ---
def normalize_text(text):
    """
    Converts text to lowercase and swaps synonyms.
    Ex: "I lost my Cellphone" -> "i lost my phone"
    """
    if not text: return ""
    text = text.lower().strip()
    
    # Synonyms Dictionary
    synonyms = {
        "mobile": "phone", "cellphone": "phone", "iphone": "phone", "android": "phone",
        "purse": "wallet", "pouch": "wallet", "billfold": "wallet",
        "specs": "glasses", "goggles": "glasses", "spectacles": "glasses",
        "macbook": "laptop", "pc": "laptop", "notebook": "laptop",
        "scooty": "bike", "scooter": "bike", "motorcycle": "bike"
    }
    
    words = text.split()
    # Replace words with their common synonym
    fixed_words = [synonyms.get(w, w) for w in words]
    return " ".join(fixed_words)

# --- 2. AUTO-DESCRIPTION ---
def generate_ai_description(name, loc, time, type):
    action = "lost" if type == "LOST" else "found"
    time_str = f" around {time}" if time else ""
    return f"Urgent: I {action} a {name} at {loc}{time_str}. Please contact me."

# --- 3. SENSITIVITY MASKING (THIS WAS MISSING!) ---
def mask_sensitive_data(text, sensitivity):
    if sensitivity == "High":
        return "🔒 [Hidden Content] - Contact Owner to view."
    return text

# --- 4. IMAGE HASHING ---
def get_image_hash(uploaded_file):
    if uploaded_file is None: return None
    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        # 8x8 average hash is good for finding identical/near-identical images
        return str(imagehash.average_hash(img))
    except: return None

# --- 5. SENSITIVITY ANALYSIS ---
def analyze_sensitivity(desc):
    keywords = ["aadhaar", "passport", "pan card", "credit card", "debit card", "password", "pin"]
    return "High" if any(k in desc.lower() for k in keywords) else "Normal"

# ==========================================
# 🧠 THE SMART MATCHING ENGINE
# ==========================================
def check_matches(target_name, target_loc, target_desc, target_img_hash, target_type, all_items_df):
    matches = []
    if all_items_df.empty: return matches

    # 1. Search Opposite Type (Lost <-> Found)
    search_type = "LOST" if target_type == "FOUND" else "FOUND"
    candidates = all_items_df[all_items_df['report_type'] == search_type]

    # 2. Normalize My Input
    my_name_clean = normalize_text(target_name) 
    my_desc_clean = normalize_text(target_desc)
    
    # Parse my location (City is crucial)
    try:
        my_city = target_loc.split(',')[-2].strip().lower() # Assuming "Area, City, State"
    except:
        my_city = ""

    for index, row in candidates.iterrows():
        score = 0
        
        # --- A. SMART LOCATION FILTER ---
        # Instead of exact match, check if City exists in the string
        db_loc = row['location'].lower()
        if my_city and my_city not in db_loc:
            continue # Skip if cities are completely different

        # --- B. SMART TEXT MATCHING ---
        db_name_clean = normalize_text(row['item_name'])
        db_desc_clean = normalize_text(row['description'])

        # Logic: "token_set_ratio" handles "Black Wallet" vs "Dark Black Wallet"
        name_score = fuzz.token_set_ratio(my_name_clean, db_name_clean)
        
        # Cross Check: Compare Name vs Description
        cross_score = fuzz.token_set_ratio(my_name_clean, db_desc_clean)
        
        # Take the higher of the two text scores
        text_score = max(name_score, cross_score)
        
        score += (text_score * 0.7) # Text is 70% of the weight

        # --- C. IMAGE MATCHING ---
        img_score = 0
        if target_img_hash and row['image_hash']:
            try:
                h1 = imagehash.hex_to_hash(target_img_hash)
                h2 = imagehash.hex_to_hash(row['image_hash'])
                # Difference of 0-5 bits is a very strong match
                if (h1 - h2) <= 5: img_score = 100
                elif (h1 - h2) <= 10: img_score = 80
                elif (h1 - h2) <= 15: img_score = 50
            except: pass
        
        # If Image matches, it boosts the score significantly
        if img_score > 0:
            score = (text_score * 0.4) + (img_score * 0.6)

        # --- FINAL THRESHOLD ---
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
