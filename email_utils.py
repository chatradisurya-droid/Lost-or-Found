import smtplib
from email.mime.text import MIMEText
import streamlit as st

# --- CONFIGURATION ---
EMAIL_SENDER = "chatradi.surya@gmail.com" 
EMAIL_PASSWORD = "your-app-password-here"  # ⚠️ Paste your Google App Password
APP_LINK = "https://lost-and-found-avdmhmp5rkarxa9qy8ucm2.streamlit.app/"

def send_notification(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp_server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

def trigger_match_emails(current_user_email, matched_user_email, item_name, match_score, current_contact, matched_contact):
    """
    Sends two different emails depending on who posted when.
    """
    
    # ---------------------------------------------------------
    # EMAIL 1: To YOU (The person who just submitted the post)
    # This handles the "Found First, Lost Late" scenario.
    # ---------------------------------------------------------
    subject_1 = f"✅ Match Found! Similar Post Detected ({match_score}%)"
    body_1 = f"""
    Hello!
    
    You just posted about "{item_name}".
    
    Our AI checked our database and found a previous post that matches your description!
    
    --------------------------------------------------
    THEIR CONTACT INFO:
    {matched_contact}
    --------------------------------------------------
    
    👉 Click here to open the app and verify:
    {APP_LINK}
    
    Please contact them immediately.
    
    - Lost & Found Team
    """
    send_notification(current_user_email, subject_1, body_1)

    # ---------------------------------------------------------
    # EMAIL 2: To THEM (The person who posted earlier)
    # This notifies the old poster that a new match arrived.
    # ---------------------------------------------------------
    subject_2 = f"🔔 Update: Someone just matched your old '{item_name}' post"
    body_2 = f"""
    Hello!
    
    Good news! Someone just submitted a new report that matches your older post for "{item_name}".
    
    --------------------------------------------------
    THEIR CONTACT INFO:
    {current_contact}
    --------------------------------------------------
    
    👉 Click here to open the app and verify:
    {APP_LINK}
    
    - Lost & Found Team
    """
    send_notification(matched_user_email, subject_2, body_2)
