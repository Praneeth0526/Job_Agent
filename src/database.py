# main_database.py
import sqlite3
import os

# --- Configuration ---
DB_FILE = "job_applications.db"


# --- Database Functions ---

def get_db_connection():
    """
    Establishes a connection to the SQLite database.
    Creates the database file if it doesn't exist.
    """
    conn = sqlite3.connect(DB_FILE)
    # This allows us to access columns by name
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    """
    Creates the 'applications' table if it doesn't already exist.
    This table will store all job data and application statuses.
    """
    print("Ensuring database table exists...")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS applications
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           title
                           TEXT
                           NOT
                           NULL,
                           company
                           TEXT
                           NOT
                           NULL,
                           location
                           TEXT,
                           job_url
                           TEXT
                           UNIQUE,
                           status
                           TEXT
                           NOT
                           NULL
                           DEFAULT
                           'found',
                           match_score
                           INTEGER
                           DEFAULT
                           0,
                           matched_skills
                           TEXT,
                           found_date
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       ''')
        conn.commit()
        print("Table 'applications' is ready.")
    except Exception as e:
        print(f"An error occurred while creating the table: {e}")
    finally:
        conn.close()


def add_job(job_data):
    """
    Adds a new job to the database.
    It ignores jobs that are already present based on the unique job_url.

    Args:
        job_data (dict): A dictionary containing job details.
                         Must include 'title', 'company', and 'job_url'.

    Returns:
        bool: True if a new row was inserted, False otherwise.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Using INSERT OR IGNORE to prevent errors on duplicate URLs
        cursor.execute('''
                       INSERT
                       OR IGNORE INTO applications (title, company, location, job_url, match_score, matched_skills)
            VALUES (?, ?, ?, ?, ?, ?)
                       ''', (
                           job_data.get('title'),
                           job_data.get('company'),
                           job_data.get('location'),
                           job_data.get('job_url'),  # Assuming the scraper can get a unique URL
                           job_data.get('match_score', 0),
                           ', '.join(job_data.get('matched_skills', []))
                       ))
        conn.commit()
        # cursor.rowcount will be 1 if a row was inserted, 0 if it was ignored.
        return cursor.rowcount > 0
    except Exception as e:
        print(f"An error occurred while adding a job: {e}")
        return False
    finally:
        conn.close()


def update_job_status(job_url, new_status):
    """
    Updates the status of a specific job application.

    Args:
        job_url (str): The unique URL of the job to update.
        new_status (str): The new status (e.g., 'applied', 'interviewing').
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE applications SET status = ? WHERE job_url = ?", (new_status, job_url))
        conn.commit()
        print(f"Updated job status to '{new_status}' for URL: {job_url}")
    except Exception as e:
        print(f"An error occurred while updating job status: {e}")
    finally:
        conn.close()


def get_jobs_by_status(status="found"):
    """
    Retrieves all jobs from the database that have a specific status.

    Args:
        status (str): The status to filter by.

    Returns:
        list: A list of job dictionaries.
    """
    conn = get_db_connection()
    jobs = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE status = ?", (status,))
        rows = cursor.fetchall()
        # Convert sqlite.Row objects to standard dictionaries
        for row in rows:
            jobs.append(dict(row))
    except Exception as e:
        print(f"An error occurred while fetching jobs: {e}")
    finally:
        conn.close()
    return jobs


def get_job_status(job_url):
    """
    Retrieves the status of a specific job.

    Args:
        job_url (str): The unique URL of the job to check.

    Returns:
        str: The status of the job, or None if not found.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM applications WHERE job_url = ?", (job_url,))
        result = cursor.fetchone()
        return result['status'] if result else None
    except Exception as e:
        print(f"An error occurred while fetching job status: {e}")
        return None
    finally:
        conn.close()


def get_all_jobs():
    """Retrieves all jobs from the database, regardless of status."""
    return get_jobs_by_status(status='%') # Use SQL wildcard to match any status


# --- Execution Example ---

if __name__ == "__main__":
    print("--- Database Management Script ---")

    # 1. Initialize the database and table
    create_table()

    # 2. Add some example jobs (as if they were scraped)
    print("\nAdding some example jobs...")
    example_jobs = [
        {'title': 'Senior Python Developer', 'company': 'Tech Solutions Inc.', 'location': 'Remote',
         'job_url': 'https://example.com/job/1', 'match_score': 3, 'matched_skills': ['python', 'api', 'aws']},
        {'title': 'Data Analyst', 'company': 'Data Corp', 'location': 'New York, NY',
         'job_url': 'https://example.com/job/2', 'match_score': 2, 'matched_skills': ['sql', 'data analysis']},
        {'title': 'Junior Python Dev', 'company': 'Tech Solutions Inc.', 'location': 'Remote',
         'job_url': 'https://example.com/job/3', 'match_score': 1, 'matched_skills': ['python']}
    ]
    for job in example_jobs:
        add_job(job)
    print("Example jobs added (or ignored if already present).")

    # 3. Retrieve jobs that are newly 'found'
    print("\nFetching jobs with status 'found':")
    found_jobs = get_jobs_by_status("found")
    for job in found_jobs:
        print(f"  - {job['title']} at {job['company']} (Score: {job['match_score']})")

    # 4. Update the status of one of the jobs
    if found_jobs:
        print("\nUpdating status for the first job to 'applied'...")
        first_job_url = found_jobs[0]['job_url']
        update_job_status(first_job_url, 'applied')

    # 5. Retrieve jobs again to see the change
    print("\nFetching 'found' jobs again:")
    newly_found_jobs = get_jobs_by_status("found")
    print(f"  Found {len(newly_found_jobs)} jobs with status 'found'.")

    print("\nFetching 'applied' jobs:")
    applied_jobs = get_jobs_by_status("applied")
    for job in applied_jobs:
        print(f"  - {job['title']} at {job['company']} is now marked as applied.")

    print("\n--- Script Finished ---")
