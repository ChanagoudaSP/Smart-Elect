from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app.models.models import User
from app import db
from app.utils.face_recognition import FaceRecognitionSystem
import cv2
import numpy as np
import logging
import re

# Configure logging
logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__, url_prefix='/auth')
face_recognition_system = FaceRecognitionSystem()

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        national_id = (request.form.get('national_id') or '').strip() or None

        # Validate input
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered')
            return redirect(url_for('auth.register'))

        # Validate first and last name: only allow letters (upper/lowercase)
        if not re.fullmatch(r"[A-Za-z]+", first_name.strip()):
            flash('First name must contain only letters (A-Z, a-z)')
            return redirect(url_for('auth.register'))
        if not re.fullmatch(r"[A-Za-z]+", last_name.strip()):
            flash('Last name must contain only letters (A-Z, a-z)')
            return redirect(url_for('auth.register'))

        # Create new user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            national_id=national_id
        )
        user.set_password(password)

        # Attempt face enrollment (photo feature) — never blocks registration
        success, face_encoding, message = face_recognition_system.capture_face()
        if success and face_encoding is not None and getattr(face_encoding, 'shape', None) == (100, 100):
            user.set_face_encoding(face_encoding)
        else:
            logger.warning(f"Face enrollment skipped during registration: {message}")

        db.session.add(user)
        db.session.commit()

        flash('Registration successful')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        logger.info(f"Login attempt for email: {email}")
        
        if user and user.check_password(password):
            logger.info("Password verification successful")
            login_user(user)
            
            # Check if user is admin and redirect accordingly
            if user.is_admin:
                logger.info("Admin user detected, redirecting to admin dashboard")
                return redirect(url_for('admin.dashboard'))
            
            next_page = request.args.get('next')
            logger.info(f"Redirecting to: {next_page or url_for('main.index')}")
            return redirect(next_page or url_for('main.index'))
        else:
            logger.error("Invalid email or password")
            flash('Invalid email or password')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        # In a real app, generate a token and send email. Here, redirect to reset form.
        return redirect(url_for('auth.reset_password', email=email))
    return render_template('auth/forgot_password.html')

@bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = request.args.get('email')
    if not email:
        flash('Invalid or missing email for password reset.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('No account found with that email.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        password = request.form['password']
        confirm = request.form['confirm_password']
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.reset_password', email=email))
        user.set_password(password)
        db.session.commit()
        flash('Password reset successful. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', email=email)

@bp.route('/restore-face', methods=['GET', 'POST'])
def restore_face():
    email = request.args.get('email') or request.form.get('email')
    if request.method == 'POST':
        password = request.form.get('password')
        if not email or not password:
            flash('Email and password are required to restore face encoding.', 'danger')
            return redirect(url_for('auth.restore_face', email=email))

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email or password for face restore.', 'danger')
            return redirect(url_for('auth.restore_face', email=email))

        success, face_encoding, message = face_recognition_system.capture_face()
        if not success:
            flash(f'Face restore failed: {message}', 'danger')
            return redirect(url_for('auth.restore_face', email=email))

        if face_encoding is None or getattr(face_encoding, 'shape', None) != (100, 100):
            flash('Face restore failed: Invalid face encoding captured.', 'danger')
            return redirect(url_for('auth.restore_face', email=email))

        user.set_face_encoding(face_encoding)
        db.session.commit()

        flash('Face encoding restored successfully. Please log in again.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/restore_face.html', email=email)