# src/automator.py
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# --- Constants ---
# This path is used to create a dedicated Chrome profile for the bot.
CHROME_PROFILE_PATH = "user-data-dir=chrome_profile_for_job_agent"

SELECTORS = {
    "workday": {
        "apply_button": (By.XPATH, "//a[contains(@data-automation-id, 'apply')]"),
        "autofill_option": (By.XPATH, "//div[contains(@data-automation-id, 'autofillWithResume')] | //a[contains(@data-automation-id, 'autofillWithResume')]"),
        "resume_input": (By.XPATH, "//input[@type='file' and contains(@aria-label, 'resume')]"),
        "next_button": (By.XPATH, "//button[contains(@data-automation-id, 'next')] | //button[contains(@data-automation-id, 'continue')]")
    },
    "greenhouse": {
        "iframe": (By.ID, "grnhse_iframe"),
        "form_field": (By.ID, "first_name"),
        "attach_button": (By.CSS_SELECTOR, "[data-source='attach']"),
        "resume_input": (By.CSS_SELECTOR, "input[type='file']"),
        "upload_confirmation": (By.XPATH, "//button[contains(text(), 'Change')]")
    },
    "lever": {
        "apply_button": (By.CLASS_NAME, "postings-btn"),
        "resume_input": (By.NAME, "resume"),
        "upload_confirmation": (By.CLASS_NAME, "filename")
    }
}


class StatusUpdater:
    """A default, print-based status updater for non-UI testing."""

    def info(self, message): print(f"INFO: {message}")
    def success(self, message): print(f"SUCCESS: {message}")
    def error(self, message, e=None): print(f"ERROR: {message}{(' - ' + str(e)) if e else ''}")
    def warning(self, message): print(f"WARNING: {message}")
    def image(self, path): print(f"IMAGE: An image was saved to {path}")


def initialize_driver():
    """Creates and returns a Selenium WebDriver instance with a persistent profile."""
    options = webdriver.ChromeOptions()
    options.add_argument(CHROME_PROFILE_PATH)
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    # You can add --headless if you don't want the browser window to show up
    # options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def apply_on_workday(driver, resume_path, status_updater):
    """Handles the application process for Workday portals."""
    try:
        status_updater.info("Workday portal detected. Starting automation...")
        wait = WebDriverWait(driver, 20)

        apply_button = wait.until(EC.element_to_be_clickable(SELECTORS["workday"]["apply_button"]))
        apply_button.click()

        wait.until(EC.any_of(
            EC.element_to_be_clickable(SELECTORS["workday"]["autofill_option"]),
            EC.presence_of_element_located(SELECTORS["workday"]["resume_input"])
        ))

        file_input = driver.find_element(*SELECTORS["workday"]["resume_input"])
        file_input.send_keys(resume_path)

        status_updater.success("Resume submitted to Workday for autofill.")
        status_updater.info("Waiting for resume parsing to complete...")

        wait.until(EC.element_to_be_clickable(SELECTORS["workday"]["next_button"]))

        status_updater.warning("Please review the auto-filled fields and proceed through the next steps manually.")
        return True

    except Exception as e:
        status_updater.error("Error during Workday automation. Manual application required.", e)
        error_path = "workday_error.png"
        driver.save_screenshot(error_path)
        status_updater.image(error_path)
        return False


def apply_on_greenhouse(driver, resume_path, status_updater):
    """Handles the application process for Greenhouse portals."""
    try:
        status_updater.info("Greenhouse portal detected. Starting automation...")
        wait = WebDriverWait(driver, 15)

        try:
            iframe = wait.until(EC.presence_of_element_located(SELECTORS["greenhouse"]["iframe"]))
            driver.switch_to.frame(iframe)
            status_updater.info("Switched to Greenhouse iframe.")
        except TimeoutException:
            status_updater.info("No iframe detected, continuing on main page.")

        wait.until(EC.presence_of_element_located(SELECTORS["greenhouse"]["form_field"]))
        attach_button = driver.find_element(*SELECTORS["greenhouse"]["attach_button"])
        attach_button.click()
        resume_input = wait.until(EC.presence_of_element_located(SELECTORS["greenhouse"]["resume_input"]))
        resume_input.send_keys(resume_path)
        wait.until(EC.presence_of_element_located(SELECTORS["greenhouse"]["upload_confirmation"]))

        status_updater.success("Resume attached successfully on Greenhouse!")
        status_updater.warning("Please fill any remaining fields and submit manually.")
        return True

    except Exception as e:
        status_updater.error("Error during Greenhouse automation. Manual application required.", e)
        error_path = "greenhouse_error.png"
        driver.save_screenshot(error_path)
        status_updater.image(error_path)
        return False
    finally:
        driver.switch_to.default_content()


def apply_on_lever(driver, resume_path, status_updater):
    """Handles the application process for Lever portals."""
    try:
        status_updater.info("Lever portal detected. Starting automation...")
        wait = WebDriverWait(driver, 15)
        apply_button = wait.until(EC.element_to_be_clickable(SELECTORS["lever"]["apply_button"]))
        apply_button.click()
        resume_input = wait.until(EC.presence_of_element_located(SELECTORS["lever"]["resume_input"]))
        resume_input.send_keys(resume_path)
        wait.until(EC.presence_of_element_located(SELECTORS["lever"]["upload_confirmation"]))

        status_updater.success("Resume attached successfully on Lever!")
        status_updater.warning("Please fill any remaining fields and submit manually.")
        return True

    except Exception as e:
        status_updater.error("Error during Lever automation. Manual application required.", e)
        error_path = "lever_error.png"
        driver.save_screenshot(error_path)
        status_updater.image(error_path)
        return False


def automate_application(driver, job, resume_path, status_updater):
    """Main router to delegate application automation to the correct handler."""
    status_updater.info(f"Attempting to automate application for: **{job.get('title')}**")
    job_url = job.get('link')
    if not job_url:
        status_updater.error("Job URL not found. Cannot apply.")
        return

    driver.get(job_url)
    status_updater.success(f"Navigated to job page: {job_url}")
    time.sleep(2)

    try:
        if "workday" in job_url:
            apply_on_workday(driver, resume_path, status_updater)
        elif "greenhouse" in job_url:
            apply_on_greenhouse(driver, resume_path, status_updater)
        elif "lever.co" in job_url:
            apply_on_lever(driver, resume_path, status_updater)
        else:
            status_updater.warning("Unknown career portal. Please apply manually on the opened page.")
            return

    except Exception as e:
        status_updater.error("A critical error occurred during the automation routing.", e)