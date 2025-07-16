# src/scraper.py
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# --- Configuration ---
URL = "https://www.linkedin.com/jobs/search"


# --- Main Functions ---

def initialize_driver():
    """
    Initializes the Selenium WebDriver.

    Returns:
        webdriver: An instance of the Selenium WebDriver.
    """
    print("Setting up the Selenium browser driver...")
    # Use the same persistent profile as the automator for a consistent session
    chrome_profile_path = "user-data-dir=chrome_profile_for_job_agent"

    options = webdriver.ChromeOptions()
    options.add_argument(chrome_profile_path)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    try:
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Error: Could not initialize the WebDriver. Please ensure it's installed and in your PATH.")
        print(f"Details: {e}")
        return None


def search_linkedin_jobs(driver, search_term, location):
    """
    Navigates to the website and performs a job search.

    Args:
        driver (webdriver): The Selenium WebDriver instance.
        search_term (str): The job title to search for.
        location (str): The location to search within.
    """
    driver.get(URL)
    print(f"Navigating to LinkedIn Jobs to search for '{search_term}' in '{location}'...")

    try:
        # Find keyword and location input fields
        keyword_input = driver.find_element(By.ID, "job-search-bar-keywords")
        location_input = driver.find_element(By.ID, "job-search-bar-location")

        keyword_input.send_keys(search_term)
        location_input.clear()
        location_input.send_keys(location)
        location_input.send_keys(Keys.ENTER)

    except TimeoutException:
        print("Error: Timed out waiting for search elements to load. The website structure may have changed.")
    except NoSuchElementException:
        print("Error: Could not find one of the search input fields. The website structure may have changed.")


def login_to_linkedin(driver, email, password):
    """Handles logging into LinkedIn if required."""
    driver.get("https://www.linkedin.com/feed/")
    time.sleep(2)  # Allow page to redirect if not logged in

    # If the URL contains 'login' or the security 'authwall', we need to sign in.
    if "login" in driver.current_url or "authwall" in driver.current_url:
        print("LinkedIn login required. Attempting to log in...")
        if not email or not password:
            print("WARNING: LinkedIn credentials not provided. Please log in manually in the browser and wait for the script to continue.")
            try:
                # Wait for the user to log in manually by waiting for the feed to load
                WebDriverWait(driver, 120, poll_frequency=2).until(EC.url_contains("feed"))
                print("Manual login detected. Continuing scrape.")
            except TimeoutException:
                print("ERROR: Manual login was not detected within 2 minutes. Aborting scrape.")
                raise  # Re-raise the exception to stop the process
            return

        try:
            # Standard login form
            email_input = driver.find_element(By.ID, "username")
            password_input = driver.find_element(By.ID, "password")
            email_input.send_keys(email)
            password_input.send_keys(password)
            password_input.send_keys(Keys.ENTER)
            # Wait for the feed to confirm successful login
            WebDriverWait(driver, 20).until(EC.url_contains("feed"))
            print("Successfully logged into LinkedIn via automation.")
        except (NoSuchElementException, TimeoutException):
            print("ERROR: Automated login failed. This can be due to a CAPTCHA or changed layout.")
    else:
        print("Already logged into LinkedIn.")


def scrape_linkedin_results(driver, max_jobs=15):
    """
    Scrapes job details from the LinkedIn search results, including the full description.
    """
    jobs = []
    try:
        # 1. Locate the list of job cards on the left
        job_list_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__results-list")))

        job_cards = job_list_element.find_elements(By.CLASS_NAME, "base-search-card")
        print(f"Found {len(job_cards)} job cards. Scraping top {max_jobs}...")

        # 2. Iterate through each card, click it, and scrape the details
        for card in job_cards[:max_jobs]:
            try:
                # Scroll the card into view to ensure it's clickable
                driver.execute_script("arguments[0].scrollIntoView(true);", card)
                time.sleep(0.5)  # Brief pause to prevent issues
                card.click()
                time.sleep(1)  # Wait for the description pane to update

                # 3. Wait for the description pane to be ready
                description_pane = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__job-details-container"))
                )

                # 4. Scrape all data
                title = card.find_element(By.CLASS_NAME, "base-search-card__title").text.strip()
                company = card.find_element(By.CLASS_NAME, "base-search-card__subtitle").text.strip()
                location = card.find_element(By.CLASS_NAME, "job-search-card__location").text.strip()
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                description_html = description_pane.get_attribute('innerHTML')

                job = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "criteria": description_html,  # Now contains the full description
                }
                jobs.append(job)
                print(f"  + Scraped: {title}")
            except (NoSuchElementException, TimeoutException) as e:
                print(f"  - Could not scrape a job card. Skipping. Details: {e}")
                continue
    except TimeoutException:
        print("Error: Timed out waiting for the initial job listings to appear.")
    return jobs

def run_scraper(driver, search_term, location, email=None, password=None):
    """
    Runs the scraping process using a provided Selenium driver instance.

    Returns:
        list: A list of scraped job dictionaries.
    """
    jobs = []
    if not driver:
        print("ERROR: run_scraper was called with no Selenium driver.")
        return jobs

    try:
        # Login if needed, then perform the search and scrape
        login_to_linkedin(driver, email, password)
        search_linkedin_jobs(driver, search_term, location)
        time.sleep(2)  # Allow results list to settle before starting scrape
        jobs = scrape_linkedin_results(driver, max_jobs=15)
    except Exception as e:
        print(f"An unexpected error occurred in the main scraper workflow: {e}")

    print(f"Scraping complete. Found {len(jobs)} jobs.")
    return jobs

# --- Execution ---

if __name__ == "__main__":
    print("--- Selenium Scraper Script (Test Run) ---")
    # Example usage for testing
    test_search_term = "Software Engineer"
    test_location = "Bengaluru, Karnataka, India"
    # NOTE: The standalone test now needs to manage its own driver instance
    test_driver = initialize_driver()
    job_data = []
    if test_driver:
        try:
            # Pass the driver instance to the function
            job_data = run_scraper(test_driver, test_search_term, test_location)
        finally:
            test_driver.quit()

    if job_data:
        print(f"\n--- Scraper Test Finished: Found {len(job_data)} jobs. ---")
        print("First job found:", job_data[0])
