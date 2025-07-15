import requests
from bs4 import BeautifulSoup
#static scraper
def scrape_company_jobs(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    jobs = []
    for job_elem in soup.find_all("div", class_="job-listing"):
        title = job_elem.find("h2").text.strip()
        location = job_elem.find("span", class_="location").text.strip()
        jobs.append({"title": title, "location": location})
    return jobs
#dynamic scraper
from selenium import webdriver
from selenium.webdriver.common.by import By

def scrape_dynamic_portal(url, username, password):
    driver = webdriver.Chrome()  # Ensure ChromeDriver is installed
    driver.get(url)
    # Example login (adjust selectors as needed)
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "login-button").click()
    # After login, navigate and extract job data
    jobs = []
    job_elements = driver.find_elements(By.CLASS_NAME, "job-listing")
    for elem in job_elements:
        title = elem.find_element(By.TAG_NAME, "h2").text
        location = elem.find_element(By.CLASS_NAME, "location").text
        jobs.append({"title": title, "location": location})
    driver.quit()
    return jobs

from scraper import scrape_company_jobs

if __name__ == "__main__":
    url = "https://www.linkedin.com/"
    jobs = scrape_company_jobs(url)
    for job in jobs:
        print(f"{job['title']} - {job['location']}")

import json

def save_jobs_to_json(jobs, filename):
    with open('Jobs.txt', "w") as f:
        json.dump(jobs, f, indent=2)
