# --------------------------------------------------------------------------
# --- AI JOB APPLICATION AGENT - AUTOMATOR MODULE
# --- Version: 2.0
# --- Description: Handles browser automation for filling out job applications
# ---              on various platforms (Greenhouse, Workday, Lever, etc.).
# --------------------------------------------------------------------------

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# It's good practice to manage WebDriver installation.
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


def initialize_driver(headless=False):
    """Initializes and returns a Selenium WebDriver instance."""
    # Using a persistent profile can help with logins, but for this task, a fresh one is fine.
    # CHROME_PROFILE_PATH = "user-data-dir=chrome_profile_for_job_agent"
    options = webdriver.ChromeOptions()
    # options.add_argument(CHROME_PROFILE_PATH)
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    # To see the browser in action, keep headless mode off.
    if headless:
        options.add_argument("--headless")

    # Use webdriver_manager to handle the driver automatically
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("WebDriver initialized.")
    return driver


def _fill_workday_form(driver, resume_data, application_text):
    """Handles the application process for Workday portals."""
    print("Workday portal detected. Starting form fill process.")
    wait = WebDriverWait(driver, 20)

    try:
        # Step 1: Often Workday has an "Autofill with Resume" option first.
        # It's generally better to use this as it can pre-populate many fields.
        print("Looking for 'Autofill with Resume' option...")
        # Common XPATH for this button.
        autofill_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[@data-automation-id='autofillWithResume']")
        ))
        autofill_button.click()
        print("Clicked 'Autofill with Resume'.")

        # Now, find the file input for the resume.
        resume_input = wait.until(EC.presence_of_element_located(
            # This selector looks for a file input associated with a resume label.
            (By.XPATH, "//input[@type='file' and contains(@aria-label, 'resume')]")
        ))
        resume_input.send_keys(resume_data['resume_path'])
        print(f"Resume uploaded from: {resume_data['resume_path']}")

        # After upload, Workday parses the resume. We need to wait for the 'Next' or 'Continue'
        # button to become clickable, which indicates parsing is done.
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@data-automation-id, 'next')] | //button[contains(@data-automation-id, 'continue')]")
        ))
        print("Workday has likely parsed the resume. Manual review of the following pages is required.")

    except (TimeoutException, NoSuchElementException) as e:
        print(f"Could not complete the initial Workday autofill step. Error: {e}")
        print("The process will require full manual completion from here.")

    # Workday is multi-page. This function would ideally handle only the first page.
    # The agent pauses here for manual review.


def _fill_greenhouse_form(driver, resume_data, application_text):
    """Handles the application process for Greenhouse portals."""
    print("Greenhouse portal detected. Starting form fill process.")
    wait = WebDriverWait(driver, 15)

    try:
        # Greenhouse often uses an iframe. We must switch to it first.
        print("Checking for Greenhouse iframe...")
        iframe = wait.until(EC.presence_of_element_located((By.ID, "grnhse_iframe")))
        driver.switch_to.frame(iframe)
        print("Switched to iframe.")
    except TimeoutException:
        # If no iframe is found, we might be on the main page.
        print("No iframe detected, continuing on main page.")

    try:
        # --- Resume Upload ---
        try:
            print("Looking for resume upload button...")
            # Greenhouse has an "Attach" button that reveals the file input
            attach_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-source='attach']")))
            attach_button.click()
            resume_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
            resume_input.send_keys(resume_data['resume_path'])
            # Wait for the upload to be confirmed (e.g., a "Change" button appears)
            wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Change')]")))
            print(f"Resume uploaded: {os.path.basename(resume_data['resume_path'])}")
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Could not upload resume. This step might need manual intervention. Error: {e}")

        # --- Fill Text Fields ---
        # Note: Greenhouse often auto-fills after resume upload. This code serves as a backup.
        field_map = {
            'first_name': (By.ID, 'first_name'),
            'last_name': (By.ID, 'last_name'),
            'email': (By.ID, 'email'),
            'phone': (By.ID, 'phone'),
        }

        for key, selector in field_map.items():
            try:
                field = driver.find_element(*selector)
                # Only fill if the field is empty after resume parsing
                if not field.get_attribute('value'):
                    print(f"Filling '{key}'...")
                    field.send_keys(resume_data[key])
            except NoSuchElementException:
                print(f"Field '{key}' not found. Skipping.")

        # --- Cover Letter / Additional Info ---
        try:
            print("Looking for cover letter text area...")
            # Selector for the cover letter box. It might have different labels.
            cover_letter_box = driver.find_element(By.ID, "cover_letter_text")
            cover_letter_box.send_keys(application_text)
            print("Pasted AI-generated application text.")
        except NoSuchElementException:
            print("Cover letter text area not found. Skipping.")

    finally:
        # IMPORTANT: Always switch back to the default content when done with an iframe.
        driver.switch_to.default_content()


def _fill_lever_form(driver, resume_data, application_text):
    """Handles the application process for Lever portals."""
    print("Lever portal detected. Starting form fill process.")
    wait = WebDriverWait(driver, 15)

    try:
        # --- Resume Upload ---
        try:
            print("Looking for resume upload input...")
            # Lever forms often have a direct file input.
            resume_input = wait.until(EC.presence_of_element_located((By.NAME, "resume")))
            resume_input.send_keys(resume_data['resume_path'])
            # Wait for confirmation of upload (e.g., the filename appears)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "filename")))
            print(f"Resume uploaded: {os.path.basename(resume_data['resume_path'])}")
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Could not upload resume. This step might need manual intervention. Error: {e}")

        # --- Fill Text Fields ---
        # Lever often uses name attributes for fields.
        field_map = {
            'name': (By.NAME, 'name'),  # Lever often combines first and last name
            'email': (By.NAME, 'email'),
            'phone': (By.NAME, 'phone'),
            'org': (By.NAME, 'org'),  # Current company
            'urls[LinkedIn]': (By.NAME, 'urls[LinkedIn]')
        }

        for key, selector in field_map.items():
            try:
                field = driver.find_element(*selector)
                if not field.get_attribute('value'):
                    print(f"Looking to fill '{key}'...")
                    # Add logic here to map resume_data to these fields if needed.
                    # e.g., if key == 'name': field.send_keys(f"{resume_data['first_name']} {resume_data['last_name']}")
            except NoSuchElementException:
                print(f"Field '{key}' not found. Skipping.")

        # --- Cover Letter / Additional Info ---
        try:
            print("Looking for cover letter/additional info text area...")
            # Lever's text area for cover letter often has the name 'comments'
            comments_box = driver.find_element(By.NAME, "comments")
            comments_box.send_keys(application_text)
            print("Pasted AI-generated application text.")
        except NoSuchElementException:
            print("Cover letter/additional info text area not found. Skipping.")

    except Exception as e:
        print(f"An unexpected error occurred on the Lever form: {e}")


def _fill_generic_form(driver, resume_data, application_text):
    """
    A fallback handler for unknown application portals.
    It attempts to find common fields but will likely require manual completion.
    """
    print("Unknown portal type. Attempting generic field fill.")
    print("WARNING: This is a best-effort attempt. Manual review is highly recommended.")
    wait = WebDriverWait(driver, 10)

    # --- Generic Resume Upload Attempt ---
    try:
        print("Attempting to find a resume file input...")
        # A generic XPath looking for any file input that might be for a resume.
        resume_input = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//input[@type='file' and (contains(@name, 'resume') or contains(@id, 'resume'))]")
        ))
        resume_input.send_keys(resume_data['resume_path'])
        print("Found and filled a potential resume input.")
    except (TimeoutException, NoSuchElementException):
        print("Could not find a standard resume upload input.")

    # --- Generic Text Field Fill Attempt ---
    # Try to find fields based on common name/id attributes.
    generic_field_map = {
        resume_data['first_name']: (By.XPATH, "//*[self::input or self::textarea][contains(@name, 'first_name') or contains(@id, 'first_name')]"),
        resume_data['last_name']: (By.XPATH, "//*[self::input or self::textarea][contains(@name, 'last_name') or contains(@id, 'last_name')]"),
        resume_data['email']: (By.XPATH, "//*[self::input or self::textarea][contains(@name, 'email') or contains(@id, 'email')]"),
        resume_data['phone']: (By.XPATH, "//*[self::input or self::textarea][contains(@name, 'phone') or contains(@id, 'phone')]"),
        application_text: (By.XPATH, "//*[self::textarea][contains(@name, 'cover') or contains(@id, 'cover') or contains(@name, 'comment')]")
    }

    for text_to_fill, selector in generic_field_map.items():
        try:
            field = driver.find_element(*selector)
            if not field.get_attribute('value'):
                print("Found a generic field and filling it.")
                field.send_keys(text_to_fill)
        except NoSuchElementException:
            pass  # Silently skip if not found on a generic page


def start_application(driver, job_url, resume_data, application_text):
    """
    Uses an existing browser session to navigate to the job URL and attempts to fill the application.
    The browser window is left open for manual review, login, and submission.

    Args:
        driver: The active Selenium WebDriver instance.
        job_url (str): The URL of the job application page.
        resume_data (dict): A dictionary containing parsed resume information.
        application_text (str): The AI-generated text for cover letters/summaries.
    """
    # Defensive check for required data
    if not all([driver, job_url, resume_data, application_text]):
        print("Error: Missing driver, job_url, resume_data, or application_text.")
        return

    # This function no longer initializes its own driver. It uses the one passed in.
    # This is the key to waiting for the user: the browser is already open and controlled by the main app.
    try:
        print(f"Navigating to job URL: {job_url}")
        driver.get(job_url)
        time.sleep(3)  # Allow page to settle

        # --- Platform Detection Logic ---
        if "workday" in job_url.lower():
            _fill_workday_form(driver, resume_data, application_text)
        elif "greenhouse.io" in job_url.lower() or "boards.greenhouse.io" in job_url.lower():
            _fill_greenhouse_form(driver, resume_data, application_text)
        elif "lever.co" in job_url.lower():
            _fill_lever_form(driver, resume_data, application_text)
        else:
            _fill_generic_form(driver, resume_data, application_text)

        # --- Final Manual Review Step ---
        print("\n" + "=" * 50)
        print("✅ Automation complete. The form has been pre-filled.")
        print(">>> Please review the application in the browser window. <<<")
        print(">>> You may need to log in or complete a CAPTCHA. <<<")
        print("=" * 50 + "\n")

        # This input will pause the script until the user presses Enter in the console.
        # This is the moment to manually check the form, complete any CAPTCHAs,
        # and fill in any fields the bot missed.
        # By not having an input() and not quitting the driver, we leave the browser open
        # for the user to interact with freely. The user will close it via the Streamlit UI.

    except Exception as e:
        print(f"A critical error occurred during the automation process: {e}")
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

    test_application_text = """As a highly motivated software developer, I am excited by the opportunity to contribute my skills in Python and cloud technologies to your team. My resume highlights my experience in building scalable applications and my dedication to writing clean, efficient code."""

    # Example URL for a Greenhouse application.
    # Replace this with a live URL you want to test.
    test_job_url = "https://boards.greenhouse.io/debricked/jobs/4006096007"

    if not os.path.exists(test_resume_data['resume_path']):
        print("FATAL ERROR: The test resume file was not found at the specified path:")
        print(f"-> {test_resume_data['resume_path']}")
        print("Please ensure the file exists and the path is correct in the `if __name__ == '__main__':` block.")
    else:
        # For direct testing, we now need to initialize a driver first and pass it.
        test_driver = initialize_driver()
        start_application(test_driver, test_job_url, test_resume_data, test_application_text)
        input("--> Test finished. Press Enter in this terminal to close the browser...")
        test_driver.quit()

    print("\n--- Automator Test Finished ---")