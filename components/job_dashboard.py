import streamlit as st
from database import MongoDB

# import pandas as pd
# import uuid
# from datetime import datetime
# from modules.parse_pdf import ResumeProcessor
# from modules.classify_text import classify_text
# import job_description
# from typing import Optional

db = MongoDB()


st.header("Job Descriptions")

# Fetch job descriptions
job_descriptions = list(db.job_descriptions.find())

if job_descriptions:
    for job in job_descriptions:
        with st.expander(f"{job.get('position', 'Untitled Position')}"):
            st.write("**Requirements:**")
            st.write(job.get("requirements", "No requirements listed"))
            st.write(f"**Created At:** {job.get('created_at', 'N/A')}")
else:
    st.write("No job descriptions found.")

# CSV file uploader (moved from sidebar to be consistent with page structure)
