import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# ⚠️ UPDATE THIS WITH YOUR APP PASSWORD
# ==========================================
SENDER_EMAIL = "chatradi.surya@gmail.com"
SENDER_PASSWORD = "vkhl nnzd uhcx bpft"  # <--- YOUR 16-DIGIT APP PASSWORD
APP_LINK = "https://lost-and-found-avdmhmp5rkarxa9qy8ucm2.streamlit.app/"
# ==========================================

def send_email_core(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

def send_match_notification(user_email, match_id, item_name, match_score, contact_info):
    """
    Sends the High Match Notification WITH Contact Details immediately.
    """
    link = f"{APP_LINK}?match_id={match_id}"
    
    subject = f"🔥 {match_score}% Match Found for '{item_name}'"
    body = f"""
    Hello!
    
    We found a post that matches your item "{item_name}" with {match_score}% confidence.
    
    --------------------------------------------------
    📞 CONTACT DETAILS:
    {contact_info}
    --------------------------------------------------
    
    Please contact them immediately to verify the item.
    
    If this is the correct item, please CLICK THE LINK BELOW to confirm it and reward the finder!
    
    👉 CLICK TO CLOSE & REWARD:
    {link}
    
    - Lost & Found Team
    """
    send_email_core(user_email, subject, body)
