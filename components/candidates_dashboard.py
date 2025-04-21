import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from database import MongoDB
import bson
import json
from modules.email_sender import send_email, get_email_settings
from dotenv import load_dotenv
import os
from modules.email_fetcher import fetch_email_content

# Initialize the database connection
db = MongoDB()


# Custom CSS for better styling
st.markdown(
    """
<style>
    body {
        background-color: #F9FAFB;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E40AF;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2563EB;
        border-bottom: 2px solid #DBEAFE;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }

    .profile-card {
        background-color: white;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #3B82F6;
    }

    .candidate-name {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1E3A8A;
        margin-bottom: 0.25rem;
    }

    .candidate-position {
        font-size: 1rem;
        color: #6B7280;
        font-style: italic;
        margin-bottom: 1rem;
    }

    .contact-info {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .info-row {
        display: flex;
        align-items: center;
    }

    .info-label {
        font-weight: 600;
        color: #374151;
        min-width: 80px;
    }

    .info-value {
        color: #374151;
    }

    .email-button {
        background-color: #3B82F6;
        color: white;
        border: none;
        padding: 4px 12px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.875rem;
        margin-left: 10px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .metric-card {
        background-color: #FFFFFF;
        border-radius: 0.75rem;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.12);
        border-left: 4px solid #60A5FA;
    }

    .metric-card strong {
        color: #1D4ED8;
    }

    .tag {
        background-color: #E5E7EB;
        border-radius: 999px;
        padding: 0.4rem 0.9rem;
        margin: 0.25rem;
        display: inline-block;
        font-size: 0.875rem;
        color: #374151;
        transition: background-color 0.2s ease;
    }

    .tag:hover {
        background-color: #D1D5DB;
    }

    .tag-skill {
        background-color: #DBEAFE;
        color: #1E3A8A;
    }

    .tag-language {
        background-color: #CFFAFE;
        color: #0E7490;
    }

    .tag-certification {
        background-color: #DCFCE7;
        color: #15803D;
    }

    .edu-entry, .work-entry, .cert-entry, .proj-entry {
        margin-bottom: 1.25rem;
    }

    .edu-entry div, .work-entry div, .cert-entry div, .proj-entry div {
        margin-top: 0.25rem;
    }

    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #4B5563;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }

    .search-filter-container {
    background-color: #F3F4F6;
    padding: 1.5rem;
    border-radius: 0.75rem;
    margin-bottom: 2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    .stRadio > div {
        flex-direction: row;
        gap: 2rem;
    }

    .stRadio label {
        background-color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        border: 1px solid #E5E7EB;
        font-weight: 500;
    }

    .candidate-card {
        background-color: white;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 4px solid #3B82F6;
    }

    .match-indicator {
        background-color: #F3F4F6;
        border-radius: 9999px;
        height: 8px;
        margin-bottom: 4px;
        width: 100%;
    }

    .match-fill {
        height: 8px;
        border-radius: 9999px;
    }

    .match-text-high {
        color: #10B981;
        font-weight: 600;
        text-align: right;
        font-size: 0.9rem;
    }

    .match-text-medium {
        color: #F59E0B;
        font-weight: 600;
        text-align: right;
        font-size: 0.9rem;
    }

    .match-text-low {
        color: #EF4444;
        font-weight: 600;
        text-align: right;
        font-size: 0.9rem;
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

# Get matching scores for all candidates
candidate_matching_data = []
matched_positions_count = {}

# Collect matching data
for index, candidate in candidates_df.iterrows():
    candidate_id = candidate.get("candidate_id")
    candidate_name = candidate.get("name", "Unnamed Candidate")
    
    matching_data = db.matching_results_collection.find_one({"candidate_id": candidate_id})
    
    if matching_data and "matching_scores" in matching_data:
        matching_scores = matching_data["matching_scores"]
        
        # Find top matching position and score
        if matching_scores:
            top_position = max(matching_scores, key=matching_scores.get)
            top_score = matching_scores[top_position]
            
            candidate_matching_data.append({
                "name": candidate_name,
                "position": top_position,
                "score": top_score
            })
            
            # Count candidates per matched position
            if top_position in matched_positions_count:
                matched_positions_count[top_position] += 1
            else:
                matched_positions_count[top_position] = 1

# Create dataframes for visualization
if candidate_matching_data:
    matching_df = pd.DataFrame(candidate_matching_data)
    positions_df = pd.DataFrame({
        'position': list(matched_positions_count.keys()),
        'count': list(matched_positions_count.values())
    })
    
    # Sort dataframes
    matching_df = matching_df.sort_values('score', ascending=False).head(10)
    positions_df = positions_df.sort_values('count', ascending=False)

    with chart_col1:
        try:
            # Create bar chart of top candidates by matching score
            fig = px.bar(
                matching_df,
                x='score',
                y='name',
                orientation='h',
                title='Top Candidates by Matching Score',
                labels={'score': 'Matching Score (%)', 'name': 'Candidate Name'},
                color='score',
                color_continuous_scale='blues',
                text='score'
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating candidates by matching score chart: {e}")
            
    with chart_col2:
        try:
            # Create pie chart of candidates per matched position
            fig = px.pie(
                positions_df,
                values='count',
                names='position',
                title='Candidates by Matched Job Position',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig.update_traces(textinfo='value+percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating positions match chart: {e}")
else:
    with chart_col1:
        st.info("No matching data available for candidate visualization.")
    
    with chart_col2:
        # Fallback to position distribution if no matching data
        if "position" in candidates_df.columns and not candidates_df["position"].isna().all():
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

# Search input with full width
search_term = st.text_input(
    "Search Candidates",
    placeholder="Search by name, email, skills, or position",
    label_visibility="collapsed"
)

# Create columns for the filter options with better spacing
filter_col1, filter_col2 = st.columns([1, 2])

with filter_col1:
    filter_type = st.radio(
        "Filter by:",
        ["Candidate Position", "Best Matching Job"],
        horizontal=True
    )

with filter_col2:
    if filter_type == "Candidate Position":
        # Original filter for candidate's position
        positions = []
        if "position" in candidates_df.columns:
            positions = candidates_df["position"].dropna().unique().tolist()
        
        selected_position = st.selectbox(
            "Select Position", 
            options=["All Positions"] + positions, 
            index=0
        )
    else:
        # Filter for best matching jobs
        # Get all available jobs from job collection
        jobs_cursor = db.job_descriptions.find({}, {"title": 1})
        available_jobs = [job.get("title", "") for job in jobs_cursor if job.get("title")]
        
        # If no jobs in database, try to extract from matching results
        if not available_jobs:
            matching_cursor = db.matching_results_collection.find()
            for match_doc in matching_cursor:
                if "matching_scores" in match_doc:
                    available_jobs.extend(list(match_doc["matching_scores"].keys()))
            
            available_jobs = list(set([job for job in available_jobs if job]))
        
        selected_position = st.selectbox(
            "Select Best Match Job", 
            options=["All Jobs"] + available_jobs, 
            index=0
        )

st.markdown('</div>', unsafe_allow_html=True)

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

# Update filtering logic based on selected filter type
if filter_type == "Candidate Position" and selected_position != "All Positions":
    filtered_candidates = filtered_candidates[
        filtered_candidates["position"] == selected_position
    ]
elif filter_type == "Best Matching Job" and selected_position != "All Jobs":
    # Find candidates that match best with the selected job
    candidate_ids_matching_job = []
    
    for candidate_id in filtered_candidates["candidate_id"]:
        matching_data = db.matching_results_collection.find_one({"candidate_id": candidate_id})
        
        if matching_data and "matching_scores" in matching_data:
            matching_scores = matching_data["matching_scores"]
            
            # If the selected position is their best match or among their matches
            if selected_position in matching_scores:
                # Check if this is their top match
                top_position = max(matching_scores, key=matching_scores.get)
                if top_position == selected_position:
                    candidate_ids_matching_job.append(candidate_id)
    
    filtered_candidates = filtered_candidates[
        filtered_candidates["candidate_id"].isin(candidate_ids_matching_job)
    ]

# After filtering logic
if len(filtered_candidates) == 0:
    st.info("No candidates found matching the search criteria.")
else:
    # Show the count with styling
    st.markdown(
        f"""
        <div style="background-color: #EFF6FF; padding: 0.75rem 1rem; border-radius: 0.5rem; 
        margin-bottom: 1.5rem; border-left: 4px solid #3B82F6; display: flex; align-items: center;">
            <span style="font-size: 1.25rem; font-weight: 600; color: #1E40AF; margin-right: 0.5rem;">
                {len(filtered_candidates)}
            </span>
            <span style="color: #3B82F6; font-weight: 500;">
                candidate{'' if len(filtered_candidates) == 1 else 's'} found
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Candidate Profiles Section
st.markdown(
    '<div class="section-header">Candidate Profiles</div>', unsafe_allow_html=True
)

# Add session state for email form
if 'email_form_open' not in st.session_state:
    st.session_state.email_form_open = None
if 'email_subject' not in st.session_state:
    st.session_state.email_subject = ""
if 'email_body' not in st.session_state:
    st.session_state.email_body = ""
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'form_cancelled' not in st.session_state:
    st.session_state.form_cancelled = False

# Get email credentials from .env file
load_dotenv(override=True)  # Add override=True to ensure variables are loaded
email_credentials = {
    'email': os.getenv('EMAIL_USER'),
    'password': os.getenv('EMAIL_PASSWORD')
}

# Log email credentials (masked for security)
#st.write(f"Using email: {email_credentials['email']}")
#st.write("Email password: ********")  # Don't show the actual password

# Get email settings based on provider
try:
    settings = get_email_settings()
    email_credentials.update({
        'smtp_server': settings['smtp_server'],
        'smtp_port': settings['smtp_port']
    })
except Exception as e:
    st.error(f"Error loading email settings: {str(e)}")

# Helper functions for handling button clicks
def open_email_form(idx, name):
    st.session_state.email_form_open = idx
    st.session_state.email_subject = f"Regarding your application - {name}"
    st.session_state.email_body = f"Dear {name},\n\n"

def handle_send_email(recipient_email, subject, body, credentials, settings):
    st.session_state.form_submitted = True
    try:
        result = send_email(
            recipient_email=recipient_email,
            subject=subject,
            body=body,
            sender_email=credentials['email'],
            sender_password=credentials['password'],
            smtp_server=settings['smtp_server'],
            smtp_port=settings['smtp_port']
        )
        
        if result[0]:
            st.session_state.email_form_open = None
            st.success("Email sent successfully!")
            return True
        else:
            st.error(f"Failed to send email: {result[1]}")
            return False
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False

def cancel_email_form():
    st.session_state.form_cancelled = True
    st.session_state.email_form_open = None
    st.rerun()  # Force a rerun immediately

# For handling direct button clicks without form
def on_cancel_click():
    st.session_state.email_form_open = None
    st.session_state.form_cancelled = True
    st.rerun()  # Force a rerun to update the UI immediately

for index, candidate in filtered_candidates.iterrows():
    try:
        # ✅ สรุปข้อมูลการ์ดด้านนอก
        latest_edu = candidate.get("education", [{}])[0] if candidate.get("education") else {}
        latest_degree = latest_edu.get("degree", "")
        latest_school = latest_edu.get("institution", "")

        # Check email for mailto link
        candidate_email = candidate.get('email', '')
        candidate_name = candidate.get('name', 'Unnamed Candidate')

        # Get matching score data before displaying
        candidate_id = candidate.get("candidate_id")
        matching_data = db.matching_results_collection.find_one({"candidate_id": candidate_id})

        top_match = None
        if matching_data and "matching_scores" in matching_data:
            matching_scores = matching_data["matching_scores"]

            # Find the highest matching position and score
            top_position = max(matching_scores, key=matching_scores.get)
            top_score = matching_scores[top_position]

            top_match = {
                "position": top_position,
                "score": round(top_score, 2)
            }

        # Create candidate card using Streamlit native components for better rendering
        with st.container():
            # Create a basic container with some styling
            st.markdown(
                """
                <style>
                .candidate-card {
                    background-color: white;
                    border-radius: 8px;
                    padding: 16px 20px;
                    margin-bottom: 16px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    border-left: 4px solid #3B82F6;
                }
                .match-indicator {
                    background-color: #F3F4F6;
                    border-radius: 9999px;
                    height: 8px;
                    margin-bottom: 4px;
                    width: 100%;
                }
                .match-fill {
                    height: 8px;
                    border-radius: 9999px;
                }
                .match-text-high {
                    color: #10B981;
                    font-weight: 600;
                    text-align: right;
                    font-size: 0.9rem;
                }
                .match-text-medium {
                    color: #F59E0B;
                    font-weight: 600;
                    text-align: right;
                    font-size: 0.9rem;
                }
                .match-text-low {
                    color: #EF4444;
                    font-weight: 600;
                    text-align: right;
                    font-size: 0.9rem;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            
            # Use columns for layout
            col1, col2 = st.columns([7, 3])
            
            with col1:
                st.markdown(f"### {candidate_name}")
                st.markdown(f"*{candidate.get('position', 'No Position')}*")
                
            with col2:
                if top_match:
                    match_score = top_match["score"]
                    position = top_match["position"]
                    
                    # Determine color based on score
                    if match_score >= 80:
                        color_class = "match-text-high"
                        bar_color = "#10B981"
                    elif match_score >= 60:
                        color_class = "match-text-medium"
                        bar_color = "#F59E0B" 
                    else:
                        color_class = "match-text-low"
                        bar_color = "#EF4444"
                    
                    # Use simple HTML with styling
                    st.markdown(f"**Top Match:** {position}", unsafe_allow_html=True)
                    
                    # Create progress bar
                    st.markdown(
                        f"""
                        <div class="match-indicator">
                            <div class="match-fill" style="background-color: {bar_color}; width: {match_score}%;"></div>
                        </div>
                        <div class="{color_class}">{match_score}%</div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown("*No matching data*")
            
            # Add a horizontal line to separate cards
            st.markdown("---")
        
        # Email form modal (remains outside expander, triggered by button inside)
        if st.session_state.email_form_open == index:
            # Initialize form key for tracking cancel button
            form_key = f"email_form_{index}"
            if f"cancel_{form_key}" not in st.session_state:
                st.session_state[f"cancel_{form_key}"] = False
        
            with st.form(form_key, clear_on_submit=True):
                st.subheader(f"Send Email to {candidate_name}")
                st.text_input("To:", value=candidate_email, disabled=True)
                
                # Get current subject and body values
                current_subject = st.text_input(
                    "Subject:", 
                    value=st.session_state.email_subject,
                    key=f"subject_{index}"
                )
                current_body = st.text_area(
                    "Message:", 
                    value=st.session_state.email_body, 
                    height=200,
                    key=f"body_{index}"
                )
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    submitted = st.form_submit_button("Send")
                    if submitted:
                        handle_send_email(
                            recipient_email=candidate_email,
                            subject=current_subject,
                            body=current_body,
                            credentials=email_credentials,
                            settings=settings
                        )
                with col2:
                    # Put the Cancel button inside the form but make it more responsive
                    cancelled = st.form_submit_button("Cancel")
                    if cancelled:
                        st.session_state[f"cancel_{form_key}"] = True
                        st.session_state.email_form_open = None
                        st.rerun()  # Force the UI to update immediately
            
            # Remove the cancel button outside the form
            # if st.button("Cancel", key=f"cancel_outside_form_{index}", on_click=on_cancel_click):
            #    pass  # Action handled by on_click

        # ✅ Expander ด้านล่าง: เปิดดูรายละเอียด
        with st.expander("View Full Details"):
            # Keep the detailed info in the expander
            # Remove duplicate header info that's now shown outside
            # st.markdown(f"### {candidate_name}")
            # st.markdown(f"*{candidate.get('position', 'No Position')}*")
            # st.markdown("---")

            # Show contact info and email button
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Email:**")
                st.write(candidate.get('email', 'N/A'))
                if candidate_email and candidate_email != 'N/A':
                    if st.button("✉️ Send Email", key=f"exp_email_btn_{index}", on_click=open_email_form, args=(index, candidate_name)): # Use on_click handler
                        pass # The action is now handled by the on_click function
            with col2:
                st.markdown("**Phone:**")
                st.write(candidate.get('phone', 'N/A'))
            with col3:
                st.markdown("**Education:**")
                st.write(f"{latest_degree} @ {latest_school}")

            st.markdown("---") # Add a separator

            col1_exp, col2_exp = st.columns([2, 1])

            with col1_exp: # Changed variable name to avoid conflict
                # Keep detailed sections like Education, Work Experience, Projects
                st.markdown("<div class='section-header'>Education</div>", unsafe_allow_html=True)
                education = candidate.get("education", [])
                if education:
                    for edu in education:
                        if isinstance(edu, dict):
                            degree = edu.get("degree", "")
                            institution = edu.get("institution", "")
                            department = edu.get("department", "")
                            year = edu.get("year", "")
                            gpa = edu.get("gpa", "")

                            gpa_text = f"<div class='edu-gpa'><strong>GPA:</strong> {gpa}</div>" if gpa else ""

                            edu_html = f"""
                                <div class='edu-entry' style='margin-bottom:20px;'>
                                    <div class='edu-degree'><strong>{degree}</strong></div>
                                    <div class='edu-department'>{department}</div>
                                    <div class='edu-institution'>{institution}</div>
                                    <div class='edu-years'>{year}</div>
                                    {gpa_text}
                                </div>
                            """
                            st.markdown(edu_html, unsafe_allow_html=True)
                else:
                    st.markdown("No education information available.")

                # Work Experience Section
                st.markdown("<div class='section-header'>Work Experience</div>", unsafe_allow_html=True)
                work_exp = candidate.get("work_experience", [])
                if isinstance(work_exp, list) and work_exp:
                    for exp in work_exp:
                        if isinstance(exp, dict):
                            position = exp.get("position", "")
                            company = exp.get("company", "")
                            year = exp.get("year", "")
                            responsibilities = exp.get("responsibilities", "")

                            st.markdown(f"""
                                <div class='metric-card work-entry'>
                                    <div><strong>{position or 'Position not specified'}</strong> @ {company or 'Unknown Company'}</div>
                                    <div>{year or 'Year not specified'}</div>
                                    <div>{responsibilities or ''}</div>
                                </div>
                            """, unsafe_allow_html=True)
                else:
                    st.markdown("No work experience listed.")


                # Projects Section
                projects = candidate.get("projects", [])
                if isinstance(projects, list) and projects:
                    st.markdown("<div class='section-header'>Projects</div>", unsafe_allow_html=True)
                    for proj in projects:
                        if isinstance(proj, dict):
                            name = proj.get("name", "")
                            description = proj.get("description", "")
                            year = proj.get("year", "")
                            
                            st.markdown(f"""
                                <div class='metric-card proj-entry'>
                                    <div><strong>{name or 'Untitled Project'}</strong> {f"({year})" if year else ''}</div>
                                    <div>{description or 'No description provided.'}</div>
                                </div>
                            """, unsafe_allow_html=True)
                else:
                    st.markdown("No project information available.")


            with col2_exp: # Changed variable name to avoid conflict
                # ดึง Matching Results ของผู้สมัครจาก MongoDB - moved outside the expander
                # candidate_id = candidate.get("candidate_id")
                # matching_data = db.matching_results_collection.find_one({"candidate_id": candidate_id})

                # top_match = None
                # if matching_data and "matching_scores" in matching_data:
                #     matching_scores = matching_data["matching_scores"]

                #     # หาตำแหน่งที่ได้คะแนนสูงสุด
                #     top_position = max(matching_scores, key=matching_scores.get)
                #     top_score = matching_scores[top_position]

                #     top_match = {
                #         "position": top_position,
                #         "score": round(top_score, 2)
                #     }

                # แสดงผลบน Dashboard - we duplicated this outside the expander
                if top_match:
                    match_score = top_match["score"]
                    position = top_match["position"]

                    if match_score >= 80:
                        color = "#10B981"
                    elif match_score >= 60:
                        color = "#F59E0B"
                    else:
                        color = "#EF4444"

                    st.markdown(f"""
                        <div style="background-color: #F9FAFB; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                            <div style="font-weight: 600; margin-bottom: 0.5rem;">Top Match: {position}</div>
                            <div class="match-indicator" style="background-color: {color}; width: {match_score}%;"></div>
                            <div class="match-text" style="color: {color};">{match_score}%</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("No matching score found for this candidate.")


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
                    # Remove debug information
                    # st.write("Debug - Languages data:", languages)
                    
                    tags_html = ""
                    
                    # Handle different formats of language data
                    if isinstance(languages, dict):
                        # If languages is a dictionary with language names as keys
                        for lang_name, lang_level in languages.items():
                            if lang_name and lang_level:
                                display_text = f"{lang_name} ({lang_level})"
                                tags_html += f'<span class="tag tag-language">{display_text}</span> '
                    elif isinstance(languages, list) and len(languages) > 0:
                        for lang_info in languages:
                            if isinstance(lang_info, dict):
                                lang_name = lang_info.get("language", "")
                                lang_level = lang_info.get("level", "")
                                if lang_name:  # Only add if there's a language name
                                    display_text = f"{lang_name} ({lang_level})" if lang_level else lang_name
                                    tags_html += f'<span class="tag tag-language">{display_text}</span> '
                            elif isinstance(lang_info, str):  # Handle if languages are just strings
                                tags_html += f'<span class="tag tag-language">{lang_info}</span> '
                    
                    if tags_html:  # Only render if we have tags
                        st.markdown(tags_html, unsafe_allow_html=True)
                    else:
                        st.markdown("No language details available.")
                else:
                    st.markdown("No languages listed.")


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
                            if isinstance(cert, dict):
                                name = cert.get("name", "")
                                issuer = cert.get("issuer", "")
                                year = cert.get("year", "")
                                cert_text = f"{name} – {issuer} ({year})" if year else f"{name} – {issuer}"
                                tags_html += f'<span class="tag tag-certification">{cert_text}</span>'
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
