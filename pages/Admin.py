# admin_panel.py
import streamlit as st
import pandas as pd
import database as db
import time

st.set_page_config(page_title="Admin Panel", layout="wide", page_icon="🔐")

# --- ADMIN CONFIG ---
ADMIN_EMAIL = "chatradi.surya@gmail.com" 

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# --- ADMIN LOGIN ---
if not st.session_state.admin_logged_in:
    st.title("🔐 Administrator Access")
    st.markdown("This portal is restricted to system administrators.")
    
    with st.form("admin_login"):
        email = st.text_input("Admin Email")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Access Dashboard"):
            # Check Credentials
            user = db.verify_user(email, password)
            if user and email == ADMIN_EMAIL:
                st.session_state.admin_logged_in = True
                st.success("Access Granted")
                st.rerun()
            else:
                st.error("Access Denied. Invalid Admin Credentials.")
    st.stop()

# --- ADMIN DASHBOARD ---
st.title("🖥️ Admin Control Center")

# Logout Button
if st.button("Log Out"):
    st.session_state.admin_logged_in = False
    st.rerun()

# Fetch All Data
all_users = db.get_all_users()
all_items = db.get_admin_all_items()

# 1. LIVE METRICS
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Users", len(all_users))
c2.metric("Total Reports", len(all_items))
c3.metric("Active Cases", len(all_items[all_items['status'] == 'OPEN']))
c4.metric("Cases Solved", len(all_items[all_items['status'] == 'CLAIMED']))

st.divider()

# 2. TABS FOR MANAGEMENT
tab1, tab2 = st.tabs(["👥 User Management", "📝 Post Management"])

# USER TAB
with tab1:
    st.subheader("All Registered Users")
    if not all_users.empty:
        st.dataframe(all_users, use_container_width=True)
        
        st.error("⚠️ Danger Zone: Delete User")
        user_to_del = st.selectbox("Select User to Remove", all_users['email'].unique())
        
        col_btn, col_warn = st.columns([1, 4])
        with col_btn:
            if st.button("❌ DELETE USER"):
                db.delete_user(user_to_del)
                st.success(f"User {user_to_del} and all their data removed.")
                time.sleep(1); st.rerun()
        with col_warn:
            st.caption("This action cannot be undone. All posts by this user will also be deleted.")
    else:
        st.info("No users found.")

# REPORTS TAB
with tab2:
    st.subheader("All System Reports (Including Hidden/Deleted)")
    if not all_items.empty:
        # Filter Logic
        status_filter = st.multiselect(
            "Filter by Status", 
            all_items['status'].unique(), 
            default=all_items['status'].unique()
        )
        
        view_df = all_items[all_items['status'].isin(status_filter)]
        st.dataframe(view_df, use_container_width=True)
        
        st.divider()
        st.write("🔧 **Admin Actions**")
        item_id = st.number_input("Enter Post ID to Force Delete", min_value=0, step=1)
        
        if st.button("🗑️ Force Delete Post"):
            db.soft_delete_item(item_id)
            st.success(f"Post ID {item_id} has been hidden/deleted.")
            time.sleep(1); st.rerun()
    else:
        st.info("No reports found.")