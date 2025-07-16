# main.py
import requests
from bs4 import BeautifulSoup
import csv

# --- Configuration ---
# URL of a job search website.
# Note: This is a placeholder URL. You'll need to find a site that allows scraping.
# Many modern job sites use JavaScript, which may require Selenium (covered next).
URL = "https://www.indeed.com/jobs?q=python+developer&l=New+York%2C+NY"

# Headers to mimic a real browser visit, which can help avoid getting blocked.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


# --- Main Functions ---

def fetch_job_page(url):
    """
    Fetches the content of a web page.

    Args:
        url (str): The URL of the page to fetch.

    Returns:
        requests.Response: The response object from the HTTP request, or None if it fails.
    """
    print(f"Fetching job listings from: {url}")
    try:
        response = requests.get(url, headers=HEADERS)
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not fetch the URL. {e}")
        return None


def parse_job_listings(html_content):
    """
    Parses the HTML to find job titles and company names.

    Note: The HTML tags and classes used here are examples and will likely
    need to be changed based on the actual structure of the target website.
    You can find the correct selectors using your browser's developer tools.

    Args:
        html_content (str): The HTML content of the job listings page.

    Returns:
        list: A list of dictionaries, where each dictionary represents a job.
    """
    print("Parsing job listings...")
    soup = BeautifulSoup(html_content, "html.parser")
    jobs = []

    # This is a hypothetical selector. You MUST inspect the job site's HTML
    # to find the correct container for job postings.
    job_cards = soup.find_all("div", class_="job_seen_beacon")

    if not job_cards:
        print("Warning: No job cards found. The HTML structure of the site may have changed.")
        print("Please inspect the page source and update the CSS selectors in the script.")

    for card in job_cards:
        # These selectors are also examples.
        title_element = card.find("h2", class_="jobTitle")
        company_element = card.find("span", class_="companyName")
        location_element = card.find("div", class_="companyLocation")

        # Ensure all elements were found before trying to access their text
        if title_element and company_element and location_element:
            job = {
                "title": title_element.get_text(strip=True),
                "company": company_element.get_text(strip=True),
                "location": location_element.get_text(strip=True),
            }
            jobs.append(job)
        else:
            print("Skipping a card because it was missing a title, company, or location.")

    return jobs


def save_to_csv(jobs, filename="job_listings.csv"):
    """
    Saves a list of jobs to a CSV file.

    Args:
        jobs (list): The list of job dictionaries.
        filename (str): The name of the output CSV file.
    """
    if not jobs:
        print("No jobs to save.")
        return

    # The keys of the first job dictionary will be our CSV headers.
    keys = jobs[0].keys()

    try:
        with open(filename, "w", newline="", encoding="utf-8") as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(jobs)
        print(f"Successfully saved {len(jobs)} jobs to {filename}")
    except IOError as e:
        print(f"Error: Could not write to file {filename}. {e}")


# --- Execution ---

if __name__ == "__main__":
    # 1. Fetch the web page
    page_response = fetch_job_page(URL)

    if page_response:
        # 2. Parse the HTML content
        job_data = parse_job_listings(page_response.text)

        # 3. Save the extracted data to a CSV file
        if job_data:
            save_to_csv(job_data)
        else:
            print("Could not find any job data to save.")
