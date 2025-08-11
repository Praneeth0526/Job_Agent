# --------------------------------------------------------------------------
# --- AI JOB APPLICATION AGENT - AUTOMATOR MODULE
# --- Version: 2.0
# --- Description: Handles browser automation for filling out job applications
# ---              on various platforms (Greenhouse, Workday, Lever, etc.).
# --------------------------------------------------------------------------

import os


# It's good practice to manage WebDriver installation.
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller


def initialize_driver(headless=False):
    """Initializes and returns a Selenium WebDriver instance with auto-matching ChromeDriver."""

    # Install matching ChromeDriver for current system Chrome
    chromedriver_autoinstaller.install()

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    if headless:
        options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)
    print("WebDriver initialized.")
    return driver


def start_application(driver, job_url):
    """
    Uses an existing browser session to navigate to the specified job URL.
    The browser window is left open for the user to manually apply.

    Args:
        driver: The active Selenium WebDriver instance.
        job_url (str): The URL of the job application page.
    """
    # Defensive check for required data
    if not all([driver, job_url]):
        print("Error: Missing driver or job_url.")
        return

    try:
        print(f"Navigating to job URL: {job_url}")
        driver.get(job_url)

        # --- Final Manual Review Step ---
        print("\n" + "=" * 50)
        print("✅ Navigation complete.")
        print(">>> The job posting has been opened in the browser for you. <<<")
        print(">>> Please proceed with the application manually. <<<")
        print("=" * 50 + "\n")

    except Exception as e:
        print(f"A critical error occurred while navigating to the job URL: {e}")
        # Save a screenshot for debugging
        driver.save_screenshot("critical_error.png")
        print("Saved a screenshot to 'critical_error.png'.")


# --- Example Usage (for testing this script directly) ---
if __name__ == '__main__':
    print("--- Running Automator Test ---")

    # Create dummy data for the test run.
    # IMPORTANT: You MUST replace 'resume_path' with the absolute path to a real file.
    test_resume_data = {
        'first_name': 'Testy',
        'last_name': 'McTestface',
        'email': 'testy.mctestface@example.com',
        'phone': '555-123-4567',
        # Get the absolute path to the resume file relative to this script
        'resume_path': os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Resume', 'New_resume.pdf'))
    }

    test_job_url = "https://www.linkedin.com/jobs/" # Example URL

    if not os.path.exists(test_resume_data['resume_path']):
        print("FATAL ERROR: The test resume file was not found at the specified path:")
        print(f"-> {test_resume_data['resume_path']}")
        print("Please ensure the file exists and the path is correct in the `if __name__ == '__main__':` block.")
    else:
        # For direct testing, we now need to initialize a driver first and pass it.
        test_driver = initialize_driver()
        start_application(test_driver, test_job_url)
        input("--> Test finished. Press Enter in this terminal to close the browser...")
        test_driver.quit()

    print("\n--- Automator Test Finished ---")