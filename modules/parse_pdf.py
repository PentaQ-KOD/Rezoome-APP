# resume_processor.py
import re
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
from pythainlp.tokenize import word_tokenize
from pythainlp.corpus.common import thai_stopwords
import tempfile
from fixthaipdf import clean
import nltk
from nltk.corpus import stopwords
from modules.embed import get_embedding
from utils.database import MongoDB
from dotenv import load_dotenv
from modules.job_description import call_llama
from together import Together
import json

load_dotenv()
together = Together()

# bring in deps
from llama_cloud_services import LlamaParse
from llama_index.core import SimpleDirectoryReader

nltk.download("stopwords")


class ResumeProcessor:
    def __init__(
        self,
        db_uri="mongodb+srv://inpantawat22:1234@agents.ci2qy.mongodb.net/",
        db_name="db_rezoome",
    ):
        self.db = MongoDB(uri=db_uri, db_name=db_name)
        self.parser = LlamaParse(fast_mode=True)  # ใช้ fast_mode สำหรับการประมวลผลเร็วขึ้น

    def load_pdf(self, file_path):
        """โหลดและดึงข้อความจาก PDF"""
        try:
            try:
                # ใช้ LlamaParse ก่อน (วิธีหลัก)
                documents = SimpleDirectoryReader(
                    input_files=[file_path], file_extractor={".pdf": self.parser}
                ).load_data()

                text = "\n".join([doc.text for doc in documents])
                print(f"📄 Loaded and parsed PDF text with LlamaParse")
                return text
            except Exception as e:
                print(f"❌ Error using LlamaParse: {e}")
                
                # ถ้า LlamaParse ล้มเหลว ลองใช้ PyPDFLoader (วิธีสำรอง)
                try:
                    from langchain_community.document_loaders import PyPDFLoader
                    print("📄 Trying alternative method (PyPDFLoader)...")
                    loader = PyPDFLoader(file_path)
                    documents = loader.load()
                    text = "\n".join([doc.page_content for doc in documents])
                    print("📄 Successfully loaded PDF with PyPDFLoader")
                    return text
                except Exception as pdf_error:
                    print(f"❌ Error using PyPDFLoader: {pdf_error}")
                    return None
                
        except Exception as main_error:
            print(f"❌ Main error in load_pdf: {main_error}")
            return None

    def clean_text(self, text):
        # ใช้ fixthaipdf เพื่อล้างข้อมูลเบื้องต้น
        cleaned_text = clean(text)

        # เก็บอีเมลไว้ก่อนลบ stopwords และ tokenization
        email_matches = list(
            re.finditer(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", cleaned_text)
        )
        emails = {m.start(): m.group() for m in email_matches}

        # แปลงข้อความให้เป็น lowercase และลบช่องว่างเกิน
        # cleaned_text = cleaned_text.lower()
        cleaned_text = " ".join(cleaned_text.split())

        # Tokenization (Thai + English)
        tokens = word_tokenize(cleaned_text, engine="newmm")

        # ลบ stopwords (ภาษาไทย + ภาษาอังกฤษ)
        stop_words = set(thai_stopwords()).difference({"นาย", "นาง", "นางสาว"})
        english_stopwords = set(stopwords.words("english"))

        tokens = [
            word
            for word in tokens
            if word not in stop_words and word not in english_stopwords
        ]

        # รวมข้อความหลังลบ stopwords และ tokenization
        result_text = " ".join(tokens)

        # ใส่อีเมลกลับในตำแหน่งเดิม
        for pos in sorted(emails.keys(), reverse=True):
            result_text = result_text[:pos] + emails[pos] + result_text[pos:]

        return result_text

    def get_full_resume_text(self, text):
        resume_text = self.load_pdf(text)
        # resume_text = self.clean_text(resume_text)
        return resume_text

    def process_pdf(self, file):
        """ดึงข้อความจาก PDF และสร้าง embedding และแยกทักษะ"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file.read())
            temp_path = temp_file.name

        resume_text = self.load_pdf(temp_path)
        print(f"🔍 Cleaned Resume Text:\n{resume_text}")
        embedding = get_embedding(resume_text)
        if embedding:
            print(f"✅ Embedding generated successfully:\n{embedding}")
        else:
            print("❌ Embedding generation failed.")
            return None, None

        return resume_text, embedding

    def extract_resume_info(self, resume_text):
        """ส่งข้อความไปยัง LLM เพื่อแยกข้อมูลเรซูเม่"""
        # แยกข้อมูลส่วนบุคคลก่อน
        personal_info_prompt = """
        คุณคือ Senior Human Resource Specialist ที่มีความเชี่ยวชาญในการวิเคราะห์เรซูเม่ของผู้สมัครงาน 
        บทบาทของคุณคือช่วยแยกข้อมูลส่วนบุคคลจากเรซูเม่

        กฎสำคัญ:
        1. คุณต้องส่งคืนเฉพาะ JSON เท่านั้น
        2. ห้ามใช้เครื่องหมาย ``` หรือข้อความอื่นใดนอกเหนือจาก JSON
        3. JSON ต้องเริ่มต้นด้วย { และจบด้วย } เท่านั้น
        4. ถ้าไม่พบข้อมูล ให้ใช้ค่า null
        5. ไม่ต้องแปลงข้อมูลให้เป็นภาษาไทย

        โปรดแยกข้อมูลส่วนบุคคลจากเรซูเม่ดังนี้:
        1. ชื่อ-นามสกุล: มักจะอยู่ที่ส่วนบนของเรซูเม่
        2. อีเมล: มักจะมีรูปแบบ xxx@xxx.xxx
        3. เบอร์โทรศัพท์: มักจะมีรูปแบบ 0XX-XXX-XXXX หรือ +66XX-XXX-XXXX
        4. ที่อยู่: มักจะอยู่หลังข้อมูลติดต่อ
        5. ตำแหน่งที่สนใจ: มักจะอยู่หลังข้อมูลส่วนตัว หรือในส่วนของ Career Objective

        โครงสร้าง JSON ที่ต้องการ:
        {
            "name": "ชื่อ-นามสกุล",
            "email": "อีเมล",
            "phone": "เบอร์โทรศัพท์",
            "address": "ที่อยู่",
            "position": "ตำแหน่งที่สนใจ"
        }
        """

        try:
            # แยกข้อมูลส่วนบุคคล
            personal_response = together.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=[
                    {"role": "system", "content": personal_info_prompt},
                    {"role": "user", "content": resume_text},
                ],
                temperature=0.3,
            )
            
            personal_info = personal_response.choices[0].message.content.strip()
            print(f"Personal Info Response: {personal_info}")
            
            # ทำความสะอาด response
            if personal_info.startswith("```json"):
                personal_info = personal_info.replace("```json", "").strip()
            if personal_info.startswith("```"):
                personal_info = personal_info.replace("```", "").strip()
            if personal_info.endswith("```"):
                personal_info = personal_info.replace("```", "").strip()
                
            personal_data = json.loads(personal_info)
            print(f"Parsed Personal Data: {personal_data}")
            
        except Exception as e:
            print(f"Error extracting personal info: {e}")
            personal_data = {
                "name": None,
                "email": None,
                "phone": None,
                "address": None,
                "position": None
            }

        # แยกข้อมูลอื่นๆ
        other_info_prompt = """
        คุณคือ Senior Human Resource Specialist ที่มีความเชี่ยวชาญในการวิเคราะห์เรซูเม่ของผู้สมัครงาน 
        บทบาทของคุณคือช่วยสรุปข้อมูลที่สำคัญจากเรซูเม่ในรูปแบบ JSON ที่มีโครงสร้างชัดเจน

        กฎสำคัญ:
        1. คุณต้องส่งคืนเฉพาะ JSON เท่านั้น
        2. ห้ามใช้เครื่องหมาย ``` หรือข้อความอื่นใดนอกเหนือจาก JSON
        3. JSON ต้องเริ่มต้นด้วย { และจบด้วย } เท่านั้น
        4. ถ้าไม่พบข้อมูล ให้ใช้ค่า null
        5. ไม่ต้องแปลงข้อมูลให้เป็นภาษาไทย

        โครงสร้าง JSON ที่ต้องการ:
        {
            "education": [
                {
                    "degree": "วุฒิการศึกษา",
                    "institution": "สถาบันการศึกษา",
                    "year": "ปีที่จบ",
                    "major": "สาขาวิชา",
                    "gpa": "เกรดเฉลี่ย"
                }
            ],
            "work_experience": [
                {
                    "position": "ตำแหน่ง",
                    "company": "บริษัท",
                    "duration": "ระยะเวลา",
                    "responsibilities": "หน้าที่ความรับผิดชอบ"
                }
            ],
            "skills": {
                "technical": ["ทักษะทางเทคนิค 1", "ทักษะทางเทคนิค 2"],
                "soft": ["ทักษะส่วนบุคคล 1", "ทักษะส่วนบุคคล 2"]
            },
            "languages": {
                "ภาษา": "ระดับความสามารถ"
            },
            "certifications": [
                {
                    "name": "ชื่อใบรับรอง",
                    "issuer": "ผู้ให้การรับรอง",
                    "year": "ปีที่ได้รับ"
                }
            ],
            "projects": [
                {
                    "name": "ชื่อโครงการ",
                    "description": "รายละเอียด",
                    "year": "ปีที่ทำ"
                }
            ],
            "hobbies": ["งานอดิเรก 1", "งานอดิเรก 2"],
            "references": [
                {
                    "name": "ชื่อผู้อ้างอิง",
                    "relationship": "ความสัมพันธ์",
                    "contact": "ข้อมูลติดต่อ"
                }
            ]
        }
        """

        try:
            # แยกข้อมูลอื่นๆ
            other_response = together.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=[
                    {"role": "system", "content": other_info_prompt},
                    {"role": "user", "content": resume_text},
                ],
                temperature=0.3,
            )
            
            other_info = other_response.choices[0].message.content.strip()
            print(f"Other Info Response: {other_info}")
            
            # ทำความสะอาด response
            if other_info.startswith("```json"):
                other_info = other_info.replace("```json", "").strip()
            if other_info.startswith("```"):
                other_info = other_info.replace("```", "").strip()
            if other_info.endswith("```"):
                other_info = other_info.replace("```", "").strip()
                
            other_data = json.loads(other_info)
            print(f"Parsed Other Data: {other_data}")
            
        except Exception as e:
            print(f"Error extracting other info: {e}")
            other_data = {
                "education": [],
                "work_experience": [],
                "skills": {"technical": [], "soft": []},
                "languages": {},
                "certifications": [],
                "projects": [],
                "hobbies": [],
                "references": []
            }

        # รวมข้อมูล
        final_data = {**personal_data, **other_data}
        print(f"Final Data: {final_data}")
        
        return final_data
