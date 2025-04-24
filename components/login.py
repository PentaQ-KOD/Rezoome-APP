import streamlit as st
import imaplib
import os
from dotenv import load_dotenv
from database import MongoDB

# Load environment variables
load_dotenv()

db = MongoDB()

# IMAP server configurations
IMAP_SERVERS = {
    "Gmail": {
        "server": os.getenv('GMAIL_IMAP_SERVER', 'imap.gmail.com'),
        "port": int(os.getenv('GMAIL_IMAP_PORT', 993))
    },
    "Zoho": {
        "server": os.getenv('ZOHO_IMAP_SERVER', 'imap.zoho.com'),
        "port": int(os.getenv('ZOHO_IMAP_PORT', 993))
    },
    "Outlook": {
        "server": os.getenv('OUTLOOK_IMAP_SERVER', 'outlook.office365.com'),
        "port": int(os.getenv('OUTLOOK_IMAP_PORT', 993))
    }
}

def check_imap_credentials(email, password, imap_server="imap.gmail.com", port=993):
    """Verify IMAP credentials by attempting to connect to the email server."""
    try:
        mail = imaplib.IMAP4_SSL(imap_server, port)
        mail.login(email, password)
        mail.logout()
        return True
    except Exception as e:
        st.error(f"Failed to connect: {str(e)}")
        return False

def login_form():
    """Display login form and handle authentication."""
    st.title("🔐 Login to ReZoome")
    
    with st.form("login_form"):
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        
        # Email provider selection
        provider = st.selectbox(
            "Email Provider",
            options=list(IMAP_SERVERS.keys()) + ["Other"],
            index=0
        )
        
        # Custom server input if "Other" is selected
        custom_server = None
        custom_port = None
        if provider == "Other":
            col1, col2 = st.columns(2)
            with col1:
                custom_server = st.text_input("Custom IMAP Server")
            with col2:
                custom_port = st.number_input("Custom IMAP Port", value=993, min_value=1, max_value=65535)
        
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if not all([email, password]):
                st.warning("Please fill in all fields")
                return False
            
            # Get server configuration
            if provider == "Other":
                if not custom_server:
                    st.warning("Please provide a custom IMAP server")
                    return False
                server = custom_server
                port = custom_port
            else:
                server = IMAP_SERVERS[provider]["server"]
                port = IMAP_SERVERS[provider]["port"]
            
            if check_imap_credentials(email, password, server, port):
                # Store credentials in session state
                st.session_state['logged_in'] = True
                st.session_state['email'] = email
                st.session_state['password'] = password
                st.session_state['imap_server'] = server
                st.session_state['imap_port'] = port
                
                # Update .env file with email credentials
                try:
                    with open('.env', 'r') as file:
                        env_lines = file.readlines()
                    
                    # Update email credentials
                    updated_lines = []
                    for line in env_lines:
                        if line.startswith('EMAIL_USER='):
                            updated_lines.append(f'EMAIL_USER={email}\n')
                        elif line.startswith('EMAIL_PASSWORD='):
                            updated_lines.append(f'EMAIL_PASSWORD={password}\n')
                        else:
                            updated_lines.append(line)
                    
                    with open('.env', 'w') as file:
                        file.writelines(updated_lines)
                except Exception as e:
                    st.error(f"Error updating .env file: {str(e)}")
                    return False
                
                # Store in database
                db.insert_user(
                    hr_id=email,  # Using email as ID
                    name=email.split('@')[0],  # Using username part as name
                    email=email,
                    role="HR"
                )
                
                st.success("Login successful!")
                return True
            else:
                st.error("Invalid credentials")
                return False
    
    return False

def logout_button():
    """Display logout button and handle logout."""
    if st.sidebar.button("Logout"):
        # Clear session state
        for key in ['logged_in', 'email', 'password', 'imap_server', 'imap_port']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

def is_logged_in():
    """Check if user is logged in."""
    return st.session_state.get('logged_in', False)

def get_user_credentials():
    """Get stored user credentials."""
    if is_logged_in():
        return {
            'email': st.session_state.get('email'),
            'password': st.session_state.get('password'),
            'imap_server': st.session_state.get('imap_server'),
            'imap_port': st.session_state.get('imap_port')
        }
    return None 