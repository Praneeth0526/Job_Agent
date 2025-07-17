# AI Job Application Agent

![AI Job Application Agent In Action](https://i.imgur.com/c7974c.png)  
*Focusing on LinkedIn, Indeed, and Direct Company Portals for the Indian Tech Market.*

An intelligent, autonomous agent that automates the entire job application process—from finding relevant openings based on your resume to assisting with the application itself.

---

## ► Key Features

- **📄 Resume-Driven Job Search:** Parses your resume to extract key technical skills and uses them to generate dynamic, relevant search queries.
- **🤖 AI-Powered Job Matching:** Employs a relevance scoring algorithm to rank job openings based on how well they match the skills in your resume.
- **✨ Gemini-Powered Insights:** Uses Google's Gemini to generate custom "talking points" and tailored application summaries for each job, highlighting your strengths.
- **⚙️ Multi-Platform Automation:** Built with a modular framework (using Selenium) to handle applications across different platforms like LinkedIn, Workday, and Greenhouse.
- **✅ Interactive UI:** A user-friendly interface built with Streamlit that allows you to review, approve, or reject jobs, giving you full control over the application process.
- **🗄️ Persistent Job Tracking:** Uses a local SQLite database to store and manage the status of all job applications (`found`, `applying`, `rejected`, `applied`).

---

## ► How It Works

The agent follows a sophisticated, multi-step process to streamline your job hunt:

1. **Resume Parsing:** You upload your resume, and the agent's parser (`src/parser.py`) extracts your technical skills.  
2. **Automated Scraping:** The Selenium-based scraper (`src/scraper.py`) launches a browser, navigates to job boards, and uses your skills to find hundreds of relevant job listings.  
3. **Relevance Scoring & Storing:** Each job is scored by the `src/matcher.py` based on skill overlap in the title and description. All jobs are then saved to a local SQLite database (`job_applications.db`).  
4. **Interactive Review:** The Streamlit UI (`app.py`) displays the found jobs as interactive cards. You have full control to:  
    - **View Job Criteria:** See the full job description.  
    - **Get AI Insights:** Generate a custom summary of how your skills match the job.  
    - **Reject:** Dismiss the job from your queue.  
    - **Approve & Apply:** Move the job to the application stage.  
5. **AI-Assisted Application:** When you approve a job, the agent uses Gemini (`src/llm_helper.py`) to craft tailored text for your application.  
6. **Browser Automation:** The automation module (`src/automator.py`) takes over, opens the job link in its own browser, and can assist in filling out the application fields on your behalf for your final review and submission.

---

## ► Tech Stack

- **Backend & Automation:** Python, Selenium WebDriver  
- **Frontend / UI:** Streamlit  
- **AI & Language Model:** Google Gemini  
- **Data Storage:** SQLite, Pandas  
- **Parsing:** BeautifulSoup, PyMuPDF (for PDFs)

---

## ► Setup and Installation

Get the agent running on your local machine in a few simple steps.

**1. Clone the Repository:**
```bash
git clone https://github.com/Praneeth0526/Job_Agent.git
cd Job_Agent
```

**2. Create a Virtual Environment (Recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scriptsctivate`
```

**3. Install Dependencies:**
```bash
pip install -r requirements.txt
```

**4. Set Up Your API Key:**
- Create a file named `.env` in the root directory of the project.
- Open the `.env` file and add your Google Gemini API key:
```
GEMINI_API_KEY=your_actual_api_key_goes_here
```

**5. Install WebDriver:**
- Download the appropriate [WebDriver](https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/) for your browser (e.g., `chromedriver` for Google Chrome).
- Ensure the WebDriver executable is placed in a directory that is included in your system's `PATH`.

---

## ► Usage

**1. Place Your Resume:**
- Add your resume PDF to the `Resume/` directory.

**2. Run the Streamlit App:**
```bash
streamlit run app.py
```
- The application will open in a new browser tab.

**3. Start the Agent:**
- In the Streamlit UI, confirm the path to your resume.
- Click the **"Fetch & Rank Jobs"** button to start the scraping process.
- Review and manage the jobs found directly from the UI.

---

## ► Project Structure

The repository is organized to be modular and scalable:

```
Job_Agent/
├── Resume/
│   └── New_resume.pdf         # Your resume file
├── src/
│   ├── automator.py           # Selenium logic for applying to jobs
│   ├── database.py            # SQLite database management
│   ├── llm_helper.py          # Gemini API integration and prompts
│   ├── matcher.py             # Job-to-resume relevance scoring
│   ├── parser.py              # Resume and job description parsing
│   └── scraper.py             # Web scraping logic
├── .env                       # Stores your API keys (create this yourself)
├── app.py                     # The main Streamlit application file
├── job_applications.db        # Local SQLite database (auto-generated)
└── requirements.txt           # Project dependencies
```

---

## ► Roadmap & Future Enhancements

This project has a strong foundation with many exciting possibilities for future development:

- [ ] **Full End-to-End Application:** Complete the final "submit" step in the automation script.
- [ ] **Advanced Platform Adapters:** Build out more robust logic in `automator.py` for specific platforms like Workday and Lever.
- [ ] **GUI-based Field Mapping:** Create a UI where users can visually map their resume details (like "First Name," "Email") to form field IDs on different job sites.
- [ ] **Chrome Extension:** Develop a companion Chrome extension to trigger the agent directly from a job posting page.
- [ ] **Cloud Deployment:** Deploy the Streamlit app to a service like Heroku or Streamlit Community Cloud for public access.

---

## ► Contributing

Contributions, issues, and feature requests are welcome!  
Feel free to check the [issues page](https://github.com/Praneeth0526/Job_Agent/issues).

---

## ► License

This project is licensed under the Apache-2.0 License. See the `LICENSE` file for details.
