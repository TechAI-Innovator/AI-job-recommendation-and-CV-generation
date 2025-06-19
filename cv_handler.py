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
from io import BytesIO
import tempfile


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
def extract_text_from_file(file_stream, filename):
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            tmp.write(file_stream.read())
            tmp_path = tmp.name

        # Use appropriate loader based on extension
        if filename.lower().endswith(".pdf"):
            loader = PyMuPDFLoader(tmp_path)
        else:
            loader = UnstructuredFileLoader(tmp_path)

        docs = loader.load()
        return "\n".join([doc.page_content for doc in docs])

    except Exception as e:
        print(f"Failed to extract text: {e}")
        return ""

    finally:
        # Ensure the temp file is deleted
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
    
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
    file_stream = BytesIO(file_storage.read())  # Read in-memory file

    # Extract text from file (you’ll need to update extract_text_from_file)
    raw_text = extract_text_from_file(file_stream, filename)

    # Parse with LangChain
    extracted_data = parse_cv_with_llm(raw_text)
    extracted_data["raw_text"] = raw_text
    extracted_data["uploaded_cv_path"] = filename  # just the name

    try:
        db = next(get_db())
        cv = CV(
            user_id=user_id,
            content=extracted_data.get("raw_text", ""),
            file_path=filename  # save just the name, not the full path
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
    Extracts resume content from uploaded file without saving permanently.
    Deletes old file if it exists (optional cleanup).
    Returns filename and extracted text.
    """

    # 🔁 Delete old file if exists (optional cleanup)
    if old_file_path and os.path.exists(old_file_path):
        try:
            os.remove(old_file_path)
            print(f"Deleted old resume: {old_file_path}")
        except Exception as e:
            print(f"Failed to delete old resume: {e}")

    # 📄 Prepare file stream
    filename = secure_filename(file_storage.filename)
    file_stream = BytesIO(file_storage.read())

    # 📦 Extract text using temp file method
    raw_text = extract_text_from_file(file_stream, filename)

    return filename, raw_text