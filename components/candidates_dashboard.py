import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from database import MongoDB

# Initialize the database connection
db = MongoDB()


# Custom CSS for better styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2563EB;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .metric-label {
        font-size: 1rem;
        color: #4B5563;
    }
    .profile-card {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #2563EB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    .candidate-name {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1E3A8A;
    }
    .candidate-position {
        font-size: 1rem;
        color: #4B5563;
        font-style: italic;
    }
    .tag {
        background-color: #E5E7EB;
        border-radius: 1rem;
        padding: 0.25rem 0.75rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        display: inline-block;
        font-size: 0.875rem;
    }
    .tag-skill {
        background-color: #DBEAFE;
        color: #1E40AF;
    }
    .tag-language {
        background-color: #E0F2FE;
        color: #0369A1;
    }
    .tag-certification {
        background-color: #ECFDF5;
        color: #065F46;
    }
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #4B5563;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .info-label {
        font-weight: 600;
        color: #4B5563;
    }
    .search-container {
        background-color: #F9FAFB;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
    }
    .filter-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .match-indicator {
        height: 10px;
        border-radius: 5px;
        margin-bottom: 0.25rem;
    }
    .match-text {
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Header with logo
st.markdown(
    '<div class="main-header">👔 ReZoome - Candidates Dashboard</div>',
    unsafe_allow_html=True,
)

# Fetch candidates data
candidates_cursor = db.candidates_collection.find()
candidates_df = pd.DataFrame(list(candidates_cursor))

# Handle empty dataframe
if candidates_df.empty:
    st.info("No candidates found in the database.")
    st.stop()

# Ensure created_at column exists, create if missing
if "created_at" not in candidates_df.columns:
    candidates_df["created_at"] = datetime.now()

# Convert created_at to datetime, handling potential errors
try:
    candidates_df["created_at"] = pd.to_datetime(
        candidates_df["created_at"], errors="coerce"
    )
except Exception as e:
    st.warning(f"Error processing dates: {e}")
    candidates_df["created_at"] = datetime.now()

# Dashboard Overview Section
st.markdown(
    '<div class="section-header">Dashboard Overview</div>', unsafe_allow_html=True
)

# Summary Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{len(candidates_df)}</div>
            <div class="metric-label">Total Candidates</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    # Filter candidates applied this month
    try:
        candidates_this_month = len(
            candidates_df[candidates_df["created_at"].dt.month == datetime.now().month]
        )
    except Exception:
        candidates_this_month = 0

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{candidates_this_month}</div>
            <div class="metric-label">This Month</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    # Count unique positions
    try:
        unique_positions = candidates_df["position"].nunique()
    except:
        unique_positions = 0

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{unique_positions}</div>
            <div class="metric-label">Unique Positions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    # Fetch total job positions
    active_jobs = db.job_descriptions.count_documents({})

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{active_jobs}</div>
            <div class="metric-label">Active Job Posts</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Data visualization section
st.markdown(
    '<div class="section-header">Candidate Analytics</div>', unsafe_allow_html=True
)

# Create two columns for charts
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # Create a skills frequency chart if skills exist
    if "skills" in candidates_df.columns and not candidates_df["skills"].isna().all():
        try:
            # Extract skills and count frequencies
            all_skills = []
            for skills_list in candidates_df["skills"].dropna():
                if isinstance(skills_list, list):
                    all_skills.extend(skills_list)
                elif isinstance(skills_list, str):
                    all_skills.append(skills_list)

            if all_skills:
                skill_counts = pd.Series(all_skills).value_counts().head(10)
                fig = px.bar(
                    x=skill_counts.values,
                    y=skill_counts.index,
                    orientation="h",
                    title="Top 10 Skills Among Candidates",
                    labels={"x": "Count", "y": "Skill"},
                    color=skill_counts.values,
                    color_continuous_scale="blues",
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No skills data available for visualization")
        except Exception as e:
            st.error(f"Error creating skills chart: {e}")

with chart_col2:
    # Create a positions chart if position exists
    if (
        "position" in candidates_df.columns
        and not candidates_df["position"].isna().all()
    ):
        try:
            position_counts = candidates_df["position"].value_counts().head(10)
            fig = px.pie(
                values=position_counts.values,
                names=position_counts.index,
                title="Candidates by Position",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Blues_r,
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating positions chart: {e}")

# Search and Filter Section
st.markdown(
    '<div class="section-header">Candidate Search</div>', unsafe_allow_html=True
)

with st.container():
    st.markdown('<div class="search-container">', unsafe_allow_html=True)

    # Create two columns for search and filtering
    search_col, filter_col = st.columns([2, 1])

    with search_col:
        search_term = st.text_input(
            "Search Candidates",
            placeholder="Search by name, email, skills, or position",
        )

    with filter_col:
        # Add position filter if positions exist
        positions = []
        if "position" in candidates_df.columns:
            positions = candidates_df["position"].dropna().unique().tolist()

        selected_position = st.selectbox(
            "Filter by Position", options=["All Positions"] + positions, index=0
        )

    st.markdown("</div>", unsafe_allow_html=True)

# Filter candidates based on search term and position
filtered_candidates = candidates_df.copy()

if search_term:
    filtered_candidates = filtered_candidates[
        filtered_candidates.apply(
            lambda row: any(
                search_term.lower() in str(value).lower()
                for value in [
                    row.get("name", ""),
                    row.get("email", ""),
                    row.get("position", ""),
                    row.get("skills", []),
                ]
                if value is not None
            ),
            axis=1,
        )
    ]

if selected_position != "All Positions":
    filtered_candidates = filtered_candidates[
        filtered_candidates["position"] == selected_position
    ]

# Display filtered candidates
if len(filtered_candidates) == 0:
    st.info("No candidates found matching the search criteria.")
else:
    st.markdown(
        f"<div style='margin-bottom:1rem;'>Showing {len(filtered_candidates)} candidates</div>",
        unsafe_allow_html=True,
    )

# Candidate Profiles Section
st.markdown(
    '<div class="section-header">Candidate Profiles</div>', unsafe_allow_html=True
)

for index, candidate in filtered_candidates.iterrows():
    try:
        with st.expander(
            f"{candidate.get('name', 'Unnamed Candidate')} - {candidate.get('position', 'No Position')}"
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                # Basic information
                st.markdown(
                    f"<div class='candidate-name'>{candidate.get('name', 'Unnamed Candidate')}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div class='candidate-position'>{candidate.get('position', 'No Position')}</div>",
                    unsafe_allow_html=True,
                )

                # Contact information
                st.markdown(
                    "<div class='section-title'>Contact Information</div>",
                    unsafe_allow_html=True,
                )
                contact_col1, contact_col2 = st.columns(2)

                with contact_col1:
                    st.markdown(
                        f"<span class='info-label'>Email:</span> {candidate.get('email', 'N/A')}",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<span class='info-label'>Phone:</span> {candidate.get('phone', 'N/A')}",
                        unsafe_allow_html=True,
                    )

                with contact_col2:
                    st.markdown(
                        f"<span class='info-label'>Address:</span> {candidate.get('address', 'N/A')}",
                        unsafe_allow_html=True,
                    )

                # Education
                st.markdown(
                    "<div class='section-title'>Education</div>", unsafe_allow_html=True
                )
                education = candidate.get("education", [])
                if education:
                    if isinstance(education, list):
                        for edu in education:
                            st.markdown(f"- {edu}")
                    else:
                        st.markdown(f"- {education}")
                else:
                    st.markdown("No education information available")

                # Work Experience
                st.markdown(
                    "<div class='section-title'>Work Experience</div>",
                    unsafe_allow_html=True,
                )
                work_exp = candidate.get("work_experience", [])
                if work_exp:
                    if isinstance(work_exp, list):
                        for exp in work_exp:
                            st.markdown(f"- {exp}")
                    else:
                        st.markdown(f"- {work_exp}")
                else:
                    st.markdown("No work experience listed")

                # Projects
                projects = candidate.get("projects", [])
                if projects:
                    st.markdown(
                        "<div class='section-title'>Projects</div>",
                        unsafe_allow_html=True,
                    )
                    if isinstance(projects, list):
                        for project in projects:
                            st.markdown(f"- {project}")
                    else:
                        st.markdown(f"- {projects}")

            with col2:
                # Match score (placeholder, would be calculated from your matching system)
                match_score = candidate.get("match", 75)  # Default placeholder

                # Determine color based on score
                if match_score >= 80:
                    color = "#10B981"  # Green
                elif match_score >= 60:
                    color = "#F59E0B"  # Yellow
                else:
                    color = "#EF4444"  # Red

                st.markdown(
                    f"""
                <div style="background-color: #F9FAFB; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">Match Score</div>
                    <div class="match-indicator" style="background-color: {color}; width: {match_score}%;"></div>
                    <div class="match-text" style="color: {color};">{match_score}%</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Skills section
                st.markdown(
                    "<div class='section-title'>Skills</div>", unsafe_allow_html=True
                )

                # ดึงข้อมูล Skills จาก Candidate
                skills = candidate.get("skills", {})

                if skills:
                    technical_skills = skills.get("technical", [])
                    soft_skills = skills.get("soft", [])

                    tags_html = ""

                    # แสดง Technical Skills
                    if technical_skills:
                        tags_html += "<div><strong>Technical Skills:</strong></div>"
                        for skill in technical_skills:
                            tags_html += f'<span class="tag tag-skill">{skill}</span> '

                    # แสดง Soft Skills
                    if soft_skills:
                        tags_html += "<div><strong>Soft Skills:</strong></div>"
                        for skill in soft_skills:
                            tags_html += f'<span class="tag tag-skill">{skill}</span> '

                    # แสดงผลลัพธ์ด้วย HTML ที่กำหนดไว้
                    st.markdown(tags_html, unsafe_allow_html=True)

                else:
                    st.markdown("No skills listed")

                # Languages section
                languages = candidate.get("languages", [])
                if languages:
                    st.markdown(
                        "<div class='section-title'>Languages</div>",
                        unsafe_allow_html=True,
                    )
                    tags_html = ""
                    if isinstance(languages, list):
                        for language in languages:
                            tags_html += (
                                f'<span class="tag tag-language">{language}</span>'
                            )
                    else:
                        tags_html += (
                            f'<span class="tag tag-language">{languages}</span>'
                        )
                    st.markdown(tags_html, unsafe_allow_html=True)

                # Certifications section
                certifications = candidate.get("certifications", [])
                if certifications:
                    st.markdown(
                        "<div class='section-title'>Certifications</div>",
                        unsafe_allow_html=True,
                    )
                    tags_html = ""
                    if isinstance(certifications, list):
                        for cert in certifications:
                            tags_html += (
                                f'<span class="tag tag-certification">{cert}</span>'
                            )
                    else:
                        tags_html += f'<span class="tag tag-certification">{certifications}</span>'
                    st.markdown(tags_html, unsafe_allow_html=True)

                # Hobbies section
                hobbies = candidate.get("hobbies", [])
                if hobbies:
                    st.markdown(
                        "<div class='section-title'>Hobbies & Interests</div>",
                        unsafe_allow_html=True,
                    )
                    if isinstance(hobbies, list):
                        for hobby in hobbies:
                            st.markdown(f"- {hobby}")
                    else:
                        st.markdown(f"- {hobbies}")

    except Exception as e:
        st.error(f"Error displaying candidate {candidate.get('name', 'Unknown')}: {e}")

# Add a footer
st.markdown(
    """
<div style="text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #E5E7EB; color: #6B7280; font-size: 0.875rem;">
    © 2025 ReZoome - AI-Powered Resume Analysis System
</div>
""",
    unsafe_allow_html=True,
)


# import streamlit as st
# import pandas as pd
# from datetime import datetime
# from database import MongoDB

# db = MongoDB()

# st.header("Candidates Dashboard")

# # Fetch candidates data
# candidates_cursor = db.candidates_collection.find()
# candidates_df = pd.DataFrame(list(candidates_cursor))

# # Ensure created_at column exists, create if missing
# if "created_at" not in candidates_df.columns:
#     candidates_df["created_at"] = datetime.now()

# # Convert created_at to datetime, handling potential errors
# try:
#     candidates_df["created_at"] = pd.to_datetime(
#         candidates_df["created_at"], errors="coerce"
#     )
# except Exception as e:
#     st.warning(f"Error processing dates: {e}")
#     candidates_df["created_at"] = datetime.now()

# # Summary Cards
# col1, col2, col3 = st.columns(3)

# with col1:
#     st.metric("Total Candidates", len(candidates_df))

# with col2:
#     # Filter candidates applied this month
#     try:
#         candidates_this_month = len(
#             candidates_df[candidates_df["created_at"].dt.month == datetime.now().month]
#         )
#     except Exception:
#         candidates_this_month = 0
#     st.metric("Candidates This Month", candidates_this_month)

# with col3:
#     # Fetch total job positions
#     st.metric("Active Job Positions", db.job_descriptions.count_documents({}))

# # Candidate List
# st.subheader("Candidate Profiles")

# # Search and filter
# search_term = st.text_input(
#     "Search Candidates", placeholder="Search by name, email, or skills"
# )

# # Filter candidates based on search term
# if search_term:
#     filtered_candidates = candidates_df[
#         candidates_df.apply(
#             lambda row: search_term.lower() in str(row.get("name", "")).lower()
#             or search_term.lower() in str(row.get("email", "")).lower()
#             or any(
#                 search_term.lower() in str(skill).lower()
#                 for skill in row.get("skills", [])
#             ),
#             axis=1,
#         )
#     ]
# else:
#     filtered_candidates = candidates_df

# # Display filtered candidates
# if len(filtered_candidates) == 0:
#     st.info("No candidates found matching the search criteria.")

# for index, candidate in filtered_candidates.iterrows():
#     try:
#         with st.expander(
#             f"{candidate.get('name', 'Unnamed Candidate')} - {candidate.get('email', 'No Email')} - Match: {candidate.get('match', 'N/A')}%"
#         ):
#             col1, col2 = st.columns(2)

#             with col1:
#                 st.write(f"**Phone:** {candidate.get('phone', 'N/A')}")
#                 st.write(f"**Email:** {candidate.get('email', 'N/A')}")

#             with col2:
#                 st.write("**Skills:**")
#                 skills = candidate.get("skills", [])
#                 if skills:
#                     skills_str = ", ".join(map(str, skills))
#                     st.write(skills_str)
#                 else:
#                     st.write("No skills listed")

#             st.write("**Work Experience:**")
#             work_exp = candidate.get("work_experience", [])
#             if work_exp:
#                 for exp in work_exp:
#                     st.write(f"- {exp}")
#             else:
#                 st.write("No work experience listed")

#             # AI Insights placeholder
#             st.write("**AI Insights:**")
#             st.markdown(
#                 """
#             <div style="background-color: #f0f0f0; border-radius: 5px; padding: 10px; display: inline-block;">
#                 <strong>Match:</strong> 75%
#             </div>
#             """,
#                 unsafe_allow_html=True,
#             )

#     except Exception as e:
#         st.error(f"Error displaying candidate {candidate.get('name', 'Unknown')}: {e}")
