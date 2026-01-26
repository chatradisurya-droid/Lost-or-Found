import smtplib
from email.mime.text import MIMEText
import streamlit as st

# SETUP: Get credentials from Streamlit Secrets
# If running locally without secrets, replace these with actual strings temporarily
EMAIL_SENDER = "chatradi.surya@gmail.com" 
EMAIL_PASSWORD = "your-app-password-here" # Google App Password

def send_notification(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email

        # Connect to Gmail Server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp_server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

def trigger_match_emails(current_user_email, matched_user_email, item_name, match_score, current_contact, matched_contact):
    """
    Sends two emails:
    1. To the Current User: "We found a match! Here is their contact."
    2. To the Matched User: "Someone found your item! Here is their contact."
    """
    
    # Email 1: To the Person who just submitted
    subject_1 = f"🎯 Match Found: {item_name} ({match_score}% Confidence)"
    body_1 = f"""
    Hello!
    
    Good news! We found a post that matches your report for "{item_name}".
    
    Match Details:
    --------------------------------
    Confidence: {match_score}%
    Contact the other person: {matched_contact}
    --------------------------------
    
    Please verify carefully before exchanging items.
    
    - Lost & Found Team
    """
    send_notification(current_user_email, subject_1, body_1)

    # Email 2: To the Person from the database (The older post)
    subject_2 = f"🔔 Update on your {item_name} Report"
    body_2 = f"""
    Hello!
    
    Someone just posted a report that matches your item "{item_name}".
    
    New Report Details:
    --------------------------------
    Confidence: {match_score}%
    Contact this person: {current_contact}
    --------------------------------
    
    Please contact them to verify if it is your item.
    
    - Lost & Found Team
    """
    send_notification(matched_user_email, subject_2, body_2)
