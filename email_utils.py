import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION ---
SENDER_EMAIL = "chatradi.surya@gmail.com"
SENDER_PASSWORD = "YOUR_16_DIGIT_APP_PASSWORD_HERE" # <--- UPDATE THIS
APP_BASE_URL = "https://lost-and-found-avdmhmp5rkarxa9qy8ucm2.streamlit.app/"

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

def send_verification_link(user_email, match_id, item_name, match_score):
    """STEP 1: Send the LINK to verify the item (No contact info yet)"""
    
    link = f"{APP_BASE_URL}?match_id={match_id}"
    
    subject = f"🔥 {match_score}% Match Found for '{item_name}'"
    body = f"""
    Hello!
    
    We found a post that matches your item "{item_name}" with {match_score}% confidence.
    
    Please click the link below to VIEW the item and confirm if it is yours.
    
    👉 CLICK TO VERIFY:
    {link}
    
    (If you confirm it is yours, we will share the contact details).
    
    - Lost & Found Team
    """
    send_email_core(user_email, subject, body)

def send_contact_share_email(recipient_email, matched_item_name, contact_info):
    """STEP 2: Send the CONTACT INFO after they clicked 'Yes'"""
    
    subject = f"📞 Contact Details for '{matched_item_name}'"
    body = f"""
    Hello!
    
    Since you confirmed the match for "{matched_item_name}", here are the contact details of the other person:
    
    --------------------------------------------------
    📞 CONTACT INFO:
    {contact_info}
    --------------------------------------------------
    
    Please contact them to arrange the exchange.
    
    - Lost & Found Team
    """
    send_email_core(recipient_email, subject, body)
