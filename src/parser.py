# src/parser.py
import re
import os
import PyPDF2
import docx

# --- Configuration ---
# This file does not require configuration. It accepts a file path.


# --- Main Functions ---

def extract_text_from_pdf(file_path):
    """
    Extracts all text from a PDF file.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        str: The extracted text, or an empty string if an error occurs.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return ""

    print(f"Reading PDF: {file_path}")
    try:
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    except Exception as e:
        print(f"An error occurred while reading the PDF: {e}")
        return ""


def extract_text_from_docx(file_path):
    """
    Extracts all text from a DOCX file.

    Args:
        file_path (str): The path to the DOCX file.

    Returns:
        str: The extracted text, or an empty string if an error occurs.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return ""

    print(f"Reading DOCX: {file_path}")
    try:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"An error occurred while reading the DOCX file: {e}")
        return ""


def find_email_in_text(text):
    """
    Uses a regular expression to find the first email address in a block of text.

    Args:
        text (str): The text to search within.

    Returns:
        str: The found email address, or "No email found."
    """
    # This is a common regex for finding email addresses.
    email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    match = re.search(email_regex, text)

    return match.group(0) if match else None


def find_phone_in_text(text):
    """
    Uses a regular expression to find a phone number in a block of text.
    This regex is designed for common formats.
    """
    # This regex looks for various formats like (123) 456-7890, 123-456-7890, 123 456 7890, etc.
    phone_regex = r"(\(?\d{3}\)?[-.\s]?)?(\d{3}[-.\s]?\d{4})"
    match = re.search(phone_regex, text)
    return match.group(0) if match else None


def find_name_in_text(text):
    """
    A heuristic-based approach to find a person's name in resume text.
    It looks for a 2-3 word line near the top of the text.
    """
    # Names are often in the first few lines of a resume.
    lines = text.split('\n')[:5]
    for line in lines:
        line = line.strip()
        # A common name format is 2-3 words, no numbers, no special characters other than spaces.
        if 1 < len(line.split()) < 4 and re.match(r"^[a-zA-Z\s]*$", line):
            # Very basic check to avoid catching headers like "Professional Experience"
            if "experience" not in line.lower() and "education" not in line.lower():
                return line
    return None


def extract_skills_from_text(text):
    """
    Extracts a predefined list of technical skills from text.
    This logic is based on your `streamlit_app.py` for consistency.
    """
    if not text:
        return set()

    # A comprehensive, categorized list of skills for a modern software developer role.
    technical_skills = {
        # Programming Languages
        'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'go', 'rust', 'kotlin', 'swift', 'ruby', 'php',
        'html', 'css', 'sql', 'c','dart',

        # Web Frameworks (Backend)
        'django', 'flask', 'fastapi', 'node.js', 'express.js', 'spring boot', 'ruby on rails', '.net',

        # Web Frameworks (Frontend & Mobile)
        'react', 'angular', 'vue', 'vue.js', 'svelte', 'next.js', 'nuxt.js', 'flutter', 'react native',

        # Databases
        'mysql', 'postgresql', 'mssql', 'sqlite', 'oracle', 'mongodb', 'redis', 'cassandra', 'dynamodb',
        'nosql', 'firebase', 'neo4j', 'supabase',

        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digitalocean', 'oracle cloud',
        'docker', 'kubernetes', 'openshift',
        'jenkins', 'gitlab', 'github actions', 'circleci',
        'terraform', 'ansible', 'puppet', 'chef',
        'prometheus', 'grafana', 'datadog', 'splunk',

        # Data Science & Machine Learning
        'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn',
        'scikit-learn', 'tensorflow', 'pytorch', 'keras',
        'opencv', 'nltk', 'spacy', 'hugging face', 'langchain',
        'spark', 'hadoop', 'kafka',
        'tableau', 'power bi', 'looker', 'streamlit',
        'machine learning', 'deep learning', 'nlp', 'natural language processing', 'data science', 'data analysis',
        'business intelligence', 'big data', 'data visualization', 'etl',

        # Tools & Methodologies
        'git', 'github', 'jira', 'confluence',
        'agile', 'scrum', 'kanban','figma','kaggle',
        'rest', 'graphql', 'soap', 'api', 'microservices', 'serverless',
        'selenium', 'pytest', 'junit', 'jest'
    }

    found_skills = {skill for skill in technical_skills if
                    re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE)}
    return found_skills


def parse_resume(file_path):
    """
    A high-level function to parse a resume file and return its text and skills.

    Args:
        file_path (str): The full path to the .pdf or .docx resume file.

    Returns:
        dict: A dictionary containing all parsed data, or None on failure.
    """
    full_text = ""
    if not os.path.exists(file_path):
        print(f"Error: Resume file not found at '{file_path}'.")
        return None

    if file_path.lower().endswith(".pdf"):
        full_text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        full_text = extract_text_from_docx(file_path)
    else:
        print(f"Unsupported file format: {file_path}")
        return None

    if not full_text:
        print(f"Could not extract text from {file_path}.")
        return None

    # Extract all components
    name = find_name_in_text(full_text)
    first_name = name.split()[0] if name else ""
    last_name = name.split()[-1] if name and len(name.split()) > 1 else ""

    return {
        'full_text': full_text,
        'skills': extract_skills_from_text(full_text),
        'name': name,
        'first_name': first_name,
        'last_name': last_name,
        'email': find_email_in_text(full_text),
        'phone': find_phone_in_text(full_text),
        'resume_path': os.path.abspath(file_path) # Ensure the path is absolute for Selenium
    }


# --- Execution for testing ---

if __name__ == "__main__":
    print("--- Testing Resume Parser ---")

    # NOTE: Update this path to point to your actual resume file for testing.
    resume_to_test = os.path.join("..", "Resume", "New_resume.pdf")

    if os.path.exists(resume_to_test):
        resume_data = parse_resume(resume_to_test)
        if resume_data:
            print(f"\nSuccessfully parsed: {resume_to_test}")
            print(f"\n--- Found Name: {resume_data.get('name', 'N/A')} ---")
            print(f"--- Found Email: {resume_data.get('email', 'N/A')} ---")
            print(f"--- Found Phone: {resume_data.get('phone', 'N/A')} ---")
            print("\n--- Found Skills ---")
            print(", ".join(sorted(list(resume_data.get('skills', [])))))
        else:
            print(f"Failed to parse {resume_to_test}.")
    else:
        print(f"\nWARNING: Test resume not found at '{os.path.abspath(resume_to_test)}'.")
        print("Please create the file to run a full test.")

    print("\n--- Parser Test Finished ---")
