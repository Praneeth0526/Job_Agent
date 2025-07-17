# src/database.py
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


def init_db():
    """
    Creates the 'applications' table if it doesn't already exist.
    This table will store all job data and application statuses.
    """
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
                           criteria
                           TEXT,
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
        print("Database initialized. Table 'applications' is ready.")
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
        # Using INSERT OR IGNORE to prevent errors on duplicate URLs and adding the criteria
        cursor.execute("""
                       INSERT OR IGNORE INTO applications (
                           title, company, location, job_url, criteria, match_score, matched_skills
                       ) VALUES (?, ?, ?, ?, ?, ?, ?)
                       """, (
                           job_data.get('title'),
                           job_data.get('company'),
                           job_data.get('location'),
                           job_data.get('job_url'),
                           job_data.get('criteria'),
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


def update_job_status(job_id, new_status):
    """
    Updates the status of a specific job application.

    Args:
        job_id (int): The unique ID of the job to update.
        new_status (str): The new status (e.g., 'applied', 'interviewing').
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (new_status, job_id))
        conn.commit()
        print(f"Updated job status to '{new_status}' for ID: {job_id}")
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


def get_job_status(job_id):
    """
    Retrieves the status of a specific job.

    Args:
        job_id (int): The unique ID of the job to check.

    Returns:
        str: The status of the job, or None if not found.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM applications WHERE id = ?", (job_id,))
        result = cursor.fetchone()
        return result['status'] if result else None
    except Exception as e:
        print(f"An error occurred while fetching job status for ID {job_id}: {e}")
        return None
    finally:
        conn.close()


def get_all_jobs():
    """Retrieves all jobs from the database."""
    conn = get_db_connection()
    jobs = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications")
        rows = cursor.fetchall()
        for row in rows:
            jobs.append(dict(row))
    except Exception as e:
        print(f"An error occurred while fetching all jobs: {e}")
    finally:
        conn.close()
    return jobs


# --- Execution Example ---

if __name__ == "__main__":
    print("--- Database Management Script ---")
    init_db()
    all_jobs = get_all_jobs()
    print(f"\nTotal jobs in database: {len(all_jobs)}")
    if all_jobs:
        print("Sample job:")
        print(dict(all_jobs[0]))
    print("\n--- Script Finished ---")
