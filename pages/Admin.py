import streamlit as st
import pandas as pd
import sys
import os
import time

# --- 1. IMPORT FIX ---
# This allows the Admin page to "see" the database file in the main folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Admin Panel", layout="wide", page_icon="🔐")

# --- CSS TO HIDE SIDEBAR (Keep it clean) ---
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
# ⚠️ REPLACE THIS WITH YOUR EXACT EMAIL USED IN THE APP
ADMIN_EMAIL = "chatradi.surya@gmail.com"

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# ==================================================
# LOGIN SCREEN
# ==================================================
if not st.session_state.admin_logged_in:
    st.title("🔐 Administrator Access")
    st.markdown("Restricted access for System Administrators only.")
    
    # Return to App Button
    st.page_link("app.py", label="← Back to Main App", icon="🏠")
    
    with st.form("admin_login_form"):
        email = st.text_input("Admin Email")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Access Dashboard"):
            # Verify user exists in DB and matches the hardcoded Admin Email
            user = db.verify_user(email, password)
            if user and email == ADMIN_EMAIL:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Access Denied. You are not an authorized administrator.")
    st.stop()

# ==================================================
# DASHBOARD
# ==================================================
st.title("🖥️ Admin Control Center")

col_head1, col_head2 = st.columns([6, 1])
with col_head1:
    st.caption(f"Logged in as: {ADMIN_EMAIL}")
with col_head2:
    if st.button("🚪 Log Out"):
        st.session_state.admin_logged_in = False
        st.switch_page("app.py")

# --- LIVE METRICS ---
all_users = db.get_all_users()
all_items = db.get_admin_all_items() # You need to ensure this function exists in database.py

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Users", len(all_users) if not all_users.empty else 0)
with c2:
    st.metric("Total Reports", len(all_items) if not all_items.empty else 0)
with c3:
    if not all_items.empty:
        active_count = len(all_items[all_items['status'] == 'OPEN'])
        st.metric("Active Cases", active_count)
    else:
        st.metric("Active Cases", 0)
with c4:
    if not all_items.empty:
        solved_count = len(all_items[all_items['status'] == 'CLAIMED'])
        st.metric("Solved Cases", solved_count)
    else:
        st.metric("Solved Cases", 0)

st.divider()

# ==================================================
# MANAGEMENT TABS
# ==================================================
tab1, tab2 = st.tabs(["👥 User Management", "📝 Post Management"])

# --- TAB 1: USERS ---
with tab1:
    st.subheader("Registered Users Directory")
    if not all_users.empty:
        st.dataframe(all_users, use_container_width=True)
        
        with st.expander("❌ Delete a User (Danger Zone)"):
            st.warning("Deleting a user will remove all their posts forever.")
            user_to_del = st.selectbox("Select User Email", all_users['email'].unique())
            if st.button("Permanently Delete User"):
                db.delete_user(user_to_del)
                st.success(f"User {user_to_del} deleted.")
                time.sleep(1)
                st.rerun()
    else:
        st.info("No users found in the database.")

# --- TAB 2: POSTS ---
with tab2:
    st.subheader("All System Reports (Active & Deleted)")
    if not all_items.empty:
        # Filter by Status
        status_filter = st.multiselect(
            "Filter Status", 
            all_items['status'].unique(), 
            default=all_items['status'].unique()
        )
        
        view_df = all_items[all_items['status'].isin(status_filter)]
        st.dataframe(view_df, use_container_width=True)
        
        st.divider()
        st.write("🔧 **Force Delete Post**")
        col_input, col_btn = st.columns([3, 1])
        with col_input:
            del_id = st.number_input("Enter Post ID to Delete", min_value=0, step=1)
        with col_btn:
            if st.button("🗑️ Delete Post", type="primary"):
                db.soft_delete_item(del_id)
                st.success(f"Post {del_id} marked as deleted.")
                time.sleep(1)
                st.rerun()
    else:
        st.info("No items have been reported yet.")
