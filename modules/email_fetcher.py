# email_fetcher.py

import imaplib
import email
from email.header import decode_header
import tempfile

from modules.classify_text import classify_text
from modules.parse_pdf import ResumeProcessor
from modules.embed import get_embedding
from database import MongoDB

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


def connect_imap(email_address, password, imap_server):
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(email_address, password)
    return mail


def fetch_attachments_and_classify(
    email_address, password, imap_server="imap.zoho.com"
):
    mail = connect_imap(email_address, password, imap_server)
    mail.select("inbox")

    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()

    processor = ResumeProcessor()

    for eid in email_ids:
        _, msg_data = mail.fetch(eid, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                message_id = msg.get("Message-ID")
                if db.has_message_id(message_id):
                    print(f"🔁 Message {message_id} already processed. Skipping.")
                    continue

                subject, encoding = decode_header(msg["Subject"])[0]
                subject = (
                    subject.decode(encoding or "utf-8")
                    if isinstance(subject, bytes)
                    else subject
                )
                from_ = msg.get("From")
                print(f"📧 From: {from_} | Subject: {subject}")

                # ถ้าอีเมลมีไฟล์แนบ
                for part in msg.walk():
                    if part.get_content_maintype() == "multipart":
                        continue
                    if part.get("Content-Disposition") is None:
                        continue

                    filename = part.get_filename()
                    if filename:
                        filename = decode_header(filename)[0][0]
                        filename = (
                            filename.decode()
                            if isinstance(filename, bytes)
                            else filename
                        )

                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".pdf"
                        ) as tmp_file:
                            tmp_file.write(part.get_payload(decode=True))
                            tmp_path = tmp_file.name

                        print(f"📎 Saved attachment: {filename}")

                        # ดึงข้อความจาก PDF
                        resume_text = processor.load_pdf(tmp_path)

                        # ทำการ classify ด้วย LLM
                        classification = classify_text(resume_text)
                        print(f"🧠 LLM classified file as: {classification}")

                        # ถ้าเป็น Resume/CV ค่อยประมวลผลต่อ
                        keywords = [
                            "Resume",
                            "CV",
                            "Job Description",
                            "Job Application",
                            "Interview",
                            "Offer",
                        ]

                        if classification and any(
                            keyword in classification for keyword in keywords
                        ):
                            print("📄 Processing resume file...")
                            personal_info, resume_info = processor.extract_resume_info(
                                resume_text
                            )
                            print(f"📊 Extracted Resume Info:\n{resume_info}")
                            embedding = get_embedding(resume_text)
                            print(f"🔗 Generated embedding: {embedding}")
                        else:
                            print("❌ File is not a resume. Skipping.")

                        # ==========================DATABASE============================
                        candidate_id = "Email_" + (message_id or str(eid))

                        db.insert_candidate(
                            candidate_id, personal_info, resume_text, embedding
                        )
                        db.insert_auth_message(message_id)

    mail.logout()
