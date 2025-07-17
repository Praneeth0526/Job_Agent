# --------------------------------------------------------------------------
# --- AI JOB APPLICATION AGENT
# --- Version: 1.0
# --- Description: A Streamlit-based agent to fetch, rank, and automate
# ---              job applications from LinkedIn, Indeed, and direct
# ---              company career portals (Workday, Greenhouse, etc.).
# --------------------------------------------------------------------------

import os
import json
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- Local Module Imports ---
from src import parser
from src import matcher
from src import scraper
from src import automator
from src import database
from src import logger
from src import llm_helper

# --- 1. CONFIGURATION & INITIALIZATION ---

# Load environment variables from .env file
load_dotenv()

# --- Constants ---
BROWSEAI_API_KEY = os.getenv("BROWSEAI_API_KEY")
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Initialize logger and database
log = logger.setup_logger()
database.init_db()  # Ensure the database and tables are created on startup



# --- Helper Functions ---

def show_error(message, e=None):
    """Displays a standardized error message in Streamlit."""
    st.error(message, icon="🚨")
    if e:
        st.error(f"Details: {e}", icon="📄")


def show_info(message):
    """Displays a standardized info message in Streamlit."""
    st.info(message)


def show_warning(message):
    """Displays a standardized warning message in Streamlit."""
    st.warning(message, icon="⚠️")


def show_success(message):
    """Displays a standardized success message in Streamlit."""
    st.success(message)


# --- 2. BACKEND LOGIC: FETCHING & PARSING ---


def find_relevant_jobs(jobs_list, resume_skills):
    """Scores and ranks jobs based on how well they match skills from the resume."""
    if not jobs_list or not resume_skills:
        return []

    scored_jobs = []
    for job in jobs_list:
        # Delegate scoring logic to the dedicated matcher module
        score, matched_skills = matcher.score_job_relevance(job, resume_skills)

        if score > 2:  # Minimum relevance threshold
            job_with_score = job.copy()
            job_with_score['score'] = score
            # Store the skills that were found for potential display later
            job_with_score['matched_skills'] = sorted(list(matched_skills))
            scored_jobs.append(job_with_score)

    return sorted(scored_jobs, key=lambda x: x['score'], reverse=True)


# --- 3. AUTOMATION LOGIC: SELENIUM HANDLERS ---

class StreamlitStatusUpdater:
    """A wrapper class to pass Streamlit's UI functions to the automator module."""

    def info(self, message): st.info(message)
    def success(self, message): st.success(message)
    def warning(self, message): st.warning(message, icon="⚠️")
    def image(self, path): st.image(path)

    def error(self, message, e=None):
        st.error(message, icon="🚨")
        if e:
            st.error(f"Details: {e}", icon="📄")


# --- 4. STREAMLIT UI ---

st.set_page_config(layout="wide", page_title="AI Job Agent", page_icon="🤖")
st.title("🤖 AI Job Application Agent")

# --- Custom CSS for 3D Effects, Gradient Background, and Enhanced UI ---
ui_enhancements_css = """
<style>
/* New background gradient */
[data-testid="stAppViewContainer"] > .main {
    background-image: linear-gradient(to top, #f0f2f6 0%, #e6e9f0 100%);
}

/* Remove header background to blend with gradient */
[data-testid="stHeader"] {
    background-color: rgba(0,0,0,0);
}

/* 3D effect for job cards created with st.container(border=True) */
div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] {
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transition: box-shadow 0.3s ease-in-out, transform 0.2s ease-in-out;
    border: 1px solid #e2ebf0;
}

div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"]:hover {
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    transform: translateY(-2px);
}

/* --- Button Styling --- */
.stButton > button {
    border-radius: 8px !important;
    transition: all 0.2s ease-in-out !important;
}

/* Green 'Approve' and 'Start Applying' buttons */
button[kind="primary"] {
    background-color: #28a745 !important;
    color: white !important;
    border-color: #28a745 !important;
}
button[kind="primary"]:hover {
    background-color: #218838 !important;
    border-color: #218838 !important;
}
button[kind="primary"]:focus {
    box-shadow: 0 0 0 0.2rem rgba(40,167,69,.5) !important;
    background-color: #218838 !important;
    border-color: #218838 !important;
}

/* Red 'Skip' and 'Cancel' buttons */
/* This affects ALL non-primary buttons by default. */
button[kind="secondary"] {
    background-color: #dc3545 !important;
    color: white !important;
    border-color: #dc3545 !important;
}
button[kind="secondary"]:hover, button[kind="secondary"]:focus {
    background-color: #c82333 !important;
    border-color: #c82333 !important;
}

/* Yellow 'AI Insights' buttons - Overriding the general secondary style */
/* This targets the button in the third column of the job card controls. */
div[data-testid="stHorizontalBlock"] > div:nth-child(3) > div[data-testid="stVerticalBlock"] button[kind="secondary"] {
    background-color: #ffc107 !important;
    color: #212529 !important;
    border-color: #ffc107 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(3) > div[data-testid="stVerticalBlock"] button[kind="secondary"]:hover,
div[data-testid="stHorizontalBlock"] > div:nth-child(3) > div[data-testid="stVerticalBlock"] button[kind="secondary"]:focus {
    background-color: #e0a800 !important;
    border-color: #d39e00 !important;
    color: #212529 !important;
}

/* Compact spacing for job criteria expander */
div[data-testid="stExpander"] div[data-testid="stMarkdown"] p {
    margin-bottom: 0.25rem !important;
    line-height: 1.3 !important;
}
div[data-testid="stExpander"] div[data-testid="stMarkdown"] ul {
    margin-top: 0.25rem !important;
    margin-bottom: 0.5rem !important;
    padding-left: 1.2rem !important;
}
div[data-testid="stExpander"] div[data-testid="stMarkdown"] li {
    margin-bottom: 0.1rem !important;
}
</style>
"""
st.markdown(ui_enhancements_css, unsafe_allow_html=True)

st.markdown("Focusing on **LinkedIn**, **Indeed**, and **Direct Company Portals** for the Indian Tech Market.")

# Initialize session state
if 'scraped_jobs' not in st.session_state:
    st.session_state.scraped_jobs = []
if 'relevant_jobs' not in st.session_state:
    st.session_state.relevant_jobs = []
if 'my_skills' not in st.session_state:
    st.session_state.my_skills = set()
# Removed approved/rejected from session_state as DB will now handle persistence
if 'approved_jobs' not in st.session_state:
    st.session_state.approved_jobs = set()
if 'rejected_jobs' not in st.session_state:
    st.session_state.rejected_jobs = set()
if 'driver' not in st.session_state:
    st.session_state.driver = None
if 'show_insights_for' not in st.session_state:
    st.session_state.show_insights_for = None
if 'resume_path' not in st.session_state:
    st.session_state.resume_path = None
if 'fetching_jobs' not in st.session_state:
    st.session_state.fetching_jobs = False

# --- Sidebar Controls ---
with st.sidebar:
    st.header("🛠️ 1. Upload Resume")
    uploaded_file = st.file_uploader(
        "Upload your resume to get started.",
        type=['pdf', 'docx'],
        help="We'll analyze your resume to find the best job matches."
    )

    # Handle the file upload and store its path in the session state
    if uploaded_file is not None:
        if not os.path.exists("temp"):
            os.makedirs("temp")
        # Save the file to a temporary location
        temp_path = os.path.join("temp", uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        # Store the path for use across the app
        st.session_state.resume_path = temp_path
        st.success(f"Resume '{uploaded_file.name}' uploaded successfully!")

    st.markdown("---")
    st.header("⚙️ 2. Scraper Settings")
    search_term = st.text_input("Additional Keywords (e.g., 'Remote', 'Fintech')", value="")
    location = st.text_input("Location", value="India")

    if st.button("🚀 Fetch & Rank Jobs", type="primary", help="Searches for jobs based on your resume and settings."):
        if not st.session_state.resume_path:
            show_error("Please upload your resume before fetching jobs.")
        else:
            st.session_state.fetching_jobs = True
            st.rerun()  # Rerun to show the spinner in the main panel

    if st.button("🛑 Quit Browser Session"):
        if st.session_state.driver:
            st.session_state.driver.quit()
            st.session_state.driver = None
            st.sidebar.success("Browser session closed.")
        else:
            st.sidebar.info("No active browser session to close.")

# --- Main Content Area Logic ---

if st.session_state.get('fetching_jobs'):
    # Display the spinner in the main panel
    with st.spinner("Please wait... Fetching jobs and ranking them against your profile. This might take a minute."):
        log.info("'Fetch & Rank Jobs' triggered.")

        # --- PARSE RESUME ---
        log.info("Parsing resume to identify your skills...")
        resume_data = parser.parse_resume(st.session_state.resume_path)
        if resume_data and resume_data.get('skills'):
            st.session_state.my_skills = resume_data['skills']
            log.info(f"Resume parsed. Found {len(st.session_state.my_skills)} skills.")
        else:
            log.error("Failed to parse resume or find skills.")
            show_error("Could not find skills in the resume. Aborting.")
            st.session_state.fetching_jobs = False
            st.stop()

        # --- SCRAPE & PROCESS (Now always live and headless) ---
        if st.session_state.my_skills:
            log.info(f"Running intelligent LinkedIn search based on your resume...")
            # Ensure a browser session is active, reusing it if possible
            if st.session_state.driver is None:
                log.info("No active driver found. Initializing a new headless one for scraping.")
                st.session_state.driver = automator.initialize_driver(headless=True)
                show_info("Background browser session started for scraping.")

            if st.session_state.driver:
                st.session_state.scraped_jobs = scraper.run_scraper(
                    st.session_state.driver, st.session_state.my_skills, location,
                    email=LINKEDIN_EMAIL, password=LINKEDIN_PASSWORD, additional_keywords=search_term
                )
            else:
                show_error("Could not initialize the browser. Scraping aborted.")
                st.session_state.scraped_jobs = []

            # --- DATABASE INTEGRATION & RANKING ---
            if st.session_state.scraped_jobs:
                log.info("Filtering and ranking new jobs...")
                processed_urls = {job['job_url'] for job in database.get_all_jobs()}
                unprocessed_jobs = []
                for job in st.session_state.scraped_jobs:
                    job['job_url'] = job.get('link')
                    if job.get('job_url') and job['job_url'] not in processed_urls:
                        unprocessed_jobs.append(job)

                log.info(f"Scraped {len(st.session_state.scraped_jobs)} total jobs. Found {len(unprocessed_jobs)} new jobs to process.")

                if unprocessed_jobs:
                    ranked_jobs = find_relevant_jobs(unprocessed_jobs, st.session_state.my_skills)
                    log.info(f"Found {len(ranked_jobs)} relevant jobs after ranking.")

                    newly_added_count = 0
                    for job in ranked_jobs:
                        if database.add_job(job):
                            newly_added_count += 1
                    show_success(f"Success! Added {newly_added_count} new relevant jobs to the database for your review.")
                else:
                    show_warning("No new jobs found that match your profile. Try different keywords or check back later.")
            else:
                log.warning("Scraper returned no jobs.")

    # Reset the flag after the process is complete
    st.session_state.fetching_jobs = False
    st.rerun()

# --- Main Content Area ---
# Fetch jobs with 'found' status directly from the database for display
jobs_to_display = database.get_jobs_by_status('found')

if not jobs_to_display and not st.session_state.get('fetching_jobs'):
    st.info("No new jobs to display. Click 'Fetch & Rank Jobs' in the sidebar to search for more.")
else:
    st.header(f"📬 {len(jobs_to_display)} New Jobs Found For Review")
    st.markdown("---")

    # Display jobs in a grid
    cols = st.columns(3)
    for i, job in enumerate(jobs_to_display):
        job_id = job.get('id')
        if not job_id:
            log.warning(f"Skipping a job because it has no ID: {job.get('title')}")
            continue

        with cols[i % 3]:
            with st.container(border=True):
                st.subheader(job.get('title', 'No Title'))
                st.write(f"**Company:** {job.get('company', 'N/A')}")
                st.write(f"**Location:** {job.get('location', 'N/A')}")
                #st.metric(label="Relevance Score", value=job.get('score', 0))

                # The 'matched_skills' field from the DB is a pre-formatted string.
                # We just need to display it directly.
                matched_skills_str = job.get('matched_skills')
                if matched_skills_str:
                    st.write(f"**Matched Skills:** {matched_skills_str}")

                with st.expander("Show Job Criteria"):
                    st.markdown(job.get('criteria', 'Not available.'), unsafe_allow_html=True)

                c1, c2, c3 = st.columns([1, 1, 1])

                if c1.button("Approve & Apply", key=f"approve_{job_id}", type="primary", use_container_width=True):
                    log.info(f"User approved job for application: {job.get('title')}")
                    database.update_job_status(job_id, 'applying')
                    st.rerun()

                if c2.button("Skip", key=f"reject_{job_id}", use_container_width=True):
                    log.info(f"User skipped job: {job.get('title')}")
                    database.update_job_status(job_id, 'rejected')
                    st.rerun()

                with c3:
                    # This button now toggles the display of insights below
                    if st.button("💡 AI Insights", key=f"ai_{job_id}", use_container_width=True):
                        # Toggle display: if already showing for this job, hide it.
                        if st.session_state.get('show_insights_for') == job_id:
                            st.session_state['show_insights_for'] = None
                        else:
                            # Otherwise, show it and generate insights if they don't exist yet
                            st.session_state['show_insights_for'] = job_id
                            if f"insights_{job_id}" not in st.session_state:
                                with st.spinner("Asking the AI for talking points..."):
                                    log.info(f"Generating AI insights for: {job.get('title')}")
                                    prompt = llm_helper.generate_talking_points_prompt(job, st.session_state.my_skills)
                                    insights = llm_helper.get_ai_insights(prompt)
                                    st.session_state[f"insights_{job_id}"] = insights

                # --- Display AI Insights below the buttons if toggled ---
                if st.session_state.get('show_insights_for') == job_id:
                    if f"insights_{job_id}" in st.session_state:
                        st.info(f"**AI Insights for {job.get('title')}**")
                        st.markdown(st.session_state[f"insights_{job_id}"])

# --- Section for jobs ready to be applied for ---
jobs_to_apply = database.get_jobs_by_status('applying')

if jobs_to_apply:
    st.header("🎯 Ready to Apply")
    st.markdown("---")

    for job in jobs_to_apply:
        job_id = job.get('id')
        if not job_id:
            continue

        with st.container(border=True):
            st.subheader(f"Generate text for: {job.get('title')} at {job.get('company')}")

            # Use session state to store the generated text for each job
            if f"app_text_{job_id}" not in st.session_state:
                st.session_state[f"app_text_{job_id}"] = ""

            if st.button("📝 Generate Application Text", key=f"generate_{job_id}"):
                if not st.session_state.resume_path:
                    show_error("Resume path not found. Please upload your resume again in the sidebar.")
                    st.stop()

                with st.spinner("🤖 AI is writing your application summary..."):
                    # Use the enhanced parser that returns a dictionary
                    resume_data = parser.parse_resume(st.session_state.resume_path)
                    if resume_data and resume_data.get('full_text'):
                        resume_text = resume_data['full_text']
                        prompt = llm_helper.generate_application_text_prompt(job, resume_text)
                        generated_text = llm_helper.get_ai_insights(prompt)
                        st.session_state[f"app_text_{job_id}"] = generated_text
                    else:
                        st.session_state[f"app_text_{job_id}"] = "Error: Could not read resume text to generate content."

            if st.session_state[f"app_text_{job_id}"]:
                st.text_area(
                    "Review and edit the generated text:",
                    value=st.session_state[f"app_text_{job_id}"],
                    height=250,
                    key=f"textarea_{job_id}"
                )

                c1, c2, _ = st.columns([1, 1, 3])

                if c1.button("👍 Looks Good, Start Applying", key=f"start_apply_{job_id}", type="primary"):
                    if not st.session_state.resume_path:
                        show_error("Resume path not found. Please upload your resume again in the sidebar.")
                        st.stop()

                    with st.spinner("Gathering data and starting browser automation..."):
                        log.info(f"Starting automation for: {job.get('title')}")
                        resume_data = parser.parse_resume(st.session_state.resume_path)
                        if not resume_data:
                            show_error("Could not parse resume. Aborting automation.")
                            st.stop()

                        # Get the latest edited text from the text area
                        edited_application_text = st.session_state[f"textarea_{job_id}"]

                        # --- TRIGGER THE AUTOMATION ---
                        # Ensure a browser session is active, reusing or creating as needed.
                        # This is where the app will "wait" for the user, by keeping the
                        # browser window open for them to log in.
                        if st.session_state.driver is None:
                            with st.spinner("Initializing new browser session..."):
                                st.session_state.driver = automator.initialize_driver()

                        if st.session_state.driver:
                            automator.start_application(st.session_state.driver, job['job_url'], resume_data, edited_application_text)
                        else:
                            show_error("Could not initialize browser for automation.")
                            st.stop()  # stop execution if browser fails

                    show_success(f"Application process for '{job.get('title')}' has finished.")
                    database.update_job_status(job_id, 'applied') # Mark as applied after automation
                    st.rerun()

                if c2.button("👎 Cancel", key=f"cancel_apply_{job_id}"):
                    # Move the job back to the 'found' queue for re-review
                    database.update_job_status(job_id, 'found')
                    st.session_state[f"app_text_{job_id}"] = ""  # Clear the generated text
                    st.rerun()
