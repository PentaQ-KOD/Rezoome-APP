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


def analyze_resume(resume_text, optimize=False):
    """Analyze a resume and return job matching scores."""
    job_descriptions = MongoDB().get_all_job_descriptions()  # ✅ แก้ให้เรียกใช้ instance

    job_embeddings = {
        position: data["embedding"]
        for position, data in job_descriptions.items()
        if data["embedding"] is not None
    }

    resume_embedding = get_embedding(resume_text)

    if resume_embedding is None:
        return {}

    matching_scores = {
        position: cosine_similarity([resume_embedding], [job_embedding])[0][0] * 100
        for position, job_embedding in job_embeddings.items()
    }

    if optimize:
        results = {}
        for position, score in matching_scores.items():
            job_requirements = job_descriptions[position]["requirements"]

            # สร้างข้อความ Prompt สำหรับ LLM
            summary = "".join(
                call_llama(
                    f"สรุปทักษะที่ตรงกันระหว่างเรซูเม่: {resume_text} และความต้องการของงาน: {job_requirements} พร้อมระบุทักษะที่ยังขาดหรือควรพัฒนาเพิ่มเติม สรุปให้กระชับ อ่านเข้าใจง่าย โดยไม่เกิน 500 ตัวอักษรในแต่ละตำแหน่ง"
                )
            )

            results[position] = (score, summary)

    return results


# summary_prompt = (
#     f"วิเคราะห์เรซูเม่นี้เพื่อประเมินการจับคู่กับตำแหน่ง '{job_requirements}' "
#     f"คะแนน: {score:.2f}%\n"
#     f"จุดแข็ง: สรุปskillที่ตรงกับความต้องการของงาน\n"
#     f"จุดอ่อน: สรุปskillที่ขาดหายไปหรือควรพัฒนา\n"
#     f"และแนะนำวิธีการพัฒนาทักษะแบบสรุป"
# )
# summary = call_llama(summary_prompt)

# summary = "".join(
#     call_llama(
#         f"ให้สรุปว่าทำไมคะแนนความเหมาะสมอยู่ที่ {score:.2f}% "
#         f"โดยพิจารณาจากเรซูเม่: {resume_text} และความต้องการของงาน: {job_requirements} โดยดูว่า skill ไหนที่เหมาะสม และ skill ไหนที่ต้องพัฒนา"
#     )
# )

#     return {
#         position: f"{score:.2f}% - {call_llama(f'Given the resume and job description, explain why the match score is {score:.2f}%')}"
#         for position, score in matching_scores.items()
#     }

# return {position: f"{score:.2f}%" for position, score in matching_scores.items()}

#     # --- 5. ใช้ Llama วิเคราะห์ผลลัพธ์ Matching Score ---
# results = {}
# for position, score in matching_scores.items():
#     analysis_prompt = f"""
#     Given a resume with skills: {optimized_resume}, and a job description: {optimized_job_descriptions[position]},
#     explain why the matching score is {score:.2f}%. Highlight strengths and weaknesses.
#     """
