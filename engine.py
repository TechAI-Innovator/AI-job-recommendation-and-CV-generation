# engine.py
from db import SessionLocal
from sqlalchemy.exc import SQLAlchemyError
from models import User, CV
from datetime import datetime

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper function to remove empty entries
def clean_entries(entries):
    return [entry for entry in entries if any(value.strip() for value in entry.values())]

def save_user_profile(user_id, profile_data: dict):
    try:
        db = next(get_db())
        db.query(User).filter(User.id == user_id).update(profile_data)
        db.commit()
        return True, "Profile updated successfully."
    except SQLAlchemyError as e:
        db.rollback()
        return False, f"Error updating profile: {str(e)}"
    finally:
        db.close()

def save_cv(user_id, resume_path, raw_text):
    try:
        db = next(get_db())

        existing_cv = db.query(CV).filter_by(user_id=user_id).order_by(CV.generated_on.desc()).first()
        if existing_cv:
            existing_cv.file_path = resume_path
            existing_cv.content = raw_text
            existing_cv.generated_on = datetime.now()
        else:
            new_cv = CV(
                user_id=user_id,
                file_path=resume_path,
                content=raw_text
            )
            db.add(new_cv)

        db.commit()
        return True, "CV saved successfully."
    except SQLAlchemyError as e:
        db.rollback()
        return False, f"Error saving CV: {str(e)}"
    
    finally:
        db.close()