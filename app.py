import streamlit as st
import pandas as pd
import database as db
import ai_utils as ai
import email_utils as notify
import locations as loc_data
import time
from datetime import datetime

st.set_page_config(page_title="Lost and Found", layout="centered")

# Hide Sidebar Nav
st.markdown("""<style>[data-testid="stSidebarNav"] { display: none !important; }</style>""", unsafe_allow_html=True)

# --- INIT ---
if "db_initialized" not in st.session_state:
    db.init_db()
    st.session_state.db_initialized = True
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "home"

# --- DEEP LINK CHECK ---
if "match_id" in st.query_params:
    st.session_state.page = "verify_match"
    st.session_state.deep_link_id = st.query_params["match_id"]

def logout():
    st.session_state.logged_in = False
    st.session_state.page = "home"
    st.rerun()

def format_date(ts):
    try: return datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y")
    except: return str(ts)

# ==========================================
# LOGIN
# ==========================================
if not st.session_state.logged_in:
    st.title("🔒 Lost & Found Login")
    st.page_link("pages/Admin.py", label="Go to Admin Portal", icon="🔐")
    st.divider()
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                user_data = db.verify_user(email, password)
                if user_data:
                    st.session_state.logged_in = True
                    st.session_state.username = user_data[0]
                    st.session_state.coins = user_data[1]
                    st.session_state.user_email_login = email
                    st.rerun()
                else: st.error("Invalid credentials")
    with tab2:
        with st.form("signup_form"):
            email = st.text_input("Email")
            name = st.text_input("Name")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Sign Up"):
                if db.add_user(email, name, pwd) == "SUCCESS": st.success("Created! Login.")
                else: st.error("User exists.")
    st.stop()

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    current_coins = db.get_user_coins(st.session_state.user_email_login)
    st.write(f"👤 **{st.session_state.username}**")
    st.metric(label="🪙 Coins", value=current_coins)
    st.divider()
    if st.button("🏠 Home"): st.session_state.page="home"; st.rerun()
    if st.button("📜 History"): st.session_state.page="history"; st.rerun()
    st.divider()
    if st.button("🚪 Logout"): logout()

# ==========================================
# DEEP LINK VERIFY
# ==========================================
if st.session_state.page == "verify_match":
    st.title("🔍 Verify Match")
    match_id = st.session_state.deep_link_id
    conn = db.init_db_connection()
    try:
        item_df = pd.read_sql(f"SELECT * FROM items WHERE id = {match_id}", conn)
        conn.close()
        if not item_df.empty:
            row = item_df.iloc[0]
            with st.container(border=True):
                st.markdown(f"### Is this your item: {row['item_name']}?")
                st.write(f"📍 {row['location']}")
                st.write(f"📝 {row['description']}")
                st.divider()
                c1, c2 = st.columns(2)
                if c1.button("✅ Yes, This is it!", type="primary"):
                    notify.send_contact_share_email(st.session_state.user_email_login, row['item_name'], row['contact_info'])
                    st.balloons()
                    st.success("Contact details sent to your email!")
                    time.sleep(3); st.session_state.page="home"; st.rerun()
                if c2.button("❌ No"):
                    st.session_state.page="home"; st.rerun()
        else: st.error("Item not found.")
    except: st.error("Error loading item.")

# ==========================================
# HOME
# ==========================================
elif st.session_state.page == "home":
    st.title("🎓 Lost & Found Feed")
    c1, c2 = st.columns(2)
    if c1.button("📢 Report LOST", use_container_width=True): 
        st.session_state.type = "LOST"; st.session_state.page = "form"; st.rerun()
    if c2.button("🔍 Report FOUND", use_container_width=True): 
        st.session_state.type = "FOUND"; st.session_state.page = "form"; st.rerun()
    
    st.divider()
    query = st.text_input("🔎 Search Items")
    df = db.get_all_active_items()
    if not df.empty:
        if query: df = df[df["item_name"].str.lower().str.contains(query.lower())]
        for _, row in df.iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['item_name']}**")
                st.caption(f"📍 {row['location']} | {format_date(row['timestamp'])}")
                if row["report_type"]=="LOST": st.error("LOST")
                else: st.success("FOUND")
    else: st.info("No active reports.")

# ==========================================
# HISTORY
# ==========================================
elif st.session_state.page == "history":
    st.title("📜 My Activity")
    df = db.get_user_history(st.session_state.user_email_login)
    if not df.empty: st.dataframe(df[["item_name", "location", "status"]])
    else: st.info("No history yet.")

# ==========================================
# FORM (THE MAIN LOGIC)
# ==========================================
elif st.session_state.page == "form":
    r_type = st.session_state.type
    st.title(f"Report {r_type} Item")
    if st.button("← Back"): st.session_state.page="home"; st.rerun()

    c1, c2 = st.columns(2)
    with c1: 
        name = st.text_input("Item Name (e.g., Black Wallet)")
        # Location
        states = list(loc_data.INDIA_LOCATIONS.keys())
        state = st.selectbox("State", states)
        cities = list(loc_data.INDIA_LOCATIONS[state].keys())
        city = st.selectbox("City", cities)
        area = st.selectbox("Area", loc_data.INDIA_LOCATIONS[state][city])
        final_area = st.text_input("Specific Area") if area == "Other" else area
        loc_string = f"{final_area}, {city}, {state}"

    with c2: 
        email = st.text_input("Email", value=st.session_state.user_email_login, disabled=True)
        phone = st.text_input("Phone Number")
    
    time_val = st.text_input("Approx Time")
    
    if st.button("✨ Auto-Generate Description"):
        st.session_state.gen_desc = ai.generate_ai_description(name, loc_string, time_val, r_type)
        st.rerun()
    
    desc_val = st.session_state.get("gen_desc", "")
    desc = st.text_area("Description", value=desc_val)
    img = st.file_uploader("Image", ["jpg","png"])
    
    # --- SUBMIT BUTTON ---
    if st.button(f"🚀 Submit {r_type} Report", type="primary"):
        if not (name and phone): st.error("Fill Name and Phone"); st.stop()
        
        # 1. Save Data
        img_bytes = img.getvalue() if img else None
        img_hash = ai.get_image_hash(img)
        contact = f"{phone} ({email})"
        db.add_item(r_type, name, loc_string, desc, "Normal", contact, email, img_bytes, img_hash)
        st.toast("✅ Saved!")

        # 2. MATCHING LOGIC (The Fix)
        st.divider()
        st.subheader("🔎 Checking for Matches...")
        
        all_items = db.get_all_active_items()
        
        # This function handles the "Black Wallet" vs "Dark Black Wallet" matching
        matches = ai.check_matches(name, loc_string, desc, img_hash, r_type, all_items)
        
        if matches:
            top_match = matches[0]
            
            # NOTIFICATION (Threshold > 80% to be safe)
            if top_match['score'] > 80:
                st.success(f"🔥 High Match ({top_match['score']}%) Found! Sending verification email...")
                notify.send_verification_link(email, top_match['id'], name, top_match['score'])
                notify.send_verification_link(top_match['email'], top_match['id'], name, top_match['score'])
            
            # DISPLAY MATCHES
            for match in matches:
                with st.container(border=True):
                    c_a, c_b = st.columns([4, 1])
                    with c_a:
                        st.write(f"**{match['item_name']}**")
                        st.write(f"📍 {match['location']}")
                        st.write(f"📝 {match['description']}")
                    with c_b:
                        score = match['score']
                        color = "green" if score > 80 else "orange"
                        st.markdown(f"<h2 style='color:{color}'>{score}%</h2>", unsafe_allow_html=True)
        else:
            # NO MATCH FOUND MESSAGE
            st.info(f"No similar '{'FOUND' if r_type=='LOST' else 'LOST'}' items found yet.")
            st.warning("We saved your report. We will email you immediately if someone reports a matching item later.")
            
            # Back Button
            time.sleep(4)
            st.session_state.page = "home"
            st.rerun()
