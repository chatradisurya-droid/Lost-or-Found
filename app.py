import streamlit as st
import pandas as pd
import database as db
import ai_utils as ai
import email_utils as notify
import locations as loc_data
import time
from datetime import datetime

# 1. SETUP PAGE CONFIG
st.set_page_config(page_title="Lost and Found", layout="centered")

# 2. HIDE SIDEBAR NAVIGATION (Keep custom buttons visible)
st.markdown("""
<style>
    [data-testid="stSidebarNav"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# --- INIT SESSION STATE ---
if "db_initialized" not in st.session_state:
    db.init_db()
    st.session_state.db_initialized = True
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "home"

# --- DEEP LINK CHECKER ---
# This detects if the user opened the app via an Email Link
# Example link: app_url/?match_id=5
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

# ==========================================
# 1. LOGIN SCREEN
# ==========================================
if not st.session_state.logged_in:
    st.title("🔒 Lost & Found Login")
    
    # Link to Admin Panel
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
# 2. SIDEBAR (User Profile & Coins)
# ==========================================
with st.sidebar:
    # Refresh coins from DB to show accurate balance
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
# 3. VERIFICATION PAGE (From Email Link)
# ==========================================
if st.session_state.page == "verify_match":
    st.title("🔍 Match Verification")
    st.info("You clicked a link from your email. Is this the item?")
    
    # Fetch the item details using the ID from the link
    match_id = st.session_state.deep_link_id
    conn = db.init_db_connection()
    try:
        item_df = pd.read_sql(f"SELECT * FROM items WHERE id = {match_id}", conn)
        conn.close()
        
        if not item_df.empty:
            row = item_df.iloc[0]
            with st.container(border=True):
                if row['image_blob']:
                    st.image(row['image_blob'], width=250)
                st.markdown(f"### {row['item_name']}")
                st.write(f"**Description:** {row['description']}")
                st.write(f"**Location:** {row['location']}")
                
                st.divider()
                st.write("Does this look like the item you are looking for?")
                
                c1, c2 = st.columns(2)
                # BUTTON: YES (Trigger Contact Share)
                if c1.button("✅ Yes, This is it!", type="primary", use_container_width=True):
                    with st.spinner("Sharing contact details..."):
                        notify.send_contact_share_email(
                            recipient_email=st.session_state.user_email_login,
                            matched_item_name=row['item_name'],
                            contact_info=row['contact_info']
                        )
                    st.balloons()
                    st.success("🎉 Contact Details have been sent to your Email!")
                    time.sleep(3)
                    st.session_state.page = "home"
                    st.rerun()
                
                # BUTTON: NO
                if c2.button("❌ No, incorrect", use_container_width=True):
                    st.warning("Okay, we will keep looking.")
                    time.sleep(2)
                    st.session_state.page = "home"
                    st.rerun()
        else:
            st.error("This item may have been deleted or resolved.")
            if st.button("Go Home"): st.session_state.page="home"; st.rerun()
    except Exception as e:
        st.error(f"Error loading verification: {e}")
        if st.button("Go Home"): st.session_state.page="home"; st.rerun()

# ==========================================
# 4. HOME PAGE (Feed)
# ==========================================
elif st.session_state.page == "home":
    st.title("🎓 Lost & Found Feed")
    
    c1, c2 = st.columns(2)
    if c1.button("📢 Report LOST", key="home_lost", use_container_width=True): 
        st.session_state.type = "LOST"; st.session_state.page = "form"; st.rerun()
    if c2.button("🔍 Report FOUND", key="home_found", use_container_width=True): 
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
    else: st.info("No active reports.")

# ==========================================
# 5. MY HISTORY PAGE
# ==========================================
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

# ==========================================
# 6. REPORT FORM (With Logic)
# ==========================================
elif st.session_state.page == "form":
    r_type = st.session_state.type
    st.title(f"Report {r_type} Item")
    if st.button("← Back to Feed"): st.session_state.page="home"; st.rerun()

    c1, c2 = st.columns(2)
    with c1: 
        name = st.text_input("Item Name (e.g., Blue Wallet)")
        # Location Dropdowns
        states_list = list(loc_data.INDIA_LOCATIONS.keys())
        state = st.selectbox("State", states_list)
        cities_list = list(loc_data.INDIA_LOCATIONS[state].keys())
        city = st.selectbox("City", cities_list)
        areas_list = loc_data.INDIA_LOCATIONS[state][city]
        area_select = st.selectbox("Area/Place", areas_list)
        
        final_area = area_select
        if area_select == "Other":
            final_area = st.text_input("Enter Specific Area Name")
        landmark = st.text_input("Specific Landmark (Optional)")
        
        loc_string = f"{landmark}, {final_area}, {city}, {state}" if landmark else f"{final_area}, {city}, {state}"

    with c2: 
        email = st.text_input("Email", value=st.session_state.user_email_login, disabled=True)
        phone = st.text_input("Phone Number")
    
    time_val = st.text_input("Approx Time (e.g. 2 PM)")
    
    # Auto-Description
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
        if not (name and loc_string and phone):
            st.error("Please fill Name, Location, and Phone.")
            st.stop()
            
        if db.check_duplicate_post(email, r_type, name):
            st.error("Duplicate post."); st.stop()
        
        img_bytes = img.getvalue() if img else None
        img_hash = ai.get_image_hash(img)
        
        contact = f"{phone} ({email})"
        
        # 1. SAVE POST & ADD COINS
        new_id = db.add_item(r_type, name, loc_string, desc, "Normal", contact, email, img_bytes, img_hash)
        st.toast("✅ Report Saved! +10 Coins added!")
        
        # 2. CHECK MATCHES (Past & Present)
        with st.spinner("🤖 AI is analyzing all past posts..."):
            all_items = db.get_all_active_items()
            matches = ai.check_matches(name, loc_string, desc, img_hash, r_type, all_items)
            
            if matches:
                st.session_state.matches = matches
                top_match = matches[0]
                
                # 3. NOTIFICATION LOGIC (90% Rule)
                if top_match['score'] > 90:
                    st.info(f"🔥 High Match ({top_match['score']}%) Found! Sending verification link...")
                    notify.send_verification_link(
                        user_email=email,
                        match_id=top_match['id'],
                        item_name=name,
                        match_score=top_match['score']
                    )
                    st.success("✅ Link Sent! Check your email to confirm.")
                
                st.session_state.page = "matches"
                st.rerun()
            else:
                st.success("Report Saved! We will notify you if a match appears later.")
                time.sleep(2); st.session_state.page="home"; st.rerun()

# ==========================================
# 7. MATCHES DISPLAY PAGE
# ==========================================
elif st.session_state.page == "matches":
    st.title("🤝 Similar Posts Found")
    st.write("We found these past posts that match your description:")
    
    if "matches" in st.session_state and st.session_state.matches:
        for match in st.session_state.matches:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{match['item_name']}**")
                    st.write(match['description'])
                    st.caption(f"📍 {match['location']}")
                with c2:
                    score = match['score']
                    # Visual Indicator for High Match
                    color = "green" if score > 90 else "orange"
                    st.markdown(f"<h1 style='color:{color}; text-align: center;'>{score}%</h1>", unsafe_allow_html=True)
                    st.caption("Confidence")
    
    st.divider()
    if st.button("Done"):
        st.session_state.page = "home"
        st.rerun()
