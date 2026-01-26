import streamlit as st
import pandas as pd
import database as db
import ai_utils as ai
import email_utils as notify
import locations as loc_data
import time
from datetime import datetime

# 1. PAGE CONFIG
st.set_page_config(page_title="Lost and Found", layout="centered")

# 2. HIDE SIDEBAR NAV (Keep custom buttons)
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
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
        st.session_state.page="home"
        st.rerun()
    if st.button("📜 My History", use_container_width=True): 
        st.session_state.page="history"
        st.rerun()
    st.divider()
    if st.button("🚪 Logout", use_container_width=True): 
        logout()

# ==================================================
# PAGE: HOME
# ==================================================
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
        if query:
            df = df[df["item_name"].str.lower().str.contains(query.lower())]
        for _, row in df.iterrows():
            with st.container(border=True):
                c_img, c_txt, c_act = st.columns([1, 4, 1.5])
                with c_img:
                    if row["image_blob"]: st.image(row["image_blob"], width=80)
                with c_txt:
                    st.markdown(f"**{row['item_name']}**")
                    st.caption(f"📍 {row['location']} | {format_date(row['timestamp'])}")
                    st.text(ai.mask_sensitive_data(str(row["description"]), str(row["sensitivity"])))
                with c_act:
                    if row["report_type"]=="LOST": st.error("LOST")
                    else: st.success("FOUND")
                    if st.session_state.user_email_login == row['email']:
                        if st.button("🗑️ Delete", key=f"d_{row['id']}"):
                            db.soft_delete_item(row["id"])
                            st.rerun()
    else: st.info("No active reports.")

# ==================================================
# PAGE: HISTORY
# ==================================================
elif st.session_state.page == "history":
    st.title("📜 My Activity")
    df_hist = db.get_user_history(st.session_state.user_email_login)
    if not df_hist.empty:
        for _, row in df_hist.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.write(f"**{row['item_name']}** ({row['report_type']})")
                    st.caption(format_date(row['timestamp']))
                with c2:
                    st.info(row['status'])
    else: st.info("No history yet.")

# ==================================================
# PAGE: FORM (LOGIC UPGRADE HERE)
# ==================================================
elif st.session_state.page == "form":
    r_type = st.session_state.type
    st.title(f"Report {r_type} Item")
    if st.button("← Back to Feed"): st.session_state.page="home"; st.rerun()

    c1, c2 = st.columns(2)
    with c1: 
        name = st.text_input("Item Name (e.g., Blue Wallet)")
        st.write("📍 **Select Location**")
        states_list = list(loc_data.INDIA_LOCATIONS.keys())
        state = st.selectbox("State", states_list, key="sb_state")
        cities_list = list(loc_data.INDIA_LOCATIONS[state].keys())
        city = st.selectbox("City", cities_list, key="sb_city")
        areas_list = loc_data.INDIA_LOCATIONS[state][city]
        area_select = st.selectbox("Area/Place", areas_list, key="sb_area")
        
        final_area = area_select
        if area_select == "Other":
            final_area = st.text_input("Enter Specific Area Name", placeholder="e.g. Near Library")
        landmark = st.text_input("Specific Landmark (Optional)", placeholder="e.g. Room 304, Bench near park")
        
        if landmark: loc_string = f"{landmark}, {final_area}, {city}, {state}"
        else: loc_string = f"{final_area}, {city}, {state}"

    with c2: 
        default_email = st.session_state.user_email_login
        email = st.text_input("Email", value=default_email, disabled=True)
        phone = st.text_input("Phone Number")
    
    time_val = st.text_input("Approx Time (e.g. 2 PM)")
    
    if "gen_desc" not in st.session_state: st.session_state.gen_desc = ""
    if st.button("✨ Auto-Generate Description"):
        st.session_state.gen_desc = ai.generate_ai_description(name, loc_string, time_val, r_type)
        st.rerun()
        
    desc = st.text_area("Description", value=st.session_state.gen_desc)
    img = st.file_uploader("Image", ["jpg","png"])
    submitted = st.button(f"🚀 Submit {r_type} Report", type="primary")

    if submitted:
        if not (name and loc_string and phone):
            st.error("Please fill Name, Location, and Phone.")
            st.stop()
        if db.check_duplicate_post(email, r_type, name):
            st.error("Duplicate post."); st.stop()
        
        img_bytes = img.getvalue() if img else None
        
        # 1. GENERATE HASH & SAVE POST
        img_hash = ai.get_image_hash(img)
        sens = ai.analyze_sensitivity(desc)
        contact = f"{phone} ({email})"
        
        new_id = db.add_item(r_type, name, loc_string, desc, sens, contact, email, img_bytes, img_hash)
        
        # -----------------------------------------------------------
        # 🔥 CRITICAL STEP: THE "TIME TRAVEL" CHECK
        # -----------------------------------------------------------
        # This function fetches ALL active items from the database.
        # It includes items posted yesterday, last week, or last month.
        all_items = db.get_all_active_items()
        
        # We now check your NEW post against ALL OLD posts.
        matches = ai.check_matches(name, loc_string, desc, img_hash, r_type, all_items)
        
        if matches:
            # --- NOTIFICATION LOGIC ---
            top_match = matches[0]
            
            if top_match['score'] > 80:
                with st.spinner(f"Previous similar post found ({top_match['score']}%)! Connecting you..."):
                    # This sends emails to both YOU (New Post) and THEM (Old Post)
                    notify.trigger_match_emails(
                        current_user_email=email,
                        matched_user_email=top_match['email'],
                        item_name=name,
                        match_score=top_match['score'],
                        current_contact=contact,
                        matched_contact=top_match['contact_info']
                    )
                st.success("✅ We found a past post that matches yours! Check your email.")
            # --------------------------
            
            st.session_state.matches = matches
            st.session_state.match_id = new_id
            st.session_state.page = "matches"
            st.rerun()
        else:
            st.success("Report Saved! We will notify you if a match appears later.")
            time.sleep(2); st.session_state.page="home"; st.rerun()

# ==================================================
# PAGE: MATCHES
# ==================================================
elif st.session_state.page == "matches":
    st.title("🤝 Matches Found from Database")
    st.markdown("Here are the past posts that match your report.")
    
    if "matches" in st.session_state and st.session_state.matches:
        for match in st.session_state.matches:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.subheader(f"{match['item_name']}")
                    st.write(f"📝 {match['description']}")
                    st.caption(f"📍 {match['location']}")
                with c2:
                    score = match['score']
                    color = "green" if score > 80 else "orange"
                    st.markdown(f"<h2 style='color:{color};'>{score}%</h2>", unsafe_allow_html=True)
                    st.caption("Match Score")
    
    st.divider()
    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.rerun()
