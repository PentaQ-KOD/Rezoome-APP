import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)  # Add override=True to ensure variables are loaded

def get_email_settings():
    """Get email settings based on the provider specified in .env"""
    provider = os.getenv('EMAIL_PROVIDER', 'ZOHO').upper()
    
    # Use generic variables first, fall back to provider-specific ones
    settings = {
        'smtp_server': os.getenv('EMAIL_SMTP_SERVER') or os.getenv(f'{provider}_SMTP_SERVER'),
        'smtp_port': int(os.getenv('EMAIL_SMTP_PORT') or os.getenv(f'{provider}_SMTP_PORT')),
        'imap_server': os.getenv('EMAIL_IMAP_SERVER') or os.getenv(f'{provider}_IMAP_SERVER'),
        'imap_port': int(os.getenv('EMAIL_IMAP_PORT') or os.getenv(f'{provider}_IMAP_PORT')),
    }
    
    logger.info(f"Using email settings: {settings}")
    return settings

def send_email(
    recipient_email,
    subject,
    body,
    sender_email=None,
    sender_password=None,
    smtp_server=None,
    smtp_port=None
):
    """
    Send an email using the configured email provider.
    
    Args:
        recipient_email (str): Email address of the recipient
        subject (str): Subject of the email
        body (str): Body of the email
        sender_email (str, optional): Sender's email address. Defaults to EMAIL_USER from .env
        sender_password (str, optional): Sender's password. Defaults to EMAIL_PASSWORD from .env
        smtp_server (str, optional): SMTP server address. Defaults to provider's SMTP server
        smtp_port (int, optional): SMTP server port. Defaults to provider's SMTP port
    """
    try:
        # Get default values from environment variables if not provided
        sender_email = sender_email or os.getenv('EMAIL_USER')
        sender_password = sender_password or os.getenv('EMAIL_PASSWORD')
        
        # Verify environment variables are loaded
        if not sender_email or not sender_password:
            logger.error("Email credentials not found in environment variables")
            logger.error(f"EMAIL_USER: {os.getenv('EMAIL_USER')}")
            logger.error(f"EMAIL_PASSWORD: {'*' * len(os.getenv('EMAIL_PASSWORD', ''))}")
            return False, "Email credentials not found in environment variables"
        
        # Get email settings
        settings = get_email_settings()
        smtp_server = smtp_server or settings['smtp_server']
        smtp_port = smtp_port or settings['smtp_port']
        
        logger.info(f"Attempting to send email from {sender_email} to {recipient_email}")
        logger.info(f"Using SMTP server: {smtp_server}:{smtp_port}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP connection
        logger.info("Establishing SMTP connection...")
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            logger.info("SMTP connection established, attempting login...")
            server.login(sender_email, sender_password)
            logger.info("Login successful, sending message...")
            server.send_message(msg)
            logger.info("Message sent successfully")
            
        return True, "Email sent successfully"
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Authentication failed: {str(e)}")
        return False, "Authentication failed. Please check your email credentials."
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {str(e)}")
        return False, f"SMTP error occurred: {str(e)}"
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return False, f"An error occurred: {str(e)}" 