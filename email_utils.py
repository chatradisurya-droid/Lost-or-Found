import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================================
# ⚠️ CRITICAL SETUP: YOU MUST CHANGE THESE
# ==========================================================
SENDER_EMAIL = "chatradi.surya@gmail.com"
# DO NOT USE YOUR NORMAL GMAIL PASSWORD. 
# GO TO: Google Account > Security > 2-Step Verification > App Passwords
SENDER_PASSWORD = "PUT_YOUR_16_DIGIT_APP_PASSWORD_HERE" 
APP_LINK = "https://lost-and-found-avdmhmp5rkarxa9qy8ucm2.streamlit.app/"

def send_email_core(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to Gmail (Use port 465 for SSL)
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        # THIS WILL PRINT THE ERROR IN YOUR LOGS SO YOU KNOW WHAT IS WRONG
        print(f"❌ FAILED TO SEND EMAIL: {e}")
        return False

def trigger_match_emails(current_user_email, matched_user_email, item_name, match_score, current_contact, matched_contact):
    """
    Sends emails to BOTH parties sharing each other's contact info.
    """
    
    # ---------------------------------------------------------
    # EMAIL 1: To YOU (The person who just submitted the post)
    # ---------------------------------------------------------
    subject_1 = f"✅ Match Found: Similar Post Detected ({match_score}%)"
    body_1 = f"""
    Hello!
    
    You just posted about "{item_name}". 
    We checked our history and found a matching post!
    
    --------------------------------------------------
    THEIR CONTACT INFO:
    {matched_contact}
    --------------------------------------------------
    
    👉 Click here to verify in the app:
    {APP_LINK}
    
    Please contact them to exchange the item.
    - Lost & Found Team
    """
    send_email_core(current_user_email, subject_1, body_1)

    # ---------------------------------------------------------
    # EMAIL 2: To THEM (The person who posted EARLIER)
    # ---------------------------------------------------------
    subject_2 = f"🔔 Good News! A Match was found for your '{item_name}'"
    body_2 = f"""
    Hello!
    
    Someone just submitted a new report that matches your older post for "{item_name}".
    
    --------------------------------------------------
    THEIR CONTACT INFO:
    {current_contact}
    --------------------------------------------------
    
    👉 Click here to verify in the app:
    {APP_LINK}
    
    Please contact them to exchange the item.
    - Lost & Found Team
    """
    send_email_core(matched_user_email, subject_2, body_2)
