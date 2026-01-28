import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# ⚠️ UPDATE THIS SECTION
# ==========================================
SENDER_EMAIL = "chatradi.surya@gmail.com"
SENDER_PASSWORD = "vkhl nnzd uhcx bpft"  # <--- YOUR 16-DIGIT APP PASSWORD
APP_LINK = "https://lost-or-found-5vwxappathabkemvybggva.streamlit.app/"
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
        # This will show the error ON THE SCREEN so you know why it failed
        st.error(f"❌ Email Failed: {e}")
        return False

def send_verification_link(user_email, match_id, item_name, match_score):
    link = f"{APP_LINK}?match_id={match_id}"
    subject = f"🔥 {match_score}% Match Found for '{item_name}'"
    body = f"""
    Hello!
    
    We found a post that matches your "{item_name}" with {match_score}% confidence.
    
    👉 CLICK TO VERIFY:
    {link}
    
    - Lost & Found Team
    """
    send_email_core(user_email, subject, body)

def send_contact_share_email(recipient_email, matched_item_name, contact_info):
    subject = f"📞 Contact Details for '{matched_item_name}'"
    body = f"""
    Hello!
    
    You confirmed the match for "{matched_item_name}". Here are the details:
    
    📞 CONTACT: {contact_info}
    
    Please contact them to verify ownership.
    - Lost & Found Team
    """
    send_email_core(recipient_email, subject, body)
