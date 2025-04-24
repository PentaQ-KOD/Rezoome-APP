import streamlit as st
from modules.email_fetcher import fetch_email_content
from modules.email_sender import send_email, get_email_settings
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(override=True)

# Page title and description
st.title("📧 Email Inbox")
st.markdown("View and reply to your emails")

# Get email credentials
email_credentials = {
    'email': os.getenv('EMAIL_USER'),
    'password': os.getenv('EMAIL_PASSWORD')
}

# Get email settings
try:
    settings = get_email_settings()
    email_credentials.update({
        'smtp_server': settings['smtp_server'],
        'smtp_port': settings['smtp_port']
    })
except Exception as e:
    st.error(f"Error loading email settings: {str(e)}")

# Add refresh button
if st.button("🔄 Refresh Inbox"):
    st.session_state.inbox_refreshed = True

# Fetch and display emails
try:
    emails = fetch_email_content(
        email_address=email_credentials['email'],
        password=email_credentials['password'],
        imap_server=settings['imap_server'],
        port=settings['imap_port'],
        limit=10
    )
    
    # Display emails in a list
    for index, email in enumerate(emails):
        with st.expander(f"📧 {email['subject']} - From: {email['from']} ({email['date']})"):
            st.markdown("### Email Content")
            st.text_area(
                "Content", 
                email['content'], 
                height=200, 
                disabled=True,
                key=f"email_content_{index}"
            )
            
            # Add reply button with unique key
            if st.button("Reply", key=f"reply_{index}_{email['from']}"):
                st.session_state.reply_to = email['from']
                st.session_state.reply_subject = f"Re: {email['subject']}"
                st.session_state.reply_body = f"\n\nOn {email['date']}, {email['from']} wrote:\n{email['content']}"

except Exception as e:
    st.error(f"Error fetching emails: {str(e)}")

# Add reply form if reply button is clicked
if 'reply_to' in st.session_state:
    with st.form("reply_form"):
        st.subheader(f"Reply to {st.session_state.reply_to}")
        st.text_input("To:", value=st.session_state.reply_to, disabled=True)
        
        # Get current subject and body values
        current_subject = st.text_input(
            "Subject:", 
            value=st.session_state.reply_subject,
            key="reply_subject_input"
        )
        current_body = st.text_area(
            "Message:", 
            value=st.session_state.reply_body, 
            height=200,
            key="reply_body_input"
        )
        
        if st.form_submit_button("Send Reply"):
            try:
                result = send_email(
                    recipient_email=st.session_state.reply_to,
                    subject=current_subject,
                    body=current_body,
                    sender_email=email_credentials['email'],
                    sender_password=email_credentials['password'],
                    smtp_server=settings['smtp_server'],
                    smtp_port=settings['smtp_port']
                )
                
                if result[0]:
                    st.success("Reply sent successfully!")
                    del st.session_state.reply_to
                    del st.session_state.reply_subject
                    del st.session_state.reply_body
                else:
                    st.error(f"Failed to send reply: {result[1]}")
            except Exception as e:
                st.error(f"Error sending reply: {str(e)}")

# Add some helpful information
st.markdown("""
### How to use:
1. Click on an email to view its content
2. Use the Reply button to respond to an email
3. Edit the subject and message as needed
4. Click Send Reply to send your response

### Notes:
- Only the 10 most recent emails are shown
- Click Refresh Inbox to update the list
- You can reply to any email in the list
""") 