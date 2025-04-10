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


db = MongoDB()


# Existing Resume Upload functionality
candidate_id = st.sidebar.text_input("Enter Candidate ID:", value="candidate_123")
mode = st.sidebar.radio("Select Mode:", ["Classify", "Maximize Performance"])

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload PDF", type="pdf")

submit_button = st.sidebar.button("Submit")

if uploaded_file is not None and submit_button:
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

        # Insert resume data into MongoDB
        db.insert_resume(resume_id, file_name, file_type)
        st.success("Resume has been successfully saved to MongoDB.")

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

            # Extract personal information
            extracted_info = processor.extract_resume_info(parsed_text)

            # ไม่ต้องแปลง JSON อีกครั้งเพราะ extract_resume_info ส่งคืนเป็น dict แล้ว
            personal_info = extracted_info  # extracted_info เป็น dict แล้ว

            # แสดงข้อมูลที่สกัดได้
            st.subheader("Extracted Information")
            st.json(personal_info)

            # บันทึกข้อมูลผู้สมัครลง MongoDB
            db.insert_candidate(candidate_id, personal_info, parsed_text, embedding)

            st.success("Candidate data has been successfully saved to MongoDB.")

            # Only run job matching based on selected mode
            if mode == "Maximize Performance":
                job_matching_results = job_description.analyze_resume(
                    parsed_text, optimize=True
                )

                # Sort results from highest to lowest
                sorted_results = sorted(
                    job_matching_results.items(),
                    key=lambda x: x[1][0],  # Use score for sorting
                    reverse=True,
                )

                st.subheader("Job Matching Results")
                for position, (score, analysis_stream) in sorted_results:
                    with st.expander(f"**{position}:** {score:.2f}%"):
                        analysis_box = st.empty()
                        full_text = ""

                        # Stream answers continuously
                        if analysis_stream:
                            for chunk in analysis_stream:
                                full_text += chunk
                                analysis_box.write(full_text)
        else:
            st.error(
                "The uploaded file is not classified as a Resume/CV. Please upload a valid resume."
            )


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


# candidate_data = {
#     "candidate_id": candidate_id,
#     "name": personal_info.get("name"),
#     "email": personal_info.get("email"),
#     "phone": personal_info.get("phone"),
#     "address": personal_info.get("address"),
#     "education": personal_info.get("education"),
#     "skills": personal_info.get("skills"),
#     "work_experience": personal_info.get("work_experience"),
#     "certifications": personal_info.get("certifications"),
#     "projects": personal_info.get("projects"),
#     "hobbies": personal_info.get("hobbies"),
#     "references": personal_info.get("references"),
#     "position": personal_info.get("position"),
#     "languages": personal_info.get("languages"),
#     "parsed_text": parsed_text,
#     "embedding": embedding,
# }
# # Insert data into MongoDB
# db.insert_candidate(candidate_data)
