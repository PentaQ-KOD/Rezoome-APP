from sklearn.metrics.pairwise import cosine_similarity
from modules.embed import get_embedding
import together
from together import Together
from dotenv import load_dotenv
from database import MongoDB
import os

# Load API Key
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    raise ValueError("API Key is missing. Please check your .env file.")

together = Together()
together.api_key = TOGETHER_API_KEY


def call_llama(prompt):
    """Call Llama for streaming response."""
    try:
        response = together.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.5,
            stream=True,  # ✅ เปิดใช้งาน Streaming
        )

        for chunk in response:
            if (
                chunk.choices
                and chunk.choices[0].delta
                and chunk.choices[0].delta.content
            ):
                yield chunk.choices[0].delta.content  # ✅ ส่งข้อความออกทีละส่วน
    except Exception as e:
        print(f"Error: {e}")
        yield "Error: Unable to generate response."


def analyze_resume(resume_text, candidate_id=None, optimize=False):
    """Analyze a resume and return job matching scores + store results."""
    db = MongoDB()
    job_descriptions = db.get_all_job_descriptions()

    job_embeddings = {
        position: data["embedding"]
        for position, data in job_descriptions.items()
        if data["embedding"] is not None
    }

    resume_embedding = get_embedding(resume_text)

    if resume_embedding is None:
        return {}

    # Calculate base matching scores using cosine similarity
    base_scores = {
        position: cosine_similarity([resume_embedding], [job_embedding])[0][0]
        for position, job_embedding in job_embeddings.items()
    }

    # Calculate keyword matching scores
    matching_scores = {}
    for position, cosine_score in base_scores.items():
        job_requirements = job_descriptions[position]["requirements"].lower()
        resume_lower = resume_text.lower()
        
        # Extract meaningful keywords (words longer than 3 characters)
        keywords = [word for word in job_requirements.split() if len(word) > 3]
        if not keywords:
            keyword_score = 0
        else:
            # Count matching keywords
            matches = sum(1 for keyword in keywords if keyword in resume_lower)
            # Calculate keyword score (0-30 points)
            keyword_score = (matches / len(keywords)) * 30
        
        # Combine scores with weights:
        # - Cosine similarity: 70% of final score
        # - Keyword matching: 30% of final score
        final_score = (cosine_score * 70) + keyword_score
        
        # Round to 2 decimal places
        matching_scores[position] = round(final_score, 2)

    # Prepare data for database
    match_result_doc = {
        "candidate_id": candidate_id,
        "matching_scores": matching_scores,
    }

    if optimize:
        results = {}
        for position, score in matching_scores.items():
            job_requirements = job_descriptions[position]["requirements"]

            summary = "".join(
                call_llama(
                    f"""คุณเป็น HR ที่กำลังประเมินความเหมาะสมระหว่างผู้สมัครกับตำแหน่งงาน 
                    ตำแหน่งงาน: {position}
                    ความต้องการของงาน: {job_requirements}
                    เรซูเม่ของผู้สมัคร: {resume_text}
                    
                    กรุณาสรุปการประเมินในรูปแบบต่อไปนี้ (ขึ้นบรรทัดใหม่ทุกหัวข้อ):
                    
                    [ความเหมาะสมกับงาน]
                    - สรุปความเหมาะสมโดยรวมกับตำแหน่งงาน
                    
                    [จุดเด่น]
                    - ทักษะและประสบการณ์ที่ตรงกับงานและเป็นจุดเด่นของผู้สมัคร
                    
                    [ข้อควรพัฒนา]
                    - ทักษะหรือประสบการณ์ที่ควรพัฒนาเพิ่มเติมเพื่อให้เหมาะสมกับงานมากขึ้น
                    
                    เขียนให้กระชับ อ่านเข้าใจง่าย เป็นธรรมชาติ เหมือน HR พูดกับเพื่อนร่วมงาน โดยไม่เกิน 300 ตัวอักษร
                    อย่าลืมขึ้นบรรทัดใหม่ทุกหัวข้อ"""
                )
            )

            results[position] = {"score": score, "summary": summary}

        match_result_doc["detailed_results"] = results
    else:
        match_result_doc["detailed_results"] = None

    # Save to database
    db.matching_results_collection.insert_one(match_result_doc)

    return match_result_doc["detailed_results"] or matching_scores
