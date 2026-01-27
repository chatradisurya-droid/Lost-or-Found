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

def format_date(ts):
    try: return datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y")
    except: return str(ts)

def logout():
    st.session_state.logged_in = False
    st.session_state.page = "home"
    st.rerun()

# --- LOGIN ---
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
    st.write(f"👤 **{st.session_state.username}**")
    if st.button("🏠 Home Feed"): st.session_state.page="home"; st.rerun()
    if st.button("📜 My History"): st.session_state.page="history"; st.rerun()
    if st.button("🚪 Logout"): logout()

# --- HOME ---
if st.session_state.page == "home":
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

# --- HISTORY ---
elif st.session_state.page == "history":
    st.title("📜 My Activity")
    df = db.get_user_history(st.session_state.user_email_login)
    if not df.empty: st.dataframe(df[["item_name", "location", "status"]])
    else: st.info("No history yet.")

# --- FORM ---
elif st.session_state.page == "form":
    r_type = st.session_state.type
    st.title(f"Report {r_type} Item")
    if st.button("← Back"): st.session_state.page="home"; st.rerun()

    c1, c2 = st.columns(2)
    with c1: 
        name = st.text_input("Item Name (e.g., Blue Wallet)")
        # Location logic...
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
    
    desc = st.text_area("Description")
    img = st.file_uploader("Image", ["jpg","png"])
    submitted = st.button(f"🚀 Submit {r_type} Report", type="primary")

    if submitted:
        if not (name and phone): st.error("Fill all fields"); st.stop()
        
        img_bytes = img.getvalue() if img else None
        img_hash = ai.get_image_hash(img)
        contact = f"{phone} ({email})"
        
        # 1. SAVE POST
        new_id = db.add_item(r_type, name, loc_string, desc, "Normal", contact, email, img_bytes, img_hash)
        
        # 2. CHECK MATCHES (Past & Present)
        all_items = db.get_all_active_items()
        matches = ai.check_matches(name, loc_string, desc, img_hash, r_type, all_items)
        
        if matches:
            top_match = matches[0]
            if top_match['score'] > 80:
                with st.spinner(f"High Match ({top_match['score']}%) Found! Sending Emails..."):
                    # 3. TRIGGER EMAILS
                    notify.trigger_match_emails(
                        current_user_email=email,
                        matched_user_email=top_match['email'],
                        item_name=name,
                        match_score=top_match['score'],
                        current_contact=contact,
                        matched_contact=top_match['contact_info']
                    )
                st.success("✅ Match Found! Emails sent to both parties.")
            
            st.session_state.matches = matches
            st.session_state.page = "matches"
            st.rerun()
        else:
            st.success("Report Saved! We will check for future matches.")
            time.sleep(2); st.session_state.page="home"; st.rerun()

# --- MATCHES ---
elif st.session_state.page == "matches":
    st.title("🤝 Matches Found")
    if "matches" in st.session_state:
        for match in st.session_state.matches:
            with st.container(border=True):
                st.write(f"**{match['item_name']}**")
                st.write(f"📍 {match['location']}")
                st.write(f"📞 {match['contact_info']}")
                st.metric("Score", f"{match['score']}%")
    if st.button("Done"): st.session_state.page="home"; st.rerun()
