from flask import (Flask, jsonify, 
                   render_template, 
                   flash, request,
                   redirect, url_for,
                   send_file, abort)
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError
from db import engine, Base
from models import User, CV, JobRecommendation, Feedback
from engine import get_db, clean_entries, save_user_profile, save_cv
from utils import init_db_if_needed
from cv_handler import handle_cv_upload, save_resume_file
from auth import auth_bp, mail
import os
from dotenv import load_dotenv
from job_scrapper import get_perfected_user_details, get_job_recommendation_details, get_perfected_user_details
from cv_generator import (generate_cv_with_llm, convert_text_to_pdf,
                          get_user_full_details)
from io import BytesIO

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

mail.init_app(app)


app.register_blueprint(auth_bp)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db = next(get_db())
    user = db.query(User).get(int(user_id))
    db.close()
    return user

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard", methods=["Get", "POST"])
@login_required
def dashboard():
    user_id = current_user.id
    
    job_details = get_job_recommendation_details(user_id)

    return render_template("dashboard.html", user = current_user.username, job_details=job_details)

@app.route("/scrape-jobs")
@login_required
def scrape_jobs():
    user_id = current_user.id
    result = get_perfected_user_details(user_id)
    return result

@app.route("/cv-generator")
@login_required
def cv_generator():
    return render_template("CV_generator.html")

@app.route("/api/generate-initial-format-cv/<int:job_id>", methods=["GET"])
@login_required
def generate_initial_format_cv(job_id):
    db = next(get_db())
    job = db.get(JobRecommendation, job_id)
    db.close()

    if not job:
        return abort(404, description="Job not found")
    
    user_details = get_user_full_details(current_user.id)

    db = next(get_db())
    user_cv_record = db.query(CV).filter_by(user_id=current_user.id).first()
    db.close()

    if not user_cv_record:
        return abort(404, description="No CV uploaded by user")

    llm_input = {
        "user_details": user_details,
        "job_details": job.__dict__.pop('_sa_instance_state', None),
        "initial_cv_content": user_cv_record.content
    }

    generated_cv_text = generate_cv_with_llm(llm_input, follow_format=True)

    if not generated_cv_text:
        return abort(500, description="CV generation failed. Please try again later.")

    pdf_bytes = convert_text_to_pdf(generated_cv_text)

    # Convert generated CV text to PDF bytes
    pdf_bytes = convert_text_to_pdf(generated_cv_text)

    return send_file(
        BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f'cv_initial_format_{job_id}.pdf'
    )


@app.route("/api/generate-llm-format-cv/<int:job_id>", methods=["GET"])
@login_required
def generate_llm_format_cv(job_id):
    db = next(get_db())
    job = db.get(JobRecommendation, job_id)
    db.close()

    job_dict = {k: v for k, v in job.__dict__.items() if k != '_sa_instance_state'}

    if not job:
        return abort(404, description="Job not found")
    
    user_details = get_user_full_details(current_user.id)

    llm_input = {
        "user_details": user_details,
        "job_details": job_dict
    }

    generated_cv_text = generate_cv_with_llm(llm_input, follow_format=False)

    if not generated_cv_text:
        return abort(500, description="CV generation failed. Please try again later.")

    # Convert generated CV text to PDF bytes
    pdf_bytes = convert_text_to_pdf(generated_cv_text)

    return send_file(
        BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f'cv_llm_format_{job_id}.pdf'
    )


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user

    if request.method == "POST":
        resume_path = request.form.get("resume_path")  # From hidden input
        raw_text = None

        # If a new resume is uploaded, overwrite the path
        if 'resume' in request.files and request.files['resume'].filename != '':
            resume_file = request.files['resume']
            resume_path, raw_text = save_resume_file(resume_file, user.id, old_file_path=resume_path)

        # collect user fields
        first_name = request.form.get('first_name', "")
        middle_name = request.form.get('middle_name', "")
        surname = request.form.get('surname', "")
        # email = request.form.get('email', "")
        phone = request.form.get("phone", "")
        location = request.form.get('location', "")
        linkedin = request.form.get('linkedin', "")
        github = request.form.get('github', "")
        summary = request.form.get("summary", "")
        skills = request.form.get('skills', "")
        min_salary  = request.form.get('min_salary', "")
        preferred_titles  = request.form.get('preferred_titles', "")
        employment_type  = request.form.get("employment_type", "")
        experience_level = request.form.get("experience_level", "")
        preferred_industries = request.form.get("preferred_industries", "")
        job_keywords = request.form.get("job_keywords", "")


        # For location mapping
        locations = request.form.getlist("locations[]")
        location_worktype_map = {}

        for i, loc in enumerate(locations):
            worktypes = request.form.getlist(f"worktypes_{i}[]")
            if loc and worktypes:
                location_worktype_map[loc.strip().lower()] = [wt.strip().lower() for wt in worktypes]


        # Serialize and clean education
        education = []
        degrees = request.form.getlist('degree[]')
        institutions = request.form.getlist('institution[]')
        years = request.form.getlist('edu_year[]')
        descriptions = request.form.getlist('edu_description[]')

        for i in range(len(degrees)):
            entry = {
                'degree': degrees[i],
                'institution': institutions[i],
                'year': years[i],
                'description': descriptions[i]
            }
            education.append(entry)

        education = clean_entries(education)


        # Serialize and clean experience
        experience = []
        titles = request.form.getlist('job_title[]')
        companies = request.form.getlist('company[]')
        durations = request.form.getlist('duration[]')
        exp_descriptions = request.form.getlist('exp_description[]')

        for i in range(len(titles)):
            entry = {
                'title': titles[i],
                'company': companies[i],
                'duration': durations[i],
                'description': exp_descriptions[i]
            }
            experience.append(entry)

        experience = clean_entries(experience)
        

        profile_data = {
                    "first_name": first_name,
                    "middle_name": middle_name,
                    "surname": surname,
                    "phone": phone,
                    "location": location,
                    "linkedin": linkedin,
                    "github": github,
                    "summary": summary,
                    "skills": skills,
                    "education": education or [],
                    "experience": experience or [],
                    "preferred_titles": preferred_titles,
                    "min_salary": min_salary,
                    "location_worktype_map": location_worktype_map,
                    "employment_type": employment_type,
                    "experience_level": experience_level,
                    "preferred_industries": preferred_industries,
                    "job_keywords": job_keywords
                }
        success, msg = save_user_profile(user.id, profile_data)
        flash(msg, "success" if success else "danger")

        # Save CV
        if resume_path and raw_text:
            success, msg = save_cv(user.id, resume_path, raw_text)
            flash(msg, "success" if success else "danger")

        return redirect(url_for('profile'))

    # GET request rendering
    db = next(get_db())
    latest_cv = db.query(CV).filter_by(user_id=user.id).order_by(CV.generated_on.desc()).first()
    db.close()

    user_data = {
        "first_name": user.first_name,
        "middle_name": user.middle_name,
        "surname": user.surname,
        "email": user.email,
        "phone": user.phone,
        "location": user.location,
        "linkedin": user.linkedin,
        "github": user.github,
        "summary": user.summary,
        "skills": user.skills,
        "resume_path": latest_cv.file_path if latest_cv else None,
        "education": user.education or [],
        "experience": user.experience or [],
        "preferred_titles": user.preferred_titles,
        "min_salary": user.min_salary,
        "location_worktype_map": user.location_worktype_map or [],
        "employment_type": user.employment_type,
        "experience_level": user.experience_level,
        "preferred_industries": user.preferred_industries,
        "job_keywords": user.job_keywords
    }

    show_upload_section = not user.first_name

    return render_template(
        "profile.html",
        user_data=user_data,
        show_upload_section=show_upload_section
    )


@app.route("/extract_cv", methods=["POST"])
@login_required
def extract_cv():
    file = request.files.get("cv_file")

    if not file or file.filename == '':
        return jsonify({"error": "No file uploaded"}), 400

    if not file.filename.lower().endswith((".pdf", ".doc", ".docx")):
        return jsonify({"error": "Invalid file type"}), 400

    try:
        user_id = current_user.id
        extracted_data = handle_cv_upload(file, user_id)
        return jsonify(extracted_data), 200
    except Exception as e:
        print(f"CV extraction error: {e}")
        return jsonify({"error": "Failed to extract CV"}), 500

@app.route("/delete_cv", methods=["POST"])
@login_required
def delete_cv():
    data = request.get_json()
    resume_path = data.get("resume_path")

    if resume_path and os.path.exists(resume_path):
        try:
            os.remove(resume_path)
            # Optionally delete from DB if you saved it in a `CV` table
            db = next(get_db())
            db.query(CV).filter(CV.user_id == current_user.id, CV.file_path == resume_path).delete()
            db.commit()
            db.close()
            return jsonify({"message": "Resume deleted"}), 200
        except Exception as e:
            print(f"Error deleting file: {e}")
            return jsonify({"error": "Failed to delete resume"}), 500
    return jsonify({"error": "File not found"}), 400

@app.route("/submit-feedback", methods=["POST"])
@login_required
def submit_feedback():
    data = request.get_json()
    rating = data.get("rating")
    message = data.get("message")

    if not rating or not message:
        return jsonify({"message": "Rating and message required"}), 400
    
    db = next(get_db())
    try:
        feedback = Feedback(
            user_id=current_user.id,
            rating=rating,
            message=message
        )
        db.add(feedback)
        db.commit()
        return jsonify({"message": "Feedback submitted successfully."}), 200
    
    except SQLAlchemyError as e:  
        print(f"Feedback error: {e}")
        return jsonify({"message": "⚠️ Feedback submision failed. Please try again."})
    finally:
        db.close()


migrate = Migrate(app, Base, engine)


if __name__ == "__main__":
    init_db_if_needed()
    app.run(debug=True)