import streamlit as st

# Streamlit interface - MUST be first Streamlit command
st.set_page_config(
    layout="wide", 
    page_title="ReZoome - HR Dashboard", 
    page_icon="👔"
)

# Import other modules after page config
from database import MongoDB
from components.login import login_form, is_logged_in, logout_button

# from modules.parse_pdf import ResumeProcessor
# from modules.classify_text import classify_text
# import modules.job_description as job_description
# from modules.embed import get_embedding
# import pandas as pd
# from datetime import datetime

# Initialize MongoDB connection
db = MongoDB()

# Main app logic
def main():
    # Check if user is logged in
    if not is_logged_in():
        # Show login form
        if login_form():
            st.rerun()
    else:
        # Show navigation and other components
        pages = {
            "Your account": [
                st.Page("components/candidates_dashboard.py", title="Candidates Dashboard"),
                st.Page("components/resume_upload.py", title="Resume Upload"),
                st.Page("components/job_dashboard.py", title="Job Descriptions"),
            ],
            "Email": [
                st.Page("components/inbox_page.py", title="Fetch Resumes from Email"),
                st.Page("components/email_inbox_page.py", title="View & Reply Emails"),
            ],
        }

        # Add logout button to sidebar
        with st.sidebar:
            st.write(f"Welcome, {st.session_state.get('email', 'User')}")
            logout_button()

        # Show navigation
        pg = st.navigation(pages)
        pg.run()

if __name__ == "__main__":
    main()


