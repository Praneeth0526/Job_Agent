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
# IMPORTANT: Update this path to your resume file.
RESUME_FILE_PATH = "Resume/New_resume.pdf"
BROWSEAI_API_KEY = os.getenv("BROWSEAI_API_KEY")
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Initialize logger and database
log = logger.setup_logger()


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

st.set_page_config(layout="wide", page_title="AI Job Agent")
st.title("🤖 AI Job Application Agent")
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

# --- Sidebar Controls ---
with st.sidebar:
    st.header("Controls")
    resume_path_input = st.text_input("Path to your Resume", value=RESUME_FILE_PATH)
    st.markdown("---")
    st.header("Scraper Settings")
    search_term = st.text_input("Job Title / Keywords", value="Python Developer")
    location = st.text_input("Location", value="India")
    use_test_data = st.checkbox("Use local test data (`jobs.json`)", value=False)

    if st.button("🚀 Fetch & Rank Jobs", type="primary"):
        # Now handled by database checks
        # st.session_state.approved_jobs.clear()
        # st.session_state.rejected_jobs.clear()
        log.info("'Fetch & Rank Jobs' button clicked.")

        with st.spinner("Parsing resume to identify your skills..."):
            # Use the dedicated parser module now
            _, st.session_state.my_skills = parser.parse_resume(resume_path_input)
            if st.session_state.my_skills:
                log.info(f"Resume parsed. Found {len(st.session_state.my_skills)} skills.")
                st.success(f"Found {len(st.session_state.my_skills)} skills.")
            else:
                log.error("Failed to parse resume or find skills.")
                st.error("Could not find skills. Aborting.")

        if st.session_state.my_skills:
            if use_test_data:
                show_info("Using local test data from jobs.json.")
                try:
                    with open('jobs.json', 'r') as f:
                        st.session_state.scraped_jobs = json.load(f)
                except FileNotFoundError:
                    log.error("jobs.json not found when 'Use local test data' was checked.")
                    show_error("`jobs.json` not found. Please uncheck the box or create the file.")
                    st.session_state.scraped_jobs = []
            else:
                with st.spinner(f"Scraping LinkedIn for '{search_term}' in '{location}'..."):
                    # Ensure a browser session is active, reusing it if possible
                    if st.session_state.driver is None:
                        log.info("No active driver found. Initializing a new one for scraping.")
                        with st.spinner("Initializing browser for the first time..."):
                            st.session_state.driver = automator.initialize_driver()
                            show_info("Browser initialized. It will be reused for all actions.")

                    if st.session_state.driver:
                        st.session_state.scraped_jobs = scraper.run_scraper(
                            st.session_state.driver, search_term, location,
                            email=LINKEDIN_EMAIL, password=LINKEDIN_PASSWORD
                        )
                    else:
                        show_error("Could not initialize the browser. Scraping aborted.")
                        st.session_state.scraped_jobs = []

            # --- DATABASE INTEGRATION ---
            # Filter out jobs that have already been processed
            unprocessed_jobs = []
            if st.session_state.scraped_jobs:
                processed_urls = {job['job_url'] for job in database.get_all_jobs()}
                for job in st.session_state.scraped_jobs:
                    # Add a unique ID based on the job link for database tracking
                    job['id'] = job.get('link') or f"no_link_{job.get('title')}"
                    # Use the link as the unique URL
                    job['job_url'] = job.get('link')
                    if job['job_url'] and job['job_url'] not in processed_urls:
                        database.add_job(job) # Add new job with 'found' status
                        unprocessed_jobs.append(job)
                log.info(f"Found {len(unprocessed_jobs)} new, unprocessed jobs.")
            else:
                log.warning("Scraper returned no jobs.")

            if unprocessed_jobs:
                show_success(f"Scraped {len(st.session_state.scraped_jobs)} jobs. Found {len(unprocessed_jobs)} new ones.")
                with st.spinner("Ranking jobs against your profile..."):
                    st.session_state.relevant_jobs = find_relevant_jobs(
                        unprocessed_jobs,
                        st.session_state.my_skills
                    )
                show_success(f"Found {len(st.session_state.relevant_jobs)} relevant jobs.")
            else:
                show_warning("No new jobs found that match your profile. Try different keywords or check back later.")

    if st.button("Quit Browser Session"):
        if st.session_state.driver:
            st.session_state.driver.quit()
            st.session_state.driver = None
            st.sidebar.success("Browser session closed.")
        else:
            st.sidebar.info("No active browser session to close.")

# --- Main Content Area ---
if not st.session_state.relevant_jobs:
    st.info("Click 'Fetch & Rank Jobs' in the sidebar to start your search.")
else:
    st.header(f"Top {len(st.session_state.relevant_jobs)} Relevant Jobs")
    st.markdown("---")

    # Display jobs in a grid
    cols = st.columns(3)
    col_idx = 0

    for i, job in enumerate(st.session_state.relevant_jobs):
        job_id = job['id']

        # This check is now redundant due to pre-filtering but kept as a failsafe for the view
        if database.get_job_status(job_id) != 'found':
            continue

        with cols[col_idx % 3]:
            with st.container(border=True):
                st.subheader(job.get('title', 'No Title'))
                st.write(f"**Company:** {job.get('company', 'N/A')}")
                st.write(f"**Location:** {job.get('location', 'N/A')}")
                st.metric(label="Relevance Score", value=job.get('score', 0))
                st.write(f"**Matched Skills:** {', '.join(job.get('matched_skills', []))}")

                with st.expander("Show Job Criteria"):
                    st.markdown(job.get('criteria', 'Not available.'), unsafe_allow_html=True)

                c1, c2, c3 = st.columns(3)
                if c1.button("✅ Approve & Apply", key=f"approve_{job_id}", type="primary"):
                    log.info(f"User approved job: {job.get('title')}")
                    if st.session_state.driver is None:
                        with st.spinner("Initializing browser... Please wait."):
                            log.info("Initializing Selenium driver...")
                            st.session_state.driver = automator.initialize_driver()
                            show_info("Browser initialized. You may need to log in manually the first time.")

                    current_resume_path = os.path.abspath(resume_path_input)
                    if not os.path.exists(current_resume_path):
                        log.critical(f"Resume file not found at absolute path: {current_resume_path}")
                        show_error(f"FATAL: Resume not found at {current_resume_path}")
                    else:
                        database.update_job_status(job_id, 'applied')
                        status_updater = StreamlitStatusUpdater()
                        automator.automate_application(st.session_state.driver, job, current_resume_path,
                                                       status_updater)
                    st.rerun()

                if c2.button("❌ Reject", key=f"reject_{job_id}"):
                    log.info(f"User rejected job: {job.get('title')}")
                    database.update_job_status(job_id, 'rejected')
                    st.rerun()

                with c3:
                    if st.button("💡 AI Insights", key=f"ai_{job_id}"):
                        log.info(f"User requested AI insights for: {job.get('title')}")
                        with st.spinner("Asking the AI for talking points..."):
                            prompt = llm_helper.generate_talking_points_prompt(job, st.session_state.my_skills)
                            insights = llm_helper.get_ai_insights(prompt)
                            st.info(f"**AI Insights for {job.get('title')}**")
                            st.markdown(insights)
        col_idx += 1
