import requests
import json


def get_embedding(text):
    url = "http://localhost:11434/api/embeddings"
    payload = {
        "model": "bge-m3",
        "prompt": text,
    }
    response = requests.post(url, json=payload)
    try:
        return response.json()["embedding"]  # Extract only the embedding
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error getting embedding: {e}, Response: {response.text}")
        return None


# # **รับไฟล์ PDF ที่อ่านมาแล้วจาก parse_pdf**
# def embed_resume(file):
#     resume_text = parse_pdf.process_pdf(file)

#     if resume_text:
#         print(f"✅ Extracted Resume Text:\n{resume_text}\n")

#         # สร้าง Embedding
#         embedding = get_embedding(resume_text)
#         if embedding:
#             print(f"✅ Embedding generated successfully:\n{embedding}")
#             return embedding
#         else:
#             print("❌ Embedding generation failed.")
#             return None
#     else:
#         print("❌ Resume text extraction failed.")
#         return None
