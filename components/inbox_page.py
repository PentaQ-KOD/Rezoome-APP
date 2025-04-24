import nest_asyncio

nest_asyncio.apply()

import streamlit as st
from modules.email_fetcher import fetch_attachments_and_classify
from database import MongoDB
from components.login import is_logged_in, get_user_credentials, logout_button

db = MongoDB()

# Check if user is logged in
if not is_logged_in():
    st.warning("Please log in to access the inbox.")
    st.stop()

# Get user credentials
credentials = get_user_credentials()

# Title and description
st.title("📥 Email Inbox")
st.markdown("Fetch and analyze recent emails for resumes")

# Sidebar with logout button
with st.sidebar:
    st.markdown("### User Info")
    st.markdown(f"**Email:** {credentials['email']}")
    st.markdown(f"**Server:** {credentials['imap_server']}")
    #logout_button()

# Main content
with st.form("inbox_form"):
    # Email count selection
    email_count = st.selectbox(
        "Number of recent emails to fetch",
        options=[1, 5, 10, 20],
        index=1,  # Default to 5
        help="Select how many of the most recent emails to process"
    )
    
    # Submit button
    submitted = st.form_submit_button("Fetch and Analyze Emails")

    if submitted:
        with st.spinner("Connecting to email server and processing..."):
            try:
                # Call the email fetcher with the selected count
                processed_count = fetch_attachments_and_classify(
                    email_address=credentials['email'],
                    password=credentials['password'],
                    imap_server=credentials['imap_server'],
                    port=credentials['imap_port'],
                    email_count=email_count
                )
                
                if processed_count > 0:
                    st.success(f"✅ Successfully processed {processed_count} resume(s) from emails!")
                else:
                    st.info("No new resumes found in the recent emails.")
                    
            except Exception as e:
                st.error(f"❌ Error processing emails: {str(e)}")

# Add some helpful information
st.markdown("""
### How it works:
1. Select the number of recent emails you want to process
2. Click "Fetch and Analyze Emails"
3. The system will:
   - Connect to your email server
   - Download the selected number of recent emails
   - Process any attached PDFs
   - Extract and analyze resume information
   - Store the results in the database

### Notes:
- Only PDF attachments are processed
- Each email is processed only once
- Resumes are automatically classified and stored in the database
- You can view processed resumes in the Candidates Dashboard
""")
