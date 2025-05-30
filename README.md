# 💼 Job Recommendation & Automated CV Generation System

An AI-powered job platform that helps job seekers **find better jobs faster** by providing **personalized job recommendations** and **automatically generated tailored CVs** using LLMs (Large Language Models).

![Platform Preview](assets/preview-placeholder.jpg)

🎥 **Watch How It Works**  
[![Watch Video](assets/video-thumbnail.jpg)](https://your-video-link.com)

---

## 🚀 Features

- 🔍 **Smart Job Matching**  
  Matches users to jobs based on their **skills, experience, and preferences**, intelligently analyzing **job descriptions** to ensure real alignment — not just keyword overlap.

- 📝 **Automated CV Generation**  
  Generates job-specific CVs using user data, GitHub, LinkedIn, and project experience.

- 📥 **CV Parser**  
  Parses uploaded resumes to auto-fill user profiles with education, experience, and skills.

- 📊 **Dynamic Dashboard**  
  View recommended jobs with key details, apply instantly, and track applications.

- ⚙️ **User Profile Management**  
  Easily update personal details, education, experience, and job preferences.

- 🌐 **Live Job Scraping**  
  Scrapes job boards like **LinkedIn**, **Indeed**, and **Jobberman** using real-time filters based on user preferences.

- 📎 **Download Tailored CVs**  
  Get a ready-to-send, optimized CV for every recommended job — tailored to the job’s requirements.

---

## 🧠 Tech Stack

| Layer      | Tech                                 |
|------------|--------------------------------------|
| Frontend   | HTML, CSS, JavaScript                |
| Backend    | Python, Flask                        |
| AI / NLP   | Groks LLaMA, LangChain               |
| Scraping   | BeautifulSoup                        |
| CV Builder | Python-docx, ReportLab               |
| Database   | PostgreSQL                           |
| Hosting    | Render                               |

---

## 📌 Use Case

> "A recent graduate uploads their resume, sets preferences for job roles, and receives a curated list of job links where their **skills, experience, and career goals match the job descriptions** — along with **automatically generated, tailored CVs** — all in minutes."

---

## 🛡️ Project Status

- ✅ MVP in progress  
- 🛠️ Scraping + Matching Logic Under Development  
- 🔐 Login & Profile Sync Coming Soon

---

## 📂 Folder Structure

├── app.py # Main Flask application
├── auth.py # Authentication routes and logic
├── cv_handler.py # CV parsing and generation logic
├── db.py # Database connection and helpers
├── engine.py # Job scraping and matching engine
├── models.py # SQLAlchemy models
├── utils.py # Utility functions
├── requirements.txt # Python dependencies
├── alembic.ini # Alembic migration config
├── LICENSE
├── README.md
├── .gitattributes
│
├── migrations/ # Alembic migration files
├── static/ # Static frontend files (CSS, JS, images)
└── templates/ # HTML templates (Jinja2)
