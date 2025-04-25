# email_fetcher.py

import imaplib
import email
from email.header import decode_header
import tempfile
import os
from datetime import datetime

from modules.classify_text import classify_text
from modules.parse_pdf import ResumeProcessor
from modules.embed import get_embedding
from modules.job_description import analyze_resume
from utils.database import MongoDB

db = MongoDB()


class MongoDB:
    def __init__(self):
        self.auth_message = self.db["inbox_auth"]
        self.resume = self.db["resume"]
        self.candidates = self.db["candidates"]
        pass

    def insert_candidate(self, candidate_id, personal_info, resume_text, embedding):
        # Insert candidate information into MongoDB
        pass

    def has_message_id(self, message_id):
        return self.auth_message.find_one({"message_id": message_id}) is not None

    def insert_auth_message(self, message_id):
        self.auth_message.insert_one({"message_id": message_id})


def connect_imap(email_address, password, imap_server, port=993):
    """Connect to IMAP server with SSL."""
    try:
        mail = imaplib.IMAP4_SSL(imap_server, port)
        mail.login(email_address, password)
        return mail
    except Exception as e:
        raise Exception(f"Failed to connect to IMAP server: {str(e)}")


def decode_email_header(header):
    """Decode email header with proper encoding."""
    if not header:
        return ""
    decoded_header = decode_header(header)
    if not decoded_header:
        return ""
    text, encoding = decoded_header[0]
    if isinstance(text, bytes):
        return text.decode(encoding or 'utf-8', errors='ignore')
    return text


def fetch_attachments_and_classify(
    email_address, password, imap_server, email_count=10, port=993
):
    """Fetch and process emails with attachments.
    
    Args:
        email_address (str): Email address to fetch from
        password (str): Email password
        imap_server (str): IMAP server address
        email_count (int): Number of recent emails to process
        port (int): IMAP server port
    """
    try:
        # Connect to IMAP server
        mail = connect_imap(email_address, password, imap_server, port)
        mail.select("inbox")

        # Search for recent emails
        status, messages = mail.search(None, "ALL")
        if status != 'OK':
            raise Exception("Failed to search emails")

        email_ids = messages[0].split()
        recent_email_ids = email_ids[-email_count:] if email_count > 0 else email_ids

        processor = ResumeProcessor()
        processed_count = 0

        for eid in recent_email_ids:
            try:
                # Fetch the email
                status, msg_data = mail.fetch(eid, "(RFC822)")
                if status != 'OK':
                    continue

                # Parse the email
                msg = email.message_from_bytes(msg_data[0][1])
                message_id = msg.get("Message-ID", "")

                # Skip if already processed
                if db.has_message_id(message_id):
                    continue

                # Get email details
                subject = decode_email_header(msg["Subject"])
                from_addr = decode_email_header(msg["From"])
                date = msg.get("Date", "")

                print(f"📧 Processing email: {subject} from {from_addr}")

                # Process attachments
                for part in msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue

                    filename = part.get_filename()
                    if not filename:
                        continue

                    # Decode filename
                    filename = decode_email_header(filename)
                    if not filename.lower().endswith('.pdf'):
                        continue

                    # Save attachment
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(part.get_payload(decode=True))
                        tmp_path = tmp_file.name

                    try:
                        # Process PDF
                        resume_text = processor.load_pdf(tmp_path)
                        if not resume_text:
                            continue

                        # Classify text
                        classification = classify_text(resume_text)
                        if not classification or "Resume" not in classification:
                            continue

                        # Extract resume info using the correct method
                        resume_info = processor.extract_resume_info(resume_text)
                        embedding = get_embedding(resume_text)

                        # Prepare candidate data
                        candidate_id = f"email_{message_id}"
                        candidate_data = {
                            "candidate_id": candidate_id,
                            "name": resume_info.get("name", ""),
                            "email": resume_info.get("email", ""),
                            "phone": resume_info.get("phone", ""),
                            "address": resume_info.get("address", ""),
                            "position": resume_info.get("position", ""),
                            "education": resume_info.get("education", []),
                            "skills": resume_info.get("skills", {"technical": [], "soft": []}),
                            "work_experience": resume_info.get("work_experience", []),
                            "source": "email",
                            "source_details": {
                                "email_subject": subject,
                                "from_email": from_addr,
                                "received_date": date
                            },
                            "parsed_text": resume_text,
                            "embedding": embedding,
                            "created_at": datetime.now()
                        }

                        # Save to database
                        db.insert_candidate(
                            candidate_id=candidate_id,
                            personal_info=resume_info,
                            parsed_text=resume_text,
                            embedding=embedding
                        )

                        # Run job matching analysis
                        matching_results = analyze_resume(resume_text, candidate_id, optimize=True)
                        
                        # Store matching results
                        if matching_results:
                            db.insert_matching_result(
                                candidate_id=candidate_id,
                                matching_scores=matching_results,
                                detailed_results=matching_results
                            )

                        db.insert_auth_message(message_id)
                        processed_count += 1

                    finally:
                        # Clean up temporary file
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)

            except Exception as e:
                print(f"Error processing email {eid}: {str(e)}")
                continue

        mail.logout()
        return processed_count

    except Exception as e:
        raise Exception(f"Failed to process emails: {str(e)}")


def fetch_email_content(email_address, password, imap_server, port=993, limit=10):
    """Fetch recent emails from inbox.
    
    Args:
        email_address (str): Email address to fetch from
        password (str): Email password
        imap_server (str): IMAP server address
        port (int): IMAP server port
        limit (int): Number of emails to fetch
        
    Returns:
        list: List of email dictionaries with subject, from, date, and content
    """
    try:
        # Connect to IMAP server
        mail = connect_imap(email_address, password, imap_server, port)
        mail.select("inbox")

        # Search for recent emails
        status, messages = mail.search(None, "ALL")
        if status != 'OK':
            raise Exception("Failed to search emails")

        email_ids = messages[0].split()
        recent_email_ids = email_ids[-limit:] if limit > 0 else email_ids

        emails = []
        for eid in recent_email_ids:
            try:
                # Fetch the email
                status, msg_data = mail.fetch(eid, "(RFC822)")
                if status != 'OK':
                    continue

                # Parse the email
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Get email details
                subject = decode_email_header(msg["Subject"])
                from_addr = decode_email_header(msg["From"])
                date = msg.get("Date", "")
                
                # Get email content
                content = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            content = part.get_payload(decode=True).decode()
                            break
                else:
                    content = msg.get_payload(decode=True).decode()
                
                emails.append({
                    "subject": subject,
                    "from": from_addr,
                    "date": date,
                    "content": content
                })
                
            except Exception as e:
                print(f"Error processing email {eid}: {str(e)}")
                continue

        mail.logout()
        return emails

    except Exception as e:
        raise Exception(f"Failed to fetch emails: {str(e)}")
