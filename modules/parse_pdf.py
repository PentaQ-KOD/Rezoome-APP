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
from database import MongoDB
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
                    
                    # ถ้ายังล้มเหลวอีก ลองวิธีสุดท้ายที่ง่ายที่สุด
                    try:
                        import PyPDF2
                        print("📄 Trying last resort method (PyPDF2)...")
                        with open(file_path, 'rb') as file:
                            reader = PyPDF2.PdfReader(file)
                            text = ""
                            for page_num in range(len(reader.pages)):
                                text += reader.pages[page_num].extract_text() + "\n"
                        
                        if text.strip():
                            print("📄 Successfully loaded PDF with PyPDF2")
                            return text
                        else:
                            print("❌ PyPDF2 failed to extract text")
                            return None
                    except Exception as pypdf2_error:
                        print(f"❌ Error using PyPDF2: {pypdf2_error}")
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
        system_prompt = f"""
        คุณคือ Senior Human Resource Specialist ที่มีความเชี่ยวชาญในการวิเคราะห์เรซูเม่ของผู้สมัครงาน 
        บทบาทของคุณคือช่วยสรุปข้อมูลที่สำคัญจากเรซูเม่ในรูปแบบ JSON เพื่อให้กระบวนการสรรหาบุคลากรมีประสิทธิภาพมากขึ้น  

        โปรดดึงข้อมูลต่อไปนี้จากเรซูเม่ของผู้สมัคร:  

        - **name**: ชื่อ-นามสกุลของผู้สมัคร  
        - **email**: อีเมลติดต่อ  
        - **phone**: หมายเลขโทรศัพท์  
        - **address**: ที่อยู่ปัจจุบัน  
        - **position**: ตำแหน่งที่ผู้สมัครสนใจ  
        - **education**: ประวัติการศึกษา (รวมถึงระดับการศึกษา, ชื่อสถาบัน และปีที่จบการศึกษา)  
        - **work_experience**: ประสบการณ์ทำงาน (รวมถึงชื่อตำแหน่ง, ชื่อบริษัท, ระยะเวลาทำงาน และหน้าที่ความรับผิดชอบโดยสังเขป)  
        - **skills**: ทักษะที่เกี่ยวข้อง (ทั้ง Hard Skills และ Soft Skills)  
        - **languages**: ความสามารถทางภาษา (ระบุระดับความเชี่ยวชาญ เช่น พื้นฐาน, ปานกลาง, ดี, ดีมาก)  
        - **certifications**: ใบรับรองทางวิชาชีพหรือประกาศนียบัตรที่เกี่ยวข้อง  
        - **projects**: โครงการที่เคยทำ (รวมถึงชื่อโครงการ, รายละเอียดโดยย่อ และปีที่ดำเนินการ)  
        - **hobbies**: งานอดิเรกหรือความสนใจส่วนตัวที่อาจเกี่ยวข้องกับตำแหน่งงาน  
        - **references**: บุคคลอ้างอิง (ชื่อ, ความสัมพันธ์ และข้อมูลติดต่อ)  

        โปรดส่งข้อมูลในรูปแบบ JSON ที่มีโครงสร้างชัดเจน และสะท้อนข้อมูลที่สำคัญต่อการพิจารณารับสมัครงาน 
        Output JSON อย่างเดียว โดยไม่ต้องอธิบายหรือให้ความคิดเห็นเพิ่มเติม
        ถ้าไม่พบข้อมูลในเรซูเม่ ให้ส่งค่านั้นเป็น NULL 
        """

        response = together.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": resume_text},
            ],
            temperature=0.3,
        )

        extracted_info = response.choices[0].message.content

        # ตรวจสอบและทำความสะอาดข้อมูล JSON
        try:
            # ลบอักขระที่ไม่จำเป็นและขอบเขต code block ที่อาจมี
            cleaned_json = re.sub(r"^```json|```$", "", extracted_info.strip())
            # แปลงเป็น Python dict
            json_data = json.loads(cleaned_json)
            return json_data  # ส่งกลับเป็น dict แทนที่จะเป็น string
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON from LLM response: {e}")
            print(f"LLM raw response: {extracted_info}")
            # สร้าง dict ว่างเป็นค่าเริ่มต้น
            return {
                "name": None,
                "email": None,
                "phone": None,
                "address": None,
                "education": None,
                "skills": None,
                "work_experience": None,
                "certifications": None,
                "projects": None,
                "hobbies": None,
                "references": None,
                "position": None,
                "languages": None,
            }
