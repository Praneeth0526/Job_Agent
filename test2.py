import requests
from bs4 import BeautifulSoup
import pandas as pd

# 1. Define the URL to scrape
# The video explains how to find this URL using the browser's inspector tool [00:01:30]
# This URL is for "python developer" jobs in "Toronto"
# This URL is for "IT and Software" jobs in "India".
url = "https://www.linkedin.com/jobs/search/?keywords=IT%20and%20Software&location=India&geoId=102713980"

# 2. Send a GET request to the URL
response = requests.get(url)

# 3. Parse the HTML content of the page with BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# 4. Find all the job listings
# The video shows how to inspect the page to find the correct tags and classes [00:02:39]
jobs = soup.find_all('div', class_='base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card')

# 5. Create a list to store the job data
job_list = []

# 6. Loop through each job listing to extract the details
for job in jobs:
    # 7. Extract the job title
    # The video demonstrates how to find the specific element for the job title [00:13:08]
    job_title = job.find('h3', class_='base-search-card__title').text.strip()

    # 8. Extract the company name
    # Similarly, the company name is found by inspecting the page [00:08:35]
    company_name = job.find('h4', class_='base-search-card__subtitle').text.strip()

    #extraxt job description
    job_desc = job.find('p',class_='jobs-box__html-content').text.strip()

    # 9. Extract the job location
    job_location = job.find('span', class_='job-search-card__location').text.strip()

    # 10. Extract the link to the job posting
    job_link = job.find('a', class_='base-card__full-link')['href']

    # 11. Store the extracted data in a dictionary
    # The video explains how to use a dictionary to organize the data for each job [00:09:29]
    job_data = {
        'Title': job_title,
        'Company': company_name,
        'Description':job_desc,
        'Location': job_location,
        'Link': job_link
    }

    # 12. Append the dictionary to the list
    job_list.append(job_data)

# 13. Create a pandas DataFrame from the list of dictionaries
# The video shows how to convert the list of jobs into a DataFrame for easy analysis [00:14:34]
df = pd.DataFrame(job_list)

# 14. Save the DataFrame to a CSV file
# The final step is to export the data to a CSV file [00:15:47]
df.to_csv('linkedin_jobs.csv', index=False)

print("Scraping complete. Data saved to linkedin_jobs.csv")