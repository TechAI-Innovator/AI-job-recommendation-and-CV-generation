import os
from datetime import datetime
from werkzeug.utils import secure_filename
from models import CV
from engine import get_db
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredFileLoader
import json


load_dotenv()
# Get Groq API key from environment variables
CV_PARSER_GROQ_API_KEY = os.environ.get("CV_PARSER_GROQ_API_KEY")

# Initialize Groq model
cv_parser_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    max_tokens=1000,
    timeout=30,
    max_retries=2,
    api_key=CV_PARSER_GROQ_API_KEY
)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === Helper to extract text from uploaded CV ===
def extract_text_from_file(file_path):
    try:
        if file_path.endswith(".pdf"):
            loader = PyMuPDFLoader(file_path)
        else:
            loader = UnstructuredFileLoader(file_path)
        docs = loader.load()
        return "\n".join([doc.page_content for doc in docs])
    except Exception as e:
        print(f"Failed to extract text: {e}")
        return ""
    
def parse_cv_with_llm(cv_text: str) -> dict:
    """
    Parses the provided CV text using LangChain + Groq LLM and extracts structured data.
    Returns a dictionary of extracted fields.
    """

    # Build a structured prompt to ensure the LLM responds in the correct JSON format
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that extracts structured data from CVs."),
        ("human", 
        """
            1. Extract the following from the CV:
            - first_name
            - middle_name
            - surname
            - email
            - phone
            - location
            - linkedin
            - github
            - skills
            - summary
            - education: list of degree, institution, year, description
            - experience: list of title, company, duration, description

            2. Return result in JSON format:
            {{
                "first_name": "",
                "middle_name": "",
                "surname": "",
                "email": "",
                "phone": "",
                "location": "",
                "linkedin": "",
                "github": "",
                "skills": "",
                "summary": "",
                "education": [],
                "experience": []
            }}

            3. No extra information, questions or instructions. Strictly just the format above.

            4. If no data is found for a field, return an empty string or empty list.

            5. Ensure it is properly formatted JSON with correct brackets and commas.

            CV TEXT:
            {cv_text}
        """
        )
            ])

    try:
        # Format the prompt using the CV text
        messages = prompt.format_messages(cv_text=cv_text)

        # Send prompt to the Groq model
        response = cv_parser_llm.invoke(messages)
        cleaned_response = response.content.strip("`\n ")
        return json.loads(cleaned_response)

    except json.JSONDecodeError as decode_err:
        print("❌ JSON Parse Error:", decode_err)
        return {}

    except Exception as general_err:
        print("❌ General Error:", general_err)
        return {}

def handle_cv_upload(file_storage, user_id):
    filename = secure_filename(file_storage.filename)
    safe_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(
        UPLOAD_FOLDER,
        f"{user_id}_{safe_timestamp}_{filename}"
    )


    print(f"The file path is {file_path}")
    file_storage.save(file_path)

    # Extract text from file
    raw_text = extract_text_from_file(file_path)

    # Parse with LangChain
    extracted_data = parse_cv_with_llm(raw_text)
    extracted_data["raw_text"] = raw_text  # Store raw content
    extracted_data["uploaded_cv_path"] = file_path

    try:
        db = next(get_db())
        cv = CV(
            user_id=user_id,
            content=extracted_data.get("raw_text", ""),
            file_path = file_path
        )
        db.add(cv)
        db.commit()
    except SQLAlchemyError as e:
        print(f"{e}")
    finally:
        db.close()

    return extracted_data

def save_resume_file(file_storage, user_id, old_file_path=None):
    """
    Saves a new resume file and deletes the old one if it exists.
    Returns the new file path and extracted content.
    """
    # Delete the old file if provided
    if old_file_path and os.path.exists(old_file_path):
        try:
            os.remove(old_file_path)
            print(f"Deleted old resume: {old_file_path}")
        except Exception as e:
            print(f"Failed to delete old resume: {e}")

    filename = secure_filename(file_storage.filename)
    safe_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(
        UPLOAD_FOLDER,
        f"{user_id}_{safe_timestamp}_{filename}"
    )
    
    file_storage.save(file_path)

    # Extract text from file
    raw_text = extract_text_from_file(file_path)

    return file_path, raw_text