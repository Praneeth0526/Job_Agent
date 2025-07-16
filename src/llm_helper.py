# src/llm_helper.py
import os
import requests
from bs4 import BeautifulSoup

# --- Configuration ---
# It is highly recommended to set your API key as an environment variable.
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"


def generate_talking_points_prompt(job, user_skills):
    """
    Creates a prompt for the AI to generate key talking points for a job.

    Args:
        job (dict): A dictionary with job info.
        user_skills (set): A set of the user's skills.

    Returns:
        str: A formatted prompt string.
    """
    # Clean up the job criteria HTML for the prompt
    soup = BeautifulSoup(job.get('criteria', ''), 'html.parser')
    job_description = soup.get_text(separator=' ', strip=True)

    prompt = f"""
    You are a professional career coach. Analyze the provided job description and my skills.
    Generate 3-4 concise, bulleted talking points that I can use in a cover letter or interview.
    For each point, briefly explain how one of my specific skills directly addresses a key requirement from the job description.

    **Job Title:** {job.get('title', 'N/A')}
    **Company:** {job.get('company', 'N/A')}
    **Job Description:** "{job_description[:1000]}..."

    **My Key Skills:**
    {', '.join(sorted(list(user_skills)))}

    Generate the talking points now.
    """
    return prompt


def get_ai_insights(prompt):
    """
    Calls the Gemini API to generate insights.

    Args:
        prompt (str): The prompt to send to the model.

    Returns:
        str: The generated text from the AI, or an error message.
    """
    if not API_KEY:
        return "Error: GEMINI_API_KEY is not set. Please set it in your .env file."

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 500,
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
        # Navigate the JSON response to get the text
        text = data['candidates'][0]['content']['parts'][0]['text']
        return text
    except requests.exceptions.RequestException as e:
        return f"Error: API request failed. The service may be unavailable or the API key may be invalid. Details: {e}"
    except (KeyError, IndexError) as e:
        return f"Error: Could not parse the API response. The response format may have changed. Details: {e}\nResponse: {data}"