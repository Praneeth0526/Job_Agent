import os
import json
import re
import requests
import streamlit as st
import docx
import PyPDF2
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver

# --- Configuration ---
load_dotenv()
RESUME_FILE_PATH = "Resume/New_resume.pdf"  # IMPORTANT: Update this path if needed
CHROME_PROFILE_PATH = "user-data-dir=chrome_profile"
BROWSEAI_API_KEY = os.getenv("BROWSEAI_API_KEY")


@st.cache_data(ttl=3600)  # Cache the data for 1 hour to avoid re-fetching
def get_jobs_from_browseai(api_robot_id):
    """Fetches the latest job listings from your Browse AI robot's API."""
    if not BROWSEAI_API_KEY:
        st.error("Error: BROWSEAI_API_KEY not found in .env file.")
        return []
    if not api_robot_id or "YOUR_ROBOT_ID" in api_robot_id:
        st.error("Please enter a valid Browse AI Robot ID in the sidebar.")
        return []

    api_url = f"https://api.browse.ai/v2/robots/{api_robot_id}/tasks"
    headers = {"Authorization": f"Bearer {BROWSEAI_API_KEY}"}

    try:
        # 1. Get the list of recent tasks to find the latest one
        st.write("Fetching recent tasks from Browse AI...")
        response = requests.get(api_url, headers=headers, params={"limit": 1})
        response.raise_for_status()
        tasks = response.json().get('result', {}).get('robotTasks', {}).get('items', [])

        if not tasks:
            st.error("No recent tasks found from Browse AI for this robot.")
            return []

        # 2. Get the captured data from the latest task
        latest_task_id = tasks[0]['id']
        st.write(f"Fetching data from the latest task: {latest_task_id}...")
        task_response = requests.get(f"{api_url}/{latest_task_id}", headers=headers)
        task_response.raise_for_status()

        # The actual data is in a 'capturedLists' field.
        # You need to find the correct key for your list of jobs.
        captured_lists = task_response.json().get('result', {}).get('capturedLists', {})
        if not captured_lists:
            st.error("Could not find 'capturedLists' in the API response. Check your robot's output.")
            return []

        # Assuming the first list in the dictionary is the one with jobs.
        # **IMPORTANT**: You might need to change this key to match your robot's output!
        # Common keys are "List", "JobListings", "Sheet1", etc.
        job_list_key = next(iter(captured_lists))
        jobs = captured_lists.get(job_list_key, [])

        # Ensure 'link' exists and is unique, otherwise use a fallback ID
        for i, job in enumerate(jobs):
            if 'link' not in job or not job['link']:
                job['link'] = f"no_link_{i}"

        return jobs

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from Browse AI: {e}")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching jobs: {e}")
        return []


def parse_resume_for_skills(file_path):
    """Extracts text from a resume and identifies a predefined set of key skills."""
    text = ""
    try:
        if file_path.lower().endswith(".pdf"):
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
        elif file_path.lower().endswith(".docx"):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text
        else:
            st.error(f"Unsupported file format: {file_path}")
            return set()
    except FileNotFoundError:
        st.error(f"Error: Resume file not found at '{file_path}'.")
        return set()

    technical_skills = {
        'python', 'java', 'c++', 'javascript', 'react', 'angular', 'vue', 'node.js',
        'sql', 'mysql', 'postgresql', 'mongodb', 'docker', 'kubernetes', 'aws',
        'azure', 'gcp', 'selenium', 'django', 'flask', 'git', 'api', 'rest', 'html', 'css',
        'typescript', 'machine learning', 'data science', 'pandas', 'numpy'
    }
    found_skills = {skill for skill in technical_skills if
                    re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE)}
    return found_skills


def find_relevant_jobs(jobs_list, resume_skills):
    """Scores and ranks jobs based on how well they match skills from the resume."""
    if not jobs_list or not resume_skills:
        return []

    scored_jobs = []
    for job in jobs_list:
        score = 0
        title = str(job.get('title', '')).lower()
        # The field name 'criteria' should match your Browse AI robot's output
        soup = BeautifulSoup(job.get('criteria', ''), 'html.parser')
        description = soup.get_text().lower()

        for skill in resume_skills:
            if skill in title:
                score += 2
            if skill in description:
                score += 1

        if score > 2:  # Minimum relevance threshold
            job_with_score = job.copy()
            job_with_score['score'] = score
            scored_jobs.append(job_with_score)

    return sorted(scored_jobs, key=lambda x: x['score'], reverse=True)


def initialize_driver():
    """Creates and returns a Selenium WebDriver instance."""
    options = webdriver.ChromeOptions()
    options.add_argument(CHROME_PROFILE_PATH)
    # Add any other options you need, like --headless
    return webdriver.Chrome(options=options)


def automate_application(driver, job):
    """Placeholder for the highly complex application automation logic."""
    st.info(f"Attempting to automate application for: **{job.get('title')}**")
    job_url = job.get('link')
    if not job_url:
        st.error("Job URL not found. Cannot apply.")
        return

    driver.get(job_url)
    st.success(f"Navigated to job page. Build portal-specific logic (Workday, Greenhouse, etc.) here.")
    # In a real scenario, you'd add logic here and return True/False on success


# --- Streamlit App UI ---

st.set_page_config(layout="wide", page_title="AI Job Agent")
st.title("🤖 AI Job Application Agent")

# Initialize session state to hold data across reruns
if 'scraped_jobs' not in st.session_state:
    st.session_state.scraped_jobs = []
if 'relevant_jobs' not in st.session_state:
    st.session_state.relevant_jobs = []
if 'approved_jobs' not in st.session_state:
    st.session_state.approved_jobs = set()
if 'rejected_jobs' not in st.session_state:
    st.session_state.rejected_jobs = set()
if 'driver' not in st.session_state:
    st.session_state.driver = None

with st.sidebar:
    st.header("Controls")
    browse_ai_robot_id = st.text_input("Browse AI Robot ID", value="YOUR_ROBOT_ID_HERE")
    resume_path = st.text_input("Path to your Resume", value=RESUME_FILE_PATH)
    use_test_data = st.checkbox("Use local test data (`jobs.json`)", value=False)

    if st.button("🚀 Fetch & Rank Jobs"):
        # Reset state for a new search
        st.session_state.approved_jobs.clear()
        st.session_state.rejected_jobs.clear()

        with st.spinner("Parsing resume to identify your skills..."):
            st.session_state.my_skills = parse_resume_for_skills(resume_path)
            if st.session_state.my_skills:
                st.success(f"Found {len(st.session_state.my_skills)} skills.")
            else:
                st.error("Could not find skills in resume. Aborting fetch.")

        if st.session_state.my_skills:
            if use_test_data:
                st.info("Using local test data from jobs.json.")
                with open('jobs.json', 'r') as f:
                    st.session_state.scraped_jobs = json.load(f)
            else:
                with st.spinner("Fetching jobs from Browse AI... This can take a moment."):
                    st.session_state.scraped_jobs = get_jobs_from_browseai(browse_ai_robot_id)

            if st.session_state.scraped_jobs:
                st.success(f"Fetched {len(st.session_state.scraped_jobs)} jobs.")
                with st.spinner("Ranking jobs against your profile..."):
                    st.session_state.relevant_jobs = find_relevant_jobs(
                        st.session_state.scraped_jobs,
                        st.session_state.my_skills
                    )
                st.success(f"Found {len(st.session_state.relevant_jobs)} relevant jobs.")
            else:
                st.error("Fetching returned no jobs. Check the API ID and Browse AI dashboard.")

if not st.session_state.relevant_jobs:
    st.info("Click 'Fetch & Rank Jobs' in the sidebar to start.")
else:
    st.header(f"Top {len(st.session_state.relevant_jobs)} Relevant Jobs")

    # Create columns for a cleaner layout
    cols = st.columns(3)
    col_idx = 0

    for i, job in enumerate(st.session_state.relevant_jobs):
        job_id = job['link']  # Use link as a unique ID

        # Skip jobs that have already been actioned
        if job_id in st.session_state.approved_jobs or job_id in st.session_state.rejected_jobs:
            continue

        with cols[col_idx % 3]:
            with st.container(border=True):
                st.subheader(job.get('title', 'No Title'))
                st.write(f"**Company:** {job.get('company', 'N/A')}")
                st.write(f"**Location:** {job.get('location', 'N/A')}")
                st.metric(label="Relevance Score", value=job.get('score', 0))

                with st.expander("Show Job Criteria"):
                    # The field name 'criteria' should match your Browse AI robot's output
                    st.markdown(job.get('criteria', 'Not available.'), unsafe_allow_html=True)

                # Action buttons
                c1, c2 = st.columns(2)
                if c1.button("✅ Approve", key=f"approve_{i}"):
                    if st.session_state.driver is None:
                        st.session_state.driver = initialize_driver()

                    automate_application(st.session_state.driver, job)
                    st.session_state.approved_jobs.add(job_id)
                    st.rerun()

                if c2.button("❌ Reject", key=f"reject_{i}"):
                    st.session_state.rejected_jobs.add(job_id)
                    st.rerun()

        col_idx += 1

    if st.sidebar.button("Quit Browser Session"):
        if st.session_state.driver:
            st.session_state.driver.quit()
            st.session_state.driver = None
            st.sidebar.success("Browser session closed.")
