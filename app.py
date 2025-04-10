import streamlit as st
from database import MongoDB

# from modules.parse_pdf import ResumeProcessor
# from modules.classify_text import classify_text
# import modules.job_description as job_description
# from modules.embed import get_embedding
# import pandas as pd
# from datetime import datetime

# Initialize MongoDB connection
db = MongoDB()

# Streamlit interface
st.set_page_config(
    layout="wide", page_title="ReZoome - Candidates Dashboard", page_icon="👔"
)
# st.title("Rezoome📄")

# Sidebar navigation
pages = {
    "Your account": [
        st.Page("components/candidates_dashboard.py", title="Candidates Dashboard"),
        st.Page("components/resume_upload.py", title="Resume Upload"),
        st.Page("components/job_dashboard.py", title="Job Descriptions"),
    ],
}

pg = st.navigation(pages)
pg.run()


# pages = st.sidebar.radio(
#     "Navigate", ["Resume Upload", "Candidates Dashboard", "Job Descriptions"]
# )

# if pages == "Resume Upload":
#     # Existing Resume Upload functionality
#     candidate_id = st.sidebar.text_input("Enter Candidate ID:", value="candidate_123")
#     mode = st.sidebar.radio("Select Mode:", ["Classify", "Maximize Performance"])

#     # File uploader
#     uploaded_file = st.sidebar.file_uploader("Upload PDF", type="pdf")

#     submit_button = st.sidebar.button("Submit")

#     if uploaded_file is not None and submit_button:
#         # Process PDF
#         processor = ResumeProcessor()
#         parsed_text, embedding = processor.process_pdf(uploaded_file)

#         if parsed_text is None or embedding is None:
#             st.error("Failed to process the PDF. Please try again.")
#         else:
#             st.subheader("Parsed Text")
#             st.text_area("Parsed Text", parsed_text, height=300)

#             # Save resume into MongoDB
#             resume_id = f"resume-{str(uuid.uuid4())}"
#             file_name = uploaded_file.name
#             file_type = uploaded_file.type

#             # Extract skills to save in MongoDB (assuming extracted skills are part of parsed text)
#             skills = processor.extract_skills(parsed_text)

#             # Insert resume data into MongoDB
#             db.insert_resume(resume_id, file_name, file_type)
#             st.success("Resume has been successfully saved to MongoDB.")

#             # Classification always runs
#             classification = classify_text(parsed_text)

#             st.subheader("Classification Result")
#             st.write(classification)

#             if classification != "Resume/CV":
#                 st.error(
#                     "The uploaded file is not classified as a Resume/CV. Please upload a valid resume."
#                 )
#             else:
#                 st.success("The uploaded file is classified as a Resume/CV.")

#                 # Extract personal information
#                 personal_info = processor.extract_personal_info(parsed_text)

#                 # Extract education
#                 education = processor.extract_education(parsed_text)

#                 # Extract skills
#                 skills = processor.extract_skills(parsed_text)

#                 # Extract work experience
#                 work_experience = processor.extract_work_experience(parsed_text)

#                 # Prepare data to insert into MongoDB
#                 candidate_data = {
#                     "candidate_id": candidate_id,
#                     "name": personal_info.get("name"),
#                     "email": personal_info.get("email"),
#                     "phone": personal_info.get("phone"),
#                     "address": personal_info.get("address"),
#                     "education": education,
#                     "skills": skills,
#                     "work_experience": work_experience,
#                     "parsed_text": parsed_text,
#                     "embedding": embedding,
#                 }

#                 # Insert data into MongoDB
#                 db.insert_candidate(candidate_data)

#                 st.success("Candidate data has been successfully saved to MongoDB.")

#                 # Only run job matching based on selected mode
#                 if mode == "Maximize Performance":
#                     job_matching_results = job_description.analyze_resume(
#                         parsed_text, optimize=True
#                     )

#                     # Sort results from highest to lowest
#                     sorted_results = sorted(
#                         job_matching_results.items(),
#                         key=lambda x: x[1][0],  # Use score for sorting
#                         reverse=True,
#                     )

#                     st.subheader("Job Matching Results")
#                     for position, (score, analysis_stream) in sorted_results:
#                         with st.expander(f"**{position}:** {score:.2f}%"):
#                             analysis_box = st.empty()
#                             full_text = ""

#                             # Stream answers continuously
#                             if analysis_stream:
#                                 for chunk in analysis_stream:
#                                     full_text += chunk
#                                     analysis_box.write(full_text)

# elif pages == "Candidates Dashboard":
#     st.header("Candidates Dashboard")

#     # Fetch candidates data
#     candidates_cursor = db.candidates_collection.find()
#     candidates_df = pd.DataFrame(list(candidates_cursor))

#     # Ensure created_at column exists, create if missing
#     if "created_at" not in candidates_df.columns:
#         candidates_df["created_at"] = datetime.now()

#     # Convert created_at to datetime, handling potential errors
#     try:
#         candidates_df["created_at"] = pd.to_datetime(
#             candidates_df["created_at"], errors="coerce"
#         )
#     except Exception as e:
#         st.warning(f"Error processing dates: {e}")
#         candidates_df["created_at"] = datetime.now()

#     # Summary Cards
#     col1, col2, col3 = st.columns(3)

#     with col1:
#         st.metric("Total Candidates", len(candidates_df))

#     with col2:
#         # Filter candidates applied this month
#         try:
#             candidates_this_month = len(
#                 candidates_df[
#                     candidates_df["created_at"].dt.month == datetime.now().month
#                 ]
#             )
#         except Exception:
#             candidates_this_month = 0
#         st.metric("Candidates This Month", candidates_this_month)

#     with col3:
#         # Fetch total job positions
#         st.metric("Active Job Positions", db.job_descriptions.count_documents({}))

#     # Candidate List
#     st.subheader("Candidate Profiles")

#     # Search and filter
#     search_term = st.text_input(
#         "Search Candidates", placeholder="Search by name, email, or skills"
#     )

#     # Filter candidates based on search term
#     if search_term:
#         filtered_candidates = candidates_df[
#             candidates_df.apply(
#                 lambda row: search_term.lower() in str(row.get("name", "")).lower()
#                 or search_term.lower() in str(row.get("email", "")).lower()
#                 or any(
#                     search_term.lower() in str(skill).lower()
#                     for skill in row.get("skills", [])
#                 ),
#                 axis=1,
#             )
#         ]
#     else:
#         filtered_candidates = candidates_df

#     # Display filtered candidates
#     if len(filtered_candidates) == 0:
#         st.info("No candidates found matching the search criteria.")

#     for index, candidate in filtered_candidates.iterrows():
#         try:
#             with st.expander(
#                 f"{candidate.get('name', 'Unnamed Candidate')} - {candidate.get('email', 'No Email')} - Match: {candidate.get('match', 'N/A')}%"
#             ):
#                 col1, col2 = st.columns(2)

#                 with col1:
#                     st.write(f"**Phone:** {candidate.get('phone', 'N/A')}")
#                     st.write(f"**Email:** {candidate.get('email', 'N/A')}")

#                 with col2:
#                     st.write("**Skills:**")
#                     skills = candidate.get("skills", [])
#                     if skills:
#                         skills_str = ", ".join(map(str, skills))
#                         st.write(skills_str)
#                     else:
#                         st.write("No skills listed")

#                 st.write("**Work Experience:**")
#                 work_exp = candidate.get("work_experience", [])
#                 if work_exp:
#                     for exp in work_exp:
#                         st.write(f"- {exp}")
#                 else:
#                     st.write("No work experience listed")

#                 # AI Insights placeholder
#                 st.write("**AI Insights:**")
#                 st.markdown(
#                     """
#                 <div style="background-color: #f0f0f0; border-radius: 5px; padding: 10px; display: inline-block;">
#                     <strong>Match:</strong> 75%
#                 </div>
#                 """,
#                     unsafe_allow_html=True,
#                 )

#         except Exception as e:
#             st.error(
#                 f"Error displaying candidate {candidate.get('name', 'Unknown')}: {e}"
#             )

# elif pages == "Job Descriptions":
#     st.header("Job Descriptions")

#     # Fetch job descriptions
#     job_descriptions = list(db.job_descriptions.find())

#     if job_descriptions:
#         for job in job_descriptions:
#             with st.expander(f"{job.get('position', 'Untitled Position')}"):
#                 st.write("**Requirements:**")
#                 st.write(job.get("requirements", "No requirements listed"))
#                 st.write(f"**Created At:** {job.get('created_at', 'N/A')}")
#     else:
#         st.write("No job descriptions found.")

# # CSV file uploader (moved from sidebar to be consistent with page structure)
# if pages == "Resume Upload":
#     uploaded_file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])

#     if uploaded_file:
#         df = pd.read_csv(uploaded_file)  # Read CSV into a DataFrame

#         # Validate CSV format
#         required_columns = {"position", "requirements"}
#         if not required_columns.issubset(df.columns):
#             st.sidebar.error(
#                 f"CSV file must contain the following columns: {required_columns}"
#             )
#         else:
#             if st.sidebar.button("Insert CSV Data"):
#                 inserted_count = 0
#                 with st.spinner("Processing CSV data..."):
#                     for _, row in df.iterrows():
#                         job_id = f"job-{str(uuid.uuid4())}"
#                         position = row["position"]
#                         requirements = row["requirements"]
#                         embedding = get_embedding(requirements)

#                         # Save to MongoDB
#                         job_descriptions = {
#                             "job_id": job_id,
#                             "position": position,
#                             "requirements": requirements,
#                             "embedding": embedding,
#                         }
#                         db.insert_job_description(**job_descriptions)
#                         inserted_count += 1

#                 st.sidebar.success(
#                     f"Successfully inserted {inserted_count} job descriptions!"
#                 )


# # Add custom badge method
# def st_badge(label, value):
#     st.markdown(
#         f'<span style="background-color: #e0e0e0; padding: 4px 8px; border-radius: 12px; margin-right: 5px;">{label}: {value}</span>',
#         unsafe_allow_html=True,
#     )


# # Monkey patch Streamlit to add badge method
# st.badge = st_badge
