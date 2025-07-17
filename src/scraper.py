# --------------------------------------------------------------------------
# --- AI JOB APPLICATION AGENT - SCRAPER MODULE
# --- Version: 1.2
# --- Description: Implements an intelligent, multi-query scraping strategy
# ---              for LinkedIn based on resume skills and roles.
# --------------------------------------------------------------------------

import time
import urllib.parse
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from src import logger

log = logger.setup_logger()


def _linkedin_login(driver, email, password):
    """Handles LinkedIn login if not already logged in."""
    log.info("Navigating to LinkedIn login page.")
    driver.get("https://www.linkedin.com/login")
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        log.info("Login page loaded. Entering credentials.")
        driver.find_element(By.ID, "username").send_keys(email)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "global-nav-search"))
        )
        log.info("LinkedIn login successful.")
        return True
    except (NoSuchElementException, TimeoutException):
        # It's possible we are already logged in. Check for a key element.
        if "global-nav-search" in driver.page_source:
            log.info("Already logged in.")
            return True
        log.error("LinkedIn login failed.")
        return False


def _get_job_links_from_search_page(driver, search_url):
    """
    Navigates to a search URL, scrolls to load all results, and extracts
    all unique job links from the page.
    """
    log.info(f"Navigating to job search URL: {search_url}")
    driver.get(search_url)

    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "base-card")))
        log.info("Initial job cards loaded.")
    except TimeoutException:
        log.error(f"Job cards not found on page: {search_url}")
        return []

    log.info("Scrolling to load all job listings...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for new jobs to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    log.info("Extracting job links from search page...")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    link_elements = soup.find_all('a', class_='base-card__full-link')
    job_links = {link['href'] for link in link_elements if 'href' in link.attrs}  # Use a set for automatic deduplication
    return list(job_links)


def _scrape_single_job_page(driver, job_url):
    """
    Visits a single job URL and scrapes the title, company, location,
    and full job description.
    """
    log.info(f"Scraping job page: {job_url}")
    driver.get(job_url)
    try:
        # Wait for the main description container to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "show-more-less-html"))
        )

        # Click the "show more" button to expand the description
        try:
            see_more_button = driver.find_element(By.CLASS_NAME, 'show-more-less-html__button')
            driver.execute_script("arguments[0].click();", see_more_button)
            time.sleep(1)  # Wait for content to expand
        except NoSuchElementException:
            log.debug("No 'show more' button found, description is likely short.")
            pass

        # Parse the page with the full description
        job_soup = BeautifulSoup(driver.page_source, 'html.parser')

        # --- Extract data ---
        job_title = job_soup.find('h1', class_='top-card-layout__title').get_text(strip=True)
        company_name = job_soup.find('a', class_='topcard__org-name-link').get_text(strip=True)
        location = job_soup.find('span', class_='topcard__flavor--bullet').get_text(strip=True)
        description_div = job_soup.find('div', class_='show-more-less-html__markup')
        # Get the full HTML for analysis and the plain text for display/matching
        job_description_html = str(description_div) if description_div else "Not found"

        return {
            "title": job_title,
            "company": company_name,
            "location": location,
            "criteria": job_description_html,
            "link": job_url
        }
    except Exception as e:
        log.error(f"Could not scrape {job_url}. Error: {e}")
        return None


def run_scraper(driver, resume_skills, location, email, password, additional_keywords=""):
    """
    Main scraper function. Logs into LinkedIn, constructs intelligent search
    queries from resume skills, scrapes multiple search pages, and visits
    each unique job link to get full details.
    """
    log.info("Starting intelligent LinkedIn scraper...")
    # --- 1. Login ---
    driver.get("https://www.linkedin.com/feed/")
    if "feed" not in driver.current_url:
        log.warning("Not on feed page, attempting login.")
        if not _linkedin_login(driver, email, password):
            log.error("LinkedIn login failed. Aborting scrape.")
            return []

    # --- 2. Construct Search Queries ---
    # Use top 5 skills from resume for focused search
    top_skills = list(resume_skills)[:5]
    skill_query_part = " OR ".join([f'"{s}"' for s in top_skills])

    base_queries = [
        f'({skill_query_part}) AND (Intern OR Internship)',
        '("Software Engineer" OR "Computer Science Engineer" OR "IT" OR "Software Developer") AND (Intern OR Internship)',
        skill_query_part
    ]

    # Add any user-provided keywords to all queries
    if additional_keywords:
        final_queries = [f'({q}) AND ("{additional_keywords}")' for q in base_queries]
    else:
        final_queries = base_queries

    # --- 3. Scrape links from all search queries ---
    all_job_links = set()
    for query in final_queries:
        log.info(f"Searching for: {query}")
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}&location={location}&f_WT=2"
        links_from_page = _get_job_links_from_search_page(driver, search_url)
        if links_from_page:
            log.info(f"Found {len(links_from_page)} links for this query.")
            all_job_links.update(links_from_page)

    if not all_job_links:
        log.warning("No job links found across all search queries.")
        return []

    log.info(f"Found {len(all_job_links)} unique job links in total. Now scraping details...")

    # --- 4. Visit each unique link and scrape the details ---
    final_jobs = []
    # --- FOR TESTING: Limit the number of jobs to scrape ---
    for i, link in enumerate(list(all_job_links)): # Original line
    # for i, link in enumerate(list(all_job_links)[:10]): # Test with only 10 jobs
        log.info(f"Processing link {i+1}/{len(list(all_job_links)[:])}")
        job_data = _scrape_single_job_page(driver, link)
        if job_data:
            final_jobs.append(job_data)
        time.sleep(1)  # Be respectful to LinkedIn's servers

    # --- 5. Return results ---
    log.info(f"Successfully scraped details for {len(final_jobs)} jobs.")
    return final_jobs