import re
from bs4 import BeautifulSoup


# --- Main Functions ---

def score_job_relevance(job, resume_skills):
    """
    Scores a job based on skill matches in title and description.
    This is the primary scoring function for the Streamlit app.

    Args:
        job (dict): A dictionary representing a single job.
        resume_skills (set): A set of skills extracted from the user's resume.

    Returns:
        tuple: A tuple containing (score, matched_skills_set).
    """
    total_score = 0
    total_found_skills = set()

    # Score based on job title (higher weight)
    title = str(job.get('title', '')).lower()
    for skill in resume_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', title):
            total_score += 2  # Higher weight for skills in the title
            total_found_skills.add(skill)

    # Score based on job description/criteria (standard weight)
    # The field name 'criteria' should match the Browse AI robot's output
    criteria_html = str(job.get('criteria', ''))
    if criteria_html:
        soup = BeautifulSoup(criteria_html, 'html.parser')
        description = soup.get_text().lower()
        for skill in resume_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', description):
                total_score += 1
                total_found_skills.add(skill)

    return total_score, total_found_skills
