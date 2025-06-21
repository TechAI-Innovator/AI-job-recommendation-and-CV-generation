from engine import get_db
import random
from models import User
import requests
import base64
from langchain.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.runnables import Runnable
from langchain.schema.output_parser import StrOutputParser
import ast
from models import JobRecommendation
import time
from tqdm import tqdm
from bs4 import BeautifulSoup
import logging
import json
import re
from urllib.parse import urlencode
from flask import flash
import hashlib


# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Load environment and initialize LLM ---
load_dotenv()
COMPARING_GROQ_API_KEY = os.getenv("COMPARING_GROQ_API_KEY")
MATCHING_GROQ_API_KEY = os.getenv("MATCHING_GROQ_API_KEY")

# Initialize Groq model
comparing_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    max_tokens=1000,
    timeout=30,
    max_retries=2,
    api_key=COMPARING_GROQ_API_KEY
)

matching_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    max_tokens=1000,
    timeout=30,
    max_retries=2,
    api_key=MATCHING_GROQ_API_KEY
)

# List of user-agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
    # Add more as needed
]

preferences = [
    "skills", "preferred_industries", "experience", "job_keywords",
    "github", "linkedin", "preferred_titles", "summary", "location_worktype_map",
    "min_salary", "employment_type", "education", "experience_level"
]

# Mapping from user-friendly terms to LinkedIn parameter codes
LINKEDIN_CODES = {
    "work_type": {
        "on-site": "1",
        "remote": "2",
        "hybrid": "3"
    },
    "experience": {
        "intern": "1",
        "entry": "2",
        "mid": "3",
        "senior": "4",
        "manager": "5"
    },
    "job_type": {
        "fulltime": "F",
        "parttime": "P",
        "contract": "C",
        "internship": "I"
    }
}

def get_headers():
    return {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15"
        ]),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }


def generate_job_hash(title, company, location, description):
    # Normalize fields and strip excessive whitespace
    normalized = f"{title.strip().lower()}|{company.strip().lower()}|{location.strip().lower()}|{description.strip().lower()}"
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def get_user_preferences(user_id):
    try:
        db = next(get_db())
        user = db.get(User, user_id)
        db.close()
    except Exception as e:
        print(f"[ERROR] DB error getting user preferences: {e}")
        return None

    if user:
        user_dict = {pref: getattr(user, pref, None) for pref in preferences}
        return user_dict
    else:
        print("[ERROR] User not found in database.")
        return None
    
def preprocess_comma_separated_field(field_str):
    if not field_str:
        return []

    # Split on commas, strip whitespace, remove empty entries
    items = [re.sub(r'\s+', ' ', item.strip()) for item in field_str.split(',')]
    return [item for item in items if item]  # remove blanks

def get_normalized_title_and_keywords(raw_title: str, llm, state: dict) -> str | None:
    prompt_template = ChatPromptTemplate.from_messages([
        ("system",
         "You are a career assistant helping job seekers with the right job roles.\n"
         "User provides job title\n"
         "1. Normalize the title into a proper professional job title.\n"
         "2. For the normalized title, generate 2-5 relevant keywords that would help generate linkedin link for job listings.\n"
         "3. Return only the result as a string, no other instructions as this would be parsed directly into another python code e.g Web Developer, JavaScript, HTML/CSS, Front-end Development"),

        ("user",
         "This is the raw title:\n{raw_title}")
    ])

    chain: Runnable = prompt_template | llm | StrOutputParser()
    try:
        result = chain.invoke({"raw_title": raw_title})
        return result
    except Exception as e:
        logger.error(f"LLM failed to process title '{raw_title}': {e}")
        if "quota" in str(e).lower() or "limit" in str(e).lower():
            state["llm_limit_exceeded"] = True
        return None

def generate_linkedin_urls(user_preferences, state: dict):
    base_url = "https://www.linkedin.com/jobs/search?"

    titles = preprocess_comma_separated_field(user_preferences.get("preferred_titles", ""))
    location_worktypes = user_preferences.get("location_worktype_map", {})
    experience = user_preferences.get("experience_level", "").lower()
    emp_type = user_preferences.get("employment_type", "").lower()
            
    urls = []

    for title in titles:
        if state.get("llm_limit_exceeded"):
            break
        normalized_title_and_keywords = get_normalized_title_and_keywords(title, matching_llm, state)
        for location, worktypes in location_worktypes.items():
            for wt in worktypes:

                wt_code = LINKEDIN_CODES.get("work_type", {}).get(wt.lower())
                exp_code = LINKEDIN_CODES.get("experience", {}).get(experience)
                emp_code = LINKEDIN_CODES.get("job_type", {}).get(emp_type)

                if not wt_code or not exp_code or not emp_code:
                    print(f"Skipping due to missing code: wt={wt_code}, exp={exp_code}, emp={emp_code}")
                    continue

                params = {
                    "keywords": normalized_title_and_keywords.lower(),
                    "location": location,
                    "f_WT": wt_code,
                    "f_E": exp_code,
                    "f_JT": emp_code,
                    "start": ""
                }
                url = base_url + urlencode(params, doseq=True)
                urls.append(url)

    return urls

def get_user_projects_with_readmes(github_username):
    if not github_username:
        msg = "No GitHub username provided."
        logger.warning(msg)
        return [], msg

    repos_url = f"https://api.github.com/users/{github_username}/repos"

    try:
        repos_response = requests.get(repos_url)
        if repos_response.status_code != 200:
            msg = f"GitHub user '{github_username}' not found."
            logger.warning(msg)
            return [], msg

        repos = repos_response.json()
        if not isinstance(repos, list):
            msg = "Unexpected response from GitHub."
            logger.error(msg)
            return [], msg

        projects = []
        for repo in repos:
            readme_url = f"https://api.github.com/repos/{github_username}/{repo['name']}/readme"
            readme_response = requests.get(readme_url)

            content = "No README available."
            if readme_response.status_code == 200:
                readme_data = readme_response.json()
                content_encoded = readme_data.get("content", "")
                if content_encoded:
                    content = base64.b64decode(content_encoded).decode("utf-8", errors="ignore")

            projects.append({
                "name": repo["name"],
                "url": repo["html_url"],
                "readme": content.strip()
            })

        return projects, f"Fetched {len(projects)} project(s) for '{github_username}'."

    except Exception as e:
        msg = "An error occurred while fetching GitHub data."
        logger.error(f"{msg} GitHub fetch error for user '{github_username}': {e}")
        return [], msg
    
def compare_social_to_database(user_details, user_github_repo, state: dict):
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", 
         "You are a user detail perfector using the user's database details and github repositories.\n"
         "What you should do:\n"
         "1. Check through the users database details.\n"
         "2. Check through the user's github repositories.\n"
         "3. Compare to see details that are the same and those completely different.\n"
         "4. Compare and see details that could be merged together.\n"
         "5. Formulate the details back including all the possible details (fully detailed enough to compare with a job description), neatly removing redundancy and not repeating the same project coming from the database and github projects.\n"
         "6. Give me back in dictionary format the way they came from the database.\n"
         "Note: Ensure no additional information or instruction is included as the result is to be used in a python code in that dictionary format."),

        ("user",
         "These are the user's details from database:\n{user_details}\n\n"
         "These are the user's projects from github repositories:\n{user_github_repo}\n\n"),
    ])

    chain: Runnable = prompt_template | comparing_llm | StrOutputParser()
    try:
        result = chain.invoke({
            "user_details": user_details, 
            "user_github_repo": user_github_repo}).strip()
        
        # === CLEANUP with REGEX ===
        result_cleaned = re.sub(r"[\n\r\\]+", "", result)       # remove line breaks and stray backslashes
        result_cleaned = re.sub(r"\s+", " ", result_cleaned)    # collapse excessive whitespace
        result_cleaned = re.sub(r",\s*}", "}", result_cleaned)  # remove trailing commas before closing brace
        result_cleaned = re.sub(r",\s*]", "]", result_cleaned)  # remove trailing commas in lists

        cleaned_result = ast.literal_eval(result_cleaned)
        return cleaned_result 
    
    except Exception as e:
        logger.error(f"LLM comparison failed: {e}")
        if "quota" in str(e).lower() or "limit" in str(e).lower():
            state["llm_limit_exceeded"] = True
        return False

def each_link_extractor(link):
    try:
        job_page = requests.get(link, headers=get_headers(), timeout=10)
        soup = BeautifulSoup(job_page.content, "html.parser")

        # ---------- Basic Job Info ----------
        title = company = location = posted_time = clicks = "N/A"

        # Get job title
        title_tag = soup.find("h1", class_="top-card-layout__title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Get company
        company_tag = soup.find("a", class_="topcard__org-name-link")
        if company_tag:
            company = company_tag.get_text(strip=True)

        # Get location (2nd span in topcard__flavor-row)
        flavor_rows = soup.find_all("div", class_="topcard__flavor-row")
        if flavor_rows and len(flavor_rows) > 0:
            flavor_spans = flavor_rows[0].find_all("span", class_="topcard__flavor")
            if len(flavor_spans) > 1:
                location = flavor_spans[1].get_text(strip=True)

        # Get posted time and clicks
        if len(flavor_rows) > 1:
            # Posted time
            posted_span = flavor_rows[1].find("span", class_="posted-time-ago__text")
            if posted_span:
                posted_time = posted_span.get_text(strip=True)

            # Clicks / applicants
            applicants_caption_figcaption = flavor_rows[1].find("figcaption", class_="num-applicants__caption")
            applicants_caption_span = flavor_rows[1].find("span", class_="num-applicants__caption")
            if applicants_caption_figcaption or applicants_caption_span:
                clicks = applicants_caption_figcaption.get_text(strip=True) if applicants_caption_figcaption else applicants_caption_span.get_text(strip=True)
            else:
                clicks = "N/A"

        # ---------- Workplace Type & Job Type ----------
        employment_type = "N/A"
        workplace_type = "N/A"
        criteria_items = soup.find_all("li", class_="description__job-criteria-item")
        # print(f"the criteria items come in as follows {criteria_items}")


        for item in criteria_items:
            header = item.find("h3", class_="description__job-criteria-subheader")
            value = item.find("span", class_="description__job-criteria-text")
            
            if header and value:
                label = header.get_text(strip=True)
                val = value.get_text(strip=True)

            if label == "Employment type":
                    employment_type = val
            elif label == "Job function":
                    workplace_type = val

        # ---------- Description ----------
        description_div = soup.find("div", class_="show-more-less-html__markup")
        description = description_div.get_text(separator="\n", strip=True) if description_div else "N/A"

        # ---------- Result ----------
        job_data = {
            "title": title,
            "company": company,
            "location": location,
            "posted": posted_time,
            "clicks": clicks,
            "workplace_type": workplace_type,
            "job_type": employment_type,
            "description": description
        }

        # ---------- Output ----------
        return job_data
    
    except Exception as e:
        logger.error(f"Job link extraction failed: {e}")
        return {}

def matches_user(job_data: dict, user_details: dict, state: dict) -> bool:
    prompt_template = ChatPromptTemplate.from_messages([
        ("system",
        "You are a job matcher.\n"
        "Your task is to determine whether the user (candidate) is a good fit for a job posting.\n\n"

        "Guidelines:\n"
        "1. Analyze the user's profile: skills, education, experience, preferences, and projects.\n"
        "2. Carefully review the job posting.\n"
        "3. Output strictly one of the following:\n"
        "   - If the user is NOT qualified: output 'False' only.\n"
        "   - If the user IS qualified: output 'True' followed by a JSON object on the same line, space-separated.\n"
        "     The JSON must include only available data from the job post, using this format:\n\n"
        "     {{\n"
        "         \"salary\": \"\",\n"
        "         \"skills_required\": \"\",\n"
        "         \"deadline\": \"\",\n"
        "         \"experienced_level\": \"\"\n"
        "     }}\n\n"

        "4. Field Standardization Rules:\n"
        "   - **skills_required**: Use full, standardized terms. Examples:\n"
        "     - 'ML' → 'Machine Learning'\n"
        "     - 'NLP' → 'Natural Language Processing'\n"
        "     - 'JS' → 'JavaScript'\n"
        "     - 'webdev' → 'Web Development'\n"
        "     - Always output as a comma-separated string, with each skill in Title Case.\n\n"
        "   - **experienced_level**: Use one of the following fixed values:\n"
        "     - \"Intern\", \"Entry-Level\", \"Mid-Level\", \"Mid-Senior\", \"Senior\", \"Director\", \"Executive\"\n"
        "     - If unclear, leave as an empty string.\n\n"
        "   - **deadline**: Format as \"YYYY-MM-DD\" (ISO 8601).\n"
        "     - If only a month/year is provided (e.g., \"June 2025\"), convert to \"2025-06-30\".\n"
        "     - If no date is available, leave as an empty string.\n\n"
        "   - **salary**: Extract numeric salary data if available.\n"
        "     - Format as: \"$X/year\" or \"$X/hour\" (e.g., \"$120000/year\", \"$60/hour\").\n"
        "     - If a salary range is given, format as: \"$X–Y/year\" (e.g., \"$90,000–120,000/year\").\n"
        "     - Always use USD format unless another currency is clearly specified.\n"
        "     - If no salary is mentioned, leave as an empty string.\n\n"

        "5. Do not explain, elaborate, or output anything else—just the boolean string and (if qualified) the JSON.\n"
        "6. The JSON must only appear if the output is 'True'. If the output is 'False', do not include JSON.\n"
        "7. Always separate 'True' and the JSON with exactly one space.\n"),

        ("human",
        "The user details are:\n{user_details}\n\n"
        "The job data is:\n{job_data}")
    ])

    chain: Runnable = prompt_template | matching_llm | StrOutputParser()

    try:
        result = chain.invoke({
            "user_details": json.dumps(user_details, indent=2),
            "job_data": json.dumps(job_data, indent=2)
        }).strip().lower()

        logger.info(f"LLM match result: {result}")

        # Ensure it's a valid Python boolean
        if result == "false":
            print("\n\nThis user is not eligible\n\n")
            return False, {}
        
        elif result.startswith("true"):
            try:
                # Remove "true " and parse the JSON
                _, json_part = result.split(" ", 1)
                job_info = json.loads(json_part)

                print("This user is eligible\n")
                print("Matched job info:\n\n", job_info)
                return True, job_info

            except (ValueError, json.JSONDecodeError) as parse_error:
                logger.error(f"Failed to parse JSON from LLM result: {parse_error}")
                return False, {}

        else:
            print(f"Unexpected LLM result: {result}")
            return False, {} # default safe behavior

    except Exception as e:
        logger.error(f"LLM match error: {e}")
        if "quota" in str(e).lower() or "limit" in str(e).lower():
            state["llm_limit_exceeded"] = True
        return False, {} 
    
def linkedin_scraper(webpage_base, user_details, user_id, delay=3, state=None, max_empty_pages=2):
    page = 0
    empty_page_count = 0  # To count how many empty pages we hit
    max_failed_matches = 10
    failed_matches = 0
    no_save_count = 0
    max_no_save_pages = 3  # You can tune this


    if state is None:
        state = {}

    # === Limit the number of jobs per user to 2 ===
    db = next(get_db())
    try:
        user_job_count = db.query(JobRecommendation).filter_by(user_id=user_id).count()
        if user_job_count >= 2:
            logger.info(f"User {user_id} already has {user_job_count} jobs saved. Skipping scraping.")
            state["user_max_jobs_reached"] = True  # flag for frontend message
            return False
        
    except Exception as e:
        logger.error(f"Failed to count user jobs: {e}")
        return False
    finally:
        db.close()

    while True:
        url = f"{webpage_base}{page}"
        logger.info(f"Scraping: {url}")

        jobs_saved_this_page = 0

        try:
            response = requests.get(url, headers=get_headers(), timeout=2)
        except Exception as e:
            logger.warning(f"Request failed: {e}")
            page += 25
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        jobs = soup.find_all(
            'div',
            class_='base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card'
        )

        if not jobs:
            empty_page_count += 1
            logger.info(f"No jobs found on page {page}. Consecutive empty pages: {empty_page_count}")
            if empty_page_count >= max_empty_pages:
                logger.info("Too many empty pages. Ending scraping.")
                break
            page += 25  # Go to next page and try again
            time.sleep(delay + random.uniform(0, 2))
            continue

        empty_page_count = 0  # Reset on a successful page

        db = next(get_db())

        try:
            for job in tqdm(jobs, desc=f"Processing page {page}"):
                job_link = job.find('a', class_='base-card__full-link')['href']
                job_details = each_link_extractor(job_link)

                if state.get("llm_limit_exceeded"):
                    logger.warning("LLM limit hit. Stopping further matching.")
                    break

                # === Check DB job count here ===
                job_count = db.query(JobRecommendation).filter_by(user_id=user_id).count()
                if job_count >= 2:
                    logger.info(f"User {user_id} already has 2 job recommendations. Stopping.")
                    state["user_max_jobs_reached"] = True  # Optional flag if you want to notify
                    break

                # Hash based deduplication
                job_hash = generate_job_hash(
                    job_details.get("title", ""),
                    job_details.get("company", ""),
                    job_details.get("location", ""),
                    job_details.get("description", "")
                )

                existing_job = db.query(JobRecommendation).filter(
                    (JobRecommendation.url == job_link) | (JobRecommendation.job_hash == job_hash)
                ).first()

                if existing_job:
                    print(f"[SKIP] Job already exists in DB: {job_link}")
                    continue  # Skip this job

                is_match, matched_info = matches_user(job_details, user_details, state)

                if is_match:
                    new_job = JobRecommendation(
                        user_id=user_id,
                        job_title=job_details.get("title", ""),
                        company=job_details.get("company", ""),
                        salary=matched_info.get("salary", ""),
                        location=job_details.get("location", ""),
                        job_type=job_details.get("job_type", ""),
                        experience_level=matched_info.get("experienced_level", ""),
                        skills_required=matched_info.get("skills_required", ""),
                        posted=job_details.get("posted", ""),
                        description=job_details.get("description", ""),
                        url=job_link,
                        deadline=matched_info.get("deadline", ""),
                        job_hash=job_hash
                    )
                    db.add(new_job)
                    db.commit()
                    print(f"[SUCCESS], one job saved to DB.")
                    
                else:
                    print(f"Job not matched. Skipping.")
                    failed_matches += 1

                    if failed_matches >= max_failed_matches:
                        logger.warning("Too many unmatched jobs. Aborting scraping early.")
                        state["too_many_failed_matches"] = True
                        break
                
                if jobs_saved_this_page == 0:
                    no_save_count += 1
                    logger.info(f"No jobs saved on page {page}. Consecutive no-save pages: {no_save_count}")
                    if no_save_count >= max_no_save_pages:
                        logger.info("Too many pages without any saved jobs. Stopping scraping.")
                        break
                else:
                    no_save_count = 0  # Reset when a job is saved

            
        except Exception as e:
            logger.exception(f"Scraping failed: {e}")
        finally:
            db.close()

        if state.get("llm_limit_exceeded"):
            logger.warning("LLM limit exceeded. Stopping scraper.")
            break

        if state.get("too_many_failed_matches"):
            logger.warning("User details do not match any job across multiple listings. Aborting.")
            break

        if state.get("user_max_jobs_reached"):
            logger.info("User has reached the 2-job limit. Ending all scraping.")
            break  # This breaks the while pagination loop

        page += 25  # Go to next LinkedIn page
        time.sleep(delay + random.uniform(0, 2))

    return True


# Declared before the function to check when LLMs exceed their limits
llm_limit_exceeded = False

def get_perfected_user_details(user_id):
    # Check when llm limits are exceeded and display messages (error or success)
    messages = []
    state = {"llm_limit_exceeded": False}

    # === Add 2-job limit check here ===
    db = next(get_db())
    try:
        job_count = db.query(JobRecommendation).filter_by(user_id=user_id).count()
        if job_count >=2:
            msg = "✅ You already have 2 job recommendations. This project is for demo purposes only."
            messages.append(msg)
            logger.info(msg)
            return {"success": True, "messages": messages}
    
    except Exception as e:
        logger.error(f"Job count check failed: {e}")
        return {"success": False, "messages": [f"DB error during job count: {e}"]}
    
    finally:
        db.close()

    try:
        user_preferences = get_user_preferences(user_id)
        if not user_preferences:
            return {"success": False, "message": "No user preferences found."}

        github_url = user_preferences.get("github")
        github_username = github_url.split("/")[-1] if github_url else ""
        user_github_repo, github_message = get_user_projects_with_readmes(github_username)

        if github_message:
            messages.append(github_message)

        # Even if user_github_repo is empty, continue...
        user_full_details = compare_social_to_database(user_preferences, user_github_repo, state)
        if not user_full_details:
            messages.append("LLM failed to generate full user details.")
            user_full_details = {}  # Avoid crash, continue with empty details

        linkedin_urls = generate_linkedin_urls(user_preferences, state)
        if not linkedin_urls:
            messages.append("No LinkedIn URLs generated.")
            linkedin_urls = [] 

        for link in linkedin_urls:
            if state.get("llm_limit_exceeded"):
                break

            linkedin_scraper(link, user_full_details, user_id, state=state)

            # === If user consistently fails to match jobs ===
            if state.get("too_many_failed_matches"):
                messages.append(
                    "⚠️ Your profile did not match any job listings. "
                    "This is likely because your skills, experience, or projects "
                    "do not align with the level of roles you selected.\n\n"
                    "➡️ Tip: Try adjusting your preferences — "
                    "select a lower experience level, junior-friendly job titles, or broader work types."
                )
                break

        if state.get("llm_limit_exceeded"):
            messages.append("LLM usage limit exceeded. Please try again in a few hours.")

        if state.get("user_max_jobs_reached"):
            messages.append("⚠️ This is a test version. Only 2 job recommendations per user are allowed.")

        if not messages:
            messages.append("Job scraping completed successfully.")

        return {"success": True, "messages": messages}

    except Exception as e:
        return {"success": False, "messages": [f"Fatal error: {e}"]}



def serialize_job(job):
    job_dict = job.__dict__.copy()
    job_dict.pop('_sa_instance_state', None)
    return job_dict

def get_job_recommendation_details(user_id: int):
    db = next(get_db())
    job_recommendations = db.query(JobRecommendation).filter(JobRecommendation.user_id == user_id).all()
    db.close()

    return [serialize_job(job) for job in job_recommendations]
