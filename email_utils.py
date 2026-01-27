import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION ---
SENDER_EMAIL = "chatradi.surya@gmail.com"
SENDER_PASSWORD = "vkhl nnzd uhcx bpft" # <--- UPDATE THIS
APP_LINK = "https://lost-and-found-avdmhmp5rkarxa9qy8ucm2.streamlit.app/"

def send_email_core(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Standard Gmail SSL Port 465
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ EMAIL ERROR: {e}")
        return False

def trigger_match_emails(current_user_email, matched_user_email, item_name, match_score, current_contact, matched_contact):
    # Email to ME (New Poster)
    subj_1 = f"🔥 {match_score}% Match Found for '{item_name}'"
    body_1 = f"We found a match!\n\nTHEIR CONTACT: {matched_contact}\n\nCheck App: {APP_LINK}"
    send_email_core(current_user_email, subj_1, body_1)

    # Email to THEM (Old Poster)
    subj_2 = f"🔔 New Match for your old '{item_name}' post"
    body_2 = f"A new item matches your old post!\n\nTHEIR CONTACT: {current_contact}\n\nCheck App: {APP_LINK}"
    send_email_core(matched_user_email, subj_2, body_2)
