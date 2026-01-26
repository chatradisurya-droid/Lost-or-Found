import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 🔧 ADMIN SETUP
# ==========================================
SENDER_EMAIL = "chatradi.surya@gmail.com"  
SENDER_PASSWORD = "vkhl nnzd uhcx bpft" 
# ==========================================

def send_email_core(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

def send_match_alert(current_user_email, matched_user_email, item_name):
    """
    Sends notifications to BOTH parties.
    1. To the person who just posted (Current User)
    2. To the person who posted previously (Matched User)
    """
    
    # 1. Email to ME (The one who just clicked submit)
    subj_me = f"✅ Match Found: {item_name}"
    body_me = f"Good news! The item you just reported ('{item_name}') matches an existing post in our database.\n\nPlease check the 'Matches' page in the app to verify."
    send_email_core(current_user_email, subj_me, body_me)

    # 2. Email to THEM (The one who posted earlier)
    subj_them = f"🔔 New Match Alert: {item_name}"
    body_them = f"Update: Someone just reported an item that matches your post for '{item_name}'.\n\nPlease log in to SmartCampus to check the details."
    send_email_core(matched_user_email, subj_them, body_them)

def send_contact_details(recipient_email, contact_info, item_name):
    subj = f"📞 Contact Details: {item_name}"
    body = f"You confirmed the match for '{item_name}'.\n\nHere is the owner's contact info:\n{contact_info}\n\nPlease reach out to arrange the return."
    send_email_core(recipient_email, subj, body)