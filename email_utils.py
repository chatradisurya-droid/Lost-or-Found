import smtplib
from email.mime.text import MIMEText
import streamlit as st

# --- CONFIGURATION ---
EMAIL_SENDER = "chatradi.surya@gmail.com" 
# ⚠️ Make sure this password is correct in your code/secrets
EMAIL_PASSWORD = "your-app-password-here" 
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
    Sends emails to both parties with the Match %, Contact Info, and App Link.
    """
    
    # ---------------------------------------------------------
    # EMAIL 1: To the person who JUST submitted the post (User B)
    # ---------------------------------------------------------
    subject_1 = f"🔥 {match_score}% Match Found for your '{item_name}'!"
    body_1 = f"""
    Hello!
    
    Great news! We found a post that matches your report for "{item_name}" with {match_score}% confidence.
    
    --------------------------------------------------
    THEIR CONTACT INFO:
    {matched_contact}
    --------------------------------------------------
    
    👉 Click here to view the item details in the app:
    {APP_LINK}
    
    Please contact them to verify the item.
    
    - Lost & Found Team
    """
    send_notification(current_user_email, subject_1, body_1)

    # ---------------------------------------------------------
    # EMAIL 2: To the person who posted EARLIER (User A)
    # ---------------------------------------------------------
    subject_2 = f"🔔 New {match_score}% Match for your '{item_name}' post"
    body_2 = f"""
    Hello!
    
    A new report was just submitted that matches your older post for "{item_name}" with {match_score}% confidence.
    
    --------------------------------------------------
    THEIR CONTACT INFO:
    {current_contact}
    --------------------------------------------------
    
    👉 Click here to verify the claim in the app:
    {APP_LINK}
    
    Please contact them to arrange the return.
    
    - Lost & Found Team
    """
    send_notification(matched_user_email, subject_2, body_2)
