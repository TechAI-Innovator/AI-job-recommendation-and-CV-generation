# 💼 Job Recommendation & Automated CV Generation System

An AI-powered job platform that helps job seekers **find better jobs faster** by providing **personalized job recommendations** and **automatically generated tailored CVs** using LLMs (Large Language Models).

![Platform Preview](assets/preview-placeholder.jpg)

🎥 **Watch How It Works**  
[![Watch Video](assets/video-thumbnail.jpg)](https://your-video-link.com)

🌐 **Live Demo**  
👉 [https://ai-job-recommendation-and-cv-generation.onrender.com](https://ai-job-recommendation-and-cv-generation.onrender.com)

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

## 🧠 Advanced Logic

- ⚠️ **LLM Quota Awareness**  
  Detects and handles AI model rate limits. Informs users and pauses scraping/generation if the limit is exceeded.

- 🔁 **Duplicate Job Prevention**  
  Prevents saving duplicate jobs by checking:
  - Job URLs
  - Content hashes (title, company, location, description)

- 🧪 **Testing Limit for Users**  
  Users can only receive a maximum of **2 job recommendations**.  
  > “This system is currently in testing mode and not deployed for large-scale use.”

- ❌ **Incomplete Input Handling**  
  Gracefully alerts users if they’ve skipped required fields like preferred job titles or location.

---

## 🧪 Use Case

> "A recent graduate uploads their resume, sets preferences for job roles, and receives a curated list of job links where their **skills, experience, and career goals match the job descriptions** — along with **automatically generated, tailored CVs** — all in minutes."

---

## 🧰 Tech Stack

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

## 📂 Folder Structure

├── app.py # Main Flask application
├── auth.py # Authentication logic
├── cv_handler.py # CV parsing and generation
├── db.py # DB connection & helpers
├── engine.py # Scraping and matching logic
├── models.py # SQLAlchemy models
├── utils.py # Utility functions
├── requirements.txt # Dependencies
├── alembic.ini # Alembic config
├── LICENSE
├── README.md
├── .gitattributes
│
├── migrations/ # Alembic files
├── static/ # CSS, JS, assets
└── templates/ # Jinja2 templates

---

## 👤 Author

**Ayomide Oluwanifesimi**  
🧑‍💻 Full Stack Developer | AI Developer
📧 Email: your.email@example.com  
🔗 LinkedIn: [linkedin.com/in/yourprofile](https://linkedin.com/in/yourprofile)  
🐙 GitHub: [github.com/yourusername](https://github.com/yourusername)

---

## 🛡️ Project Status

- ✅ MVP completed
- 🧠 LLM logic + job matching live
- 🧪 Currently running in **testing mode** (limited scraping & AI quota)

---

## 📃 License

This project is licensed under the MIT License.