from job_scrapper import (compare_social_to_database, get_user_preferences,
                          get_user_projects_with_readmes)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.platypus.flowables import HRFlowable
from io import BytesIO
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()
CV_GENERATOR_GROQ_API_KEY = os.environ.get("CV_GENERATOR_GROQ_API_KEY")

cv_generator_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    max_tokens=1000,
    timeout=30,
    max_retries=2,
    api_key=CV_GENERATOR_GROQ_API_KEY
)

def get_user_full_details(user_id):
    user_preferences = get_user_preferences(user_id)
    if not user_preferences:
        print("[ERROR] User preferences not found.")
        return None

    github_url = user_preferences.get("github")
    if not github_url:
        print("[ERROR] No GitHub URL in user preferences.")
        return user_preferences  # fallback to just using preferences

    github_username = github_url.split("/")[-1].strip()
    if not github_username:
        print("[ERROR] Invalid GitHub URL.")
        return user_preferences  # fallback

    user_github_repo = get_user_projects_with_readmes(github_username)

    full_details = compare_social_to_database(user_preferences, user_github_repo)
    if not full_details:
        print("[ERROR] Failed to merge user details and GitHub projects.")
        return user_preferences  # fallback to user_preferences only

    return full_details


def generate_cv_with_llm(data, follow_format=False):
    prompt_template = ChatPromptTemplate.from_messages([
        ("system",
        "You are a professional CV generator.\n\n"
        "Instructions:\n"
        "1. If `follow_format` is True:\n"
        "   - Follow the original CV structure provided in `initial_cv_content`.\n"
        "2. If `follow_format` is False:\n"
        "   - Ignore the original format and create a new CV from scratch.\n"
        "3. Only include content relevant to the job and the user's capacity.\n"
        "4. Your response must ONLY contain the final CV content (no preamble, no extra explanation),\n"
        "   as it will be converted directly to PDF."
        ),
        ("user",
        "Here is the input data:\n\n"
        "{data}\n\n"
        "Follow original format: {follow_format}")
    ])

    
    chain: Runnable = prompt_template | cv_generator_llm | StrOutputParser()
    try:
        response = chain.invoke({
            "data": data,
            "follow_format": follow_format
        }).strip()

        return response
    
    except Exception as e:
        print(f"LLM failed to generate CV: {e}")
        return False

def convert_text_to_pdf(text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)

    styles = getSampleStyleSheet()
    flowables = []

    for paragraph in text.split('\n\n'):  # detect paragraphs
        flowables.append(Paragraph(paragraph.strip(), styles["Normal"]))
        flowables.append(Spacer(1, 10))  # space between paragraphs

    doc.build(flowables)
    return buffer.getvalue()

