import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from database import MongoDB
from modules.parse_pdf import ResumeProcessor
from modules.classify_text import classify_text
import modules.job_description as job_description
from modules.embed import get_embedding
from typing import Optional
import json
import nest_asyncio

nest_asyncio.apply()

db = MongoDB()


# Existing Resume Upload functionality
default_id = f"candidate_{uuid.uuid4().hex[:8]}"
#candidate_id = st.sidebar.text_input("Enter Candidate ID:", value=default_id)
candidate_id = default_id
st.sidebar.subheader("Candidate ID")
st.sidebar.text(default_id)
mode = st.sidebar.radio("Select Mode:", ["Classify", "Maximize Performance"])

# File uploader
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

submit_button = st.button("Submit")

async def process_resume(uploaded_file, candidate_id, mode):
    # Process PDF
    processor = ResumeProcessor()
    parsed_text, embedding = processor.process_pdf(uploaded_file)

    if parsed_text is None or embedding is None:
        st.error("Failed to process the PDF. Please try again.")
    else:
        st.subheader("Parsed Text")
        st.text_area("Parsed Text", parsed_text, height=300)

        # Save resume into MongoDB
        resume_id = f"resume-{str(uuid.uuid4())}"
        file_name = uploaded_file.name
        file_type = uploaded_file.type


        # Classification always runs
        classification = classify_text(parsed_text)

        st.subheader("Classification Result")
        st.write(classification)

        keywords = [
            "Resume",
            "CV",
            "Job Description",
            "Job Application",
            "Interview",
            "Offer",
        ]
        if any(keyword in classification for keyword in keywords):
            st.success("The uploaded file is classified as a Resume/CV.")
            # Insert resume data into MongoDB
            

            # Only run job matching based on selected mode
            if mode == "Maximize Performance":
                db.insert_resume(resume_id, file_name, file_type)
                st.success("Resume has been successfully saved to MongoDB.")
                # Extract personal information
                # max_length = 10000  # Adjust this value based on the function's requirements
                # truncated_text = parsed_text[:max_length] if len(parsed_text) > max_length else parsed_text
                personal_info = processor.extract_resume_info(parsed_text)

                # ไม่ต้องแปลง JSON อีกครั้งเพราะ extract_resume_info ส่งคืนเป็น dict แล้ว
                # personal_info = extracted_info  # extracted_info เป็น dict แล้ว

                # แสดงข้อมูลที่สกัดได้
                st.subheader("Extracted Information")
                print(personal_info)
                st.json(personal_info)

                # บันทึกข้อมูลผู้สมัครลง MongoDB
                db.insert_candidate(
                    candidate_id=candidate_id,
                    personal_info=personal_info,
                    parsed_text=parsed_text,
                    embedding=embedding
                )

                st.success("Candidate data has been successfully saved to MongoDB.")
                
                job_matching_results = job_description.analyze_resume(
                    parsed_text, candidate_id, optimize=True
                )

                # ✅ ปรับการ sort ให้ robust
                sorted_results = sorted(
                    job_matching_results.items(),
                    key=lambda x: x[1]["score"],  # ← ใช้ค่า score จริงๆ
                    reverse=True,
                )

                st.subheader("Job Matching Results")
                for position, result in sorted_results:
                    score = result["score"]
                    summary = result.get("summary", "")

                    with st.expander(f"**{position}:** {score:.2f}%"):
                        st.write(summary)

        else:
            st.error(
                "The uploaded file is not classified as a Resume/CV. Please upload a valid resume."
            )


if uploaded_file is not None and submit_button:
    import asyncio
    asyncio.run(process_resume(uploaded_file, candidate_id, mode))

st.sidebar.subheader("Job Matching Results")
uploaded_file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)  # Read CSV into a DataFrame

    # Validate CSV format
    required_columns = {"position", "requirements"}
    if not required_columns.issubset(df.columns):
        st.sidebar.error(
            f"CSV file must contain the following columns: {required_columns}"
        )
    else:
        if st.sidebar.button("Insert CSV Data"):
            inserted_count = 0
            with st.spinner("Processing CSV data..."):
                for _, row in df.iterrows():
                    job_id = f"job-{str(uuid.uuid4())}"
                    position = row["position"]
                    requirements = row["requirements"]
                    embedding = get_embedding(requirements)

                    # Save to MongoDB
                    job_descriptions = {
                        "job_id": job_id,
                        "position": position,
                        "requirements": requirements,
                        "embedding": embedding,
                    }
                    db.insert_job_description(**job_descriptions)
                    inserted_count += 1

            st.sidebar.success(
                f"Successfully inserted {inserted_count} job descriptions!"
            )

