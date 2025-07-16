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


def extract_skills_from_text(text):
    """
    Extracts a predefined list of technical skills from text.
    This logic is based on your `app.py` for consistency.
    """
    if not text:
        return set()

    # This list is from your Streamlit app. You can manage it here centrally.
    technical_skills = {
        'python', 'java', 'c++', 'javascript', 'react', 'angular', 'vue', 'node.js', 'next.js',
        'sql', 'mysql', 'postgresql', 'mongodb', 'nosql', 'dynamodb', 'docker', 'kubernetes', 'aws',
        'azure', 'gcp', 'terraform', 'ansible', 'selenium', 'django', 'flask', 'fastapi', 'git',
        'api', 'rest', 'graphql', 'html', 'css', 'typescript', 'machine learning', 'data science',
        'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'deep learning', 'nlp',
        'data analysis', 'business intelligence', 'tableau', 'power bi', 'big data', 'spark', 'hadoop'
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
        tuple: A tuple containing (full_text, found_skills_set) or (None, None) on failure.
    """
    text = ""
    if not os.path.exists(file_path):
        print(f"Error: Resume file not found at '{file_path}'.")
        return None, None

    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        print(f"Unsupported file format: {file_path}")
        return None, None

    if not text:
        print(f"Could not extract text from {file_path}.")
        return None, None

    skills = extract_skills_from_text(text)
    return text, skills


# --- Execution for testing ---

if __name__ == "__main__":
    print("--- Testing Resume Parser ---")

    # NOTE: Update this path to point to your actual resume file for testing.
    resume_to_test = os.path.join("..", "Resume", "New_resume.pdf")

    if os.path.exists(resume_to_test):
        full_text, found_skills = parse_resume(resume_to_test)
        if full_text and found_skills:
            print(f"\nSuccessfully parsed: {resume_to_test}")
            print("\n--- Found Skills ---")
            print(", ".join(sorted(list(found_skills))))
            email = find_email_in_text(full_text)
            print(f"\n--- Found Email ---\n{email or 'No email found.'}")
        else:
            print(f"Failed to parse {resume_to_test}.")
    else:
        print(f"\nWARNING: Test resume not found at '{os.path.abspath(resume_to_test)}'.")
        print("Please create the file to run a full test.")

    print("\n--- Parser Test Finished ---")
