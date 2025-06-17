# auth.py
from flask import (Blueprint, request, redirect,
                   url_for, flash, current_app,
                   render_template)
from flask_login import (login_user, logout_user,
                         login_required, current_user)
from flask_mail import Message, Mail
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import (generate_password_hash,
                               check_password_hash)
from sqlalchemy.exc import SQLAlchemyError
from models import User
from engine import get_db
import os
from dotenv import load_dotenv

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    username_or_email = request.form['identifier']
    password = request.form['password']
    try:
        db = next(get_db())
        user = db.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
            ).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("❌ Incorrect username or password", "login-error")
            return redirect(url_for("index") + "#login")
    except SQLAlchemyError as e:
        flash("⚠️ An error occurred during login. Please try again.", "login-error")
        print(f"Login error: {e}")
        return redirect(url_for("index") + "#login")
    finally:
        db.close()

@auth_bp.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    try:
        db = next(get_db())
        hashed_password = generate_password_hash(password)
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
            ).first()
        
        if existing_user:
            flash("❌ Username or email already exists.", "register-error")
            return redirect(url_for("index") + "#register")
        
        new_user = User(username=username, email=email, password=hashed_password)
        db.add(new_user)
        db.commit()
        flash("✅ Registration successful!", "register-success")
        return redirect(url_for("index") + "#login")
    except SQLAlchemyError as e:
        flash("⚠️ An error occurred during registration. Please try again.", "register-error")
        print(f"Registration error: {e}")
        return redirect(url_for("index") + "#register")
    finally:
        db.close()

@auth_bp.route('/logout')
@login_required
def logout():
    try:
        username = current_user.username
        logout_user()
        return render_template('logout.html', username=username)
    except Exception as e:
        flash("⚠️ An error occurred during logout.", "logout-error")
        print(f"Logout error: {e}")
        return redirect(url_for("index"))



load_dotenv()

'''For password resetting'''
# Setup Mail
mail = Mail()

def send_reset_email(user):
    try:
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        token = s.dumps(user.email, salt='password-reset-salt')
        reset_link = url_for('auth.reset_token', token=token, _external=True)

        msg = Message(
                subject='Password Reset Request',
                sender=os.getenv('MAIL_DEFAULT_SENDER'),
                recipients=[user.email]
            )
        
        msg.body = f'''Hello {user.username or 'there'},

    We received a request to reset your password. You can do this securely by clicking the button below:

    Reset Password: {reset_link}

    If the button above doesn't work, you can copy and paste this link into your browser:
    {reset_link}

    Alternatively, copy the reset code below and paste it on the manual reset page:

    Your Reset Code:
    {token}

    Go to this page to use the code:
    https://yourapp.com/manual-reset

    ⚠️ Note: This reset link and code will expire in 1 hour.

    If you did not request this, you can safely ignore this email — no changes will be made to your account.

    Stay secure,
    The Job Finder Team
'''
        mail.send(msg)
        return True
    
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        try:
            db = next(get_db())
            user = db.query(User).filter_by(email=email).first()
            if user:
                success = send_reset_email(user)
                if success:
                    flash('📬 Password reset link sent to your email.', "success")
                else:
                    flash('⚠️ Could not send email. Please try again later.', 'error')
            else:
                flash('❌ Email not found.', "error")
        except Exception as e:
            print(f"❌ Forgot password error: {e}")
            flash('⚠️ Something went wrong. Please try again.', "error")
        finally:
            db.close()
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception as e:
        print(f"❌ Token error: {e}")
        flash("⏳ Token expired or invalid", "error")
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'GET':
        flash("🔑 Enter your new password. Note: The reset link/code is valid for 1 hour.", "info")

    if request.method == 'POST':
        try:
            db = next(get_db())
            user = db.query(User).filter_by(email=email).first()
            if user:
                new_password = generate_password_hash(request.form['password'])
                user.password = new_password
                db.commit()
                flash("🔐 Password updated successfully.", "success")
                return redirect(url_for("index") + "#login")
            else:
                flash("❌ User not found.", "error")
        except Exception as e:
            print(f"❌ Reset password error: {e}")
            flash("⚠️ Something went wrong. Please try again.", "error")
        finally:
            db.close()

    return render_template('reset_password.html')

@auth_bp.route('/manual-reset', methods=['GET', 'POST'])
def manual_reset():
    if request.method == 'POST':
        token = request.form['token']
        return redirect(url_for('auth.reset_token', token=token))
    return render_template('manual_reset.html')