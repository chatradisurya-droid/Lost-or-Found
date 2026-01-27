import streamlit as st
import pandas as pd
import database as db
import ai_utils as ai
import email_utils as notify
import locations as loc_data
import time
from datetime import datetime

# 1. SETUP
st.set_page_config(page_title="Lost and Found", layout="centered")

# 2. HIDE SIDEBAR NAV
st.markdown("""
<style>
    [data-testid="stSidebarNav"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# --- INIT ---
if "db_initialized" not in st.session_state:
    db.init_db()
    st.session_state.db_initialized = True
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "home"

# --- DEEP LINK CHECKER (NEW) ---
# This checks if the user clicked an email link (e.g. ?match_id=5)
if "match_id" in st.query_params:
    st.session_state.page = "verify_match"
    st.session_state.deep_link_id = st.query_params["match_id"]

def format_date(ts):
    try: return datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y")
    except: return str(ts)

def logout():
    st.session_state.logged_in = False
    st.session_state.page = "home"
    st.rerun()

# --- LOGIN SCREEN ---
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

# --- SIDEBAR ---
with st.sidebar:
    current_coins = db.get_user_coins(st.session_state.user_email_login)
    st.write(f"👤 **{st.session_state.username}**")
    st.metric(label="🪙 Your Gold Coins", value=current_coins)
    
    st.divider()
    if st.button("🏠 Home Feed", use_container_width=True): 
        st.session_state.page="home"; st.rerun()
    if st.button("📜 My History", use_container_width=True): 
        st.session_state.page="history"; st.rerun()
    st.divider()
    if st.button("🚪 Logout", use_container_width=True): 
        logout()

# ==========================================
# PAGE: DEEP LINK VERIFICATION (NEW)
# ==========================================
if st.session_state.page == "verify_match":
    st.title("🔍 Verify Match")
    
    # Get the item details from the ID in the link
    match_id = st.session_state.deep_link_id
    # We need a function to get one item (I'll add this to database code below)
    conn = db.init_db_connection()
    item = pd.read_sql(f"SELECT * FROM items WHERE id = {match_id}", conn)
    conn.close()
    
    if not item.empty:
        row = item.iloc[0]
        st.info("You clicked a link from your email. Is this the item?")
        
        with st.container(border=True):
            st.image(row['image_blob'], width=200) if row['image_blob'] else None
            st.markdown(f"### {row['item_name']}")
            st.write(f"**Description:** {row['description']}")
            st.write(f"**Location:** {row['location']}")
            
            st.divider()
            
            # CONFIRMATION BUTTONS
            c1, c2 = st.columns(2)
            if c1.button("✅ Yes, This is it!", type="primary"):
                # NOW we share the contact details
                notify.send_contact_share_email(
                    recipient_email=st.session_state.user_email_login, 
                    matched_item_name=row['item_name'], 
                    contact_info=row['contact_info']
                )
                st.balloons()
                st.success("🎉 Contact Details have been sent to your Email!")
                
            if c2.button("❌ No, Not mine"):
                st.warning("Okay, we will keep looking.")
                time.sleep(2)
                st.session_state.page = "home"
                st.rerun()
    else:
        st.error("Item not found or deleted.")
        if st.button("Go Home"): st.session_state.page="home"; st.rerun()

# ==========================================
# PAGE: HOME
# ==========================================
elif st.session_state.page == "home":
    st.title("🎓 Lost & Found Feed")
    c1, c2 = st.columns(2)
    if c1.button("📢 Report LOST", key="h_lost", use_container_width=True): 
        st.session_state.type = "LOST"; st.session_state.page = "form"; st.rerun()
    if c2.button("🔍 Report FOUND", key="h_found", use_container_width=True): 
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
# PAGE: HISTORY
# ==========================================
elif st.session_state.page == "history":
    st.title("📜 My Activity")
    df = db.get_user_history(st.session_state.user_email_login)
    if not df.empty: st.dataframe(df[["item_name", "location", "status"]])
    else: st.info("No history yet.")

# ==========================================
# PAGE: FORM (Reporting & Matching)
# ==========================================
elif st.session_state.page == "form":
    r_type = st.session_state.type
    st.title(f"Report {r_type} Item")
    if st.button("← Back"): st.session_state.page="home"; st.rerun()

    c1, c2 = st.columns(2)
    with c1: 
        name = st.text_input("Item Name (e.g., Blue Wallet)")
        # Location Selection
        states = list(loc_data.INDIA_LOCATIONS.keys())
        state = st.selectbox("State", states)
        cities = list(loc_data.INDIA_LOCATIONS[state].keys())
        city = st.selectbox("City", cities)
        areas = loc_data.INDIA_LOCATIONS[state][city]
        area = st.selectbox("Area", areas)
        final_area = st.text_input("Specific Area") if area == "Other" else area
        loc_string = f"{final_area}, {city}, {state}"

    with c2: 
        email = st.text_input("Email", value=st.session_state.user_email_login, disabled=True)
        phone = st.text_input("Phone Number")
    
    time_val = st.text_input("Approx Time (e.g., 2 PM)")
    
    # Auto-Desc
    if "gen_desc" not in st.session_state: st.session_state.gen_desc = ""
    if st.button("✨ Auto-Generate Description"):
        if name and loc_string:
            st.session_state.gen_desc = ai.generate_ai_description(name, loc_string, time_val, r_type)
            st.rerun()
        else: st.warning("Please fill Name and Location first.")

    desc = st.text_area("Description", value=st.session_state.gen_desc)
    img = st.file_uploader("Image", ["jpg","png"])
    submitted = st.button(f"🚀 Submit {r_type} Report", type="primary")

    if submitted:
        if not (name and phone): st.error("Fill all fields"); st.stop()
        
        img_bytes = img.getvalue() if img else None
        img_hash = ai.get_image_hash(img)
        contact = f"{phone} ({email})"
        
        # 1. SAVE POST
        new_id = db.add_item(r_type, name, loc_string, desc, "Normal", contact, email, img_bytes, img_hash)
        st.toast("✅ Saved! Checking for matches...")
        
        # 2. CHECK MATCHES
        all_items = db.get_all_active_items()
        matches = ai.check_matches(name, loc_string, desc, img_hash, r_type, all_items)
        
        if matches:
            st.session_state.matches = matches
            
            # --- NOTIFICATION LOGIC (90% Threshold) ---
            top_match = matches[0]
            if top_match['score'] > 90:
                with st.spinner("🔥 High match found! Sending verification link..."):
                    # Send Email with LINK ONLY (No contact info yet)
                    notify.send_verification_link(
                        user_email=email,
                        match_id=top_match['id'],
                        item_name=name,
                        match_score=top_match['score']
                    )
                st.success("✅ High Match! We sent a verification link to your email.")
            
            st.session_state.page = "matches"
            st.rerun()
        else:
            st.success("Report Saved! We will notify you if a match appears later.")
            time.sleep(2); st.session_state.page="home"; st.rerun()

# ==========================================
# PAGE: MATCHES DISPLAY
# ==========================================
elif st.session_state.page == "matches":
    st.title("🤝 Matches Found")
    
    if "matches" in st.session_state:
        for match in st.session_state.matches:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.subheader(f"{match['item_name']}")
                    st.write(f"📍 {match['location']}")
                    st.write(f"📝 {match['description']}")
                with c2:
                    score = match['score']
                    color = "green" if score > 90 else "orange"
                    st.markdown(f"<h1 style='color:{color};'>{score}%</h1>", unsafe_allow_html=True)
                    st.caption("Match Score")
                    
    if st.button("Done"): st.session_state.page="home"; st.rerun()
