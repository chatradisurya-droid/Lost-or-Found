from rapidfuzz import fuzz
from deep_translator import GoogleTranslator
import imagehash
from PIL import Image
import io

translator = GoogleTranslator(source='auto', target='en')

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    synonyms = {
        "mobile": "phone", "cellphone": "phone", "iphone": "phone",
        "pc": "laptop", "macbook": "laptop",
        "specs": "glasses", "spectacles": "glasses",
        "purse": "wallet", "pouch": "wallet",
        "license": "id", "passport": "id"
    }
    words = text.split()
    return " ".join([synonyms.get(w, w) for w in words])

def generate_ai_description(item_name, location, time_val, r_type):
    try:
        item = translator.translate(item_name)
        loc = translator.translate(location)
    except:
        item, loc = item_name, location
    action = "lost" if r_type == "LOST" else "found"
    time_str = f" around {time_val}" if time_val else ""
    return f"Urgent: I {action} a {item} near {loc}{time_str}."

def verify_image_integrity(uploaded_file):
    if uploaded_file is None: return True
    try:
        img = Image.open(uploaded_file)
        img.verify()
        return True
    except: return False

def get_image_hash(uploaded_file):
    if uploaded_file is None: return None
    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        return str(imagehash.dhash(img))
    except: return None

def check_matches(name, loc, desc, img_hash, r_type, db_df):
    if db_df.empty: return []

    q_name = normalize_text(name)
    q_loc = normalize_text(loc)
    target_type = "FOUND" if r_type == "LOST" else "LOST"
    target_df = db_df[db_df['report_type'] == target_type]
    
    matches = []
    
    for idx, row in target_df.iterrows():
        db_name = normalize_text(str(row['item_name']))
        db_loc = normalize_text(str(row['location']))
        
        name_score = fuzz.token_set_ratio(q_name, db_name)
        loc_score = fuzz.token_set_ratio(q_loc, db_loc)
        
        img_score = 0
        if img_hash and row['image_hash']:
            try:
                h1 = imagehash.hex_to_hash(img_hash)
                h2 = imagehash.hex_to_hash(row['image_hash'])
                if (h1 - h2) <= 15: img_score = 100
            except: pass

        final_score = (name_score * 0.5) + (loc_score * 0.2) + (img_score * 0.3)
        
        if final_score > 60:
            matches.append({
                "id": row['id'],
                "item_name": row['item_name'],
                "location": row['location'],
                "contact_info": row['contact_info'],
                "email": row['email'], # Get the hidden email for notifications
                "image_blob": row['image_blob'],
                "score": int(final_score),
                "reasons": f"Name: {name_score}%, Loc: {loc_score}%, Img: {img_score}%"
            })
            
    return sorted(matches, key=lambda x: x['score'], reverse=True)

def analyze_sensitivity(text):
    text = normalize_text(text)
    if any(x in text for x in ['id', 'credit', 'passport']): return "HIGH"
    if any(x in text for x in ['phone', 'laptop']): return "MEDIUM"
    return "LOW"

def mask_sensitive_data(text, sensitivity):
    if sensitivity == "HIGH": return "🔒 [HIDDEN] Sensitive Doc"
    return text