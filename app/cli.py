import os
import click
import cv2
import numpy as np
from flask.cli import with_appcontext
from app.models.models import User
from app import db
from app.utils.face_recognition import FaceRecognitionSystem
from sqlalchemy.orm.exc import NoResultFound
import numpy as np

@click.command('create-admin')
@click.argument('email')
@click.argument('password')
@click.argument('first_name')
@click.argument('last_name')
@click.argument('national_id')
@click.option('--image', help='Path to admin profile image for face recognition')
@with_appcontext
def create_admin(email, password, first_name, last_name, national_id, image=None):
    """Create an admin user with optional face recognition.
    
    Example:
        flask create-admin admin@example.com password123 John Doe AB123456 --image /path/to/image.jpg
    """
    user = User.query.filter_by(email=email).first()
    if user:
        click.echo('Email already registered')
        return

    # Initialize face recognition system
    face_recognition_system = FaceRecognitionSystem()
    face_encoding = None
    
    if image:
        if not os.path.exists(image):
            click.echo(f'Error: Image file not found: {image}')
            return
            
        try:
            # Read and process the image
            img = cv2.imread(image)
            if img is None:
                raise ValueError('Could not read image file')
                
            # Convert to RGB (face_recognition uses RGB)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Get face encoding
            face_roi = face_recognition_system.get_face_encoding(rgb_img)
            if face_roi is None:
                click.echo('Warning: No face detected in the provided image.')
                if not click.confirm('Continue without face registration?', default=False):
                    return
            else:
                face_encoding = face_roi
                
        except Exception as e:
            click.echo(f'Error processing face image: {str(e)}')
            if not click.confirm('Continue without face registration?', default=False):
                return

    # Create user
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        national_id=national_id,
        is_admin=True,
        is_verified=True
    )
    user.set_face_encoding(face_encoding)
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        if face_encoding is not None:
            click.echo(f'Admin user {email} created successfully with face recognition')
        else:
            click.echo(f'Admin user {email} created successfully (no face registration)')
            click.echo('Note: The admin will need to register their face through the web interface')
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error creating admin user: {str(e)}')

@click.command('update-face')
@click.argument('email')
@click.argument('image_path')
@with_appcontext
def update_face_encoding(email, image_path):
    """Update face encoding for an existing user.
    
    Example:
        flask update-face admin@example.com /path/to/face.jpg
    """
    try:
        user = User.query.filter_by(email=email).one()
    except NoResultFound:
        click.echo(f'Error: User with email {email} not found')
        return
        
    if not os.path.exists(image_path):
        click.echo(f'Error: Image file not found: {image_path}')
        return
        
    try:
        # Initialize face recognition system
        face_recognition_system = FaceRecognitionSystem()
        
        # Read and process the image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError('Could not read image file')
            
        # Convert to RGB (face_recognition uses RGB)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Get face encoding as numpy array (100x100)
        face_roi = face_recognition_system.get_face_encoding(rgb_img)
        if face_roi is None:
            click.echo('Error: No face detected in the provided image')
            return
            
        # Convert to grayscale and resize to 100x100 if needed
        if len(face_roi.shape) == 3:  # If color image
            face_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        if face_roi.shape != (100, 100):
            face_roi = cv2.resize(face_roi, (100, 100))
            
        # Store as string representation of numpy array
        user.set_face_encoding(face_roi)
        
        db.session.commit()
        click.echo(f'Successfully updated face encoding for {email}')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error updating face encoding: {str(e)}')

@click.command('check-face-encodings')
@with_appcontext
def check_face_encodings():
    """Check and fix face encodings for all users."""
    try:
        users = User.query.all()
        if not users:
            click.echo("No users found in the database.")
            return
            
        click.echo(f"Found {len(users)} users in the database.")
        
        for user in users:
            if not user.face_encoding:
                click.echo(f"User {user.email}: No face encoding found")
                continue

            encoding = user.get_face_encoding()
            if encoding is None:
                click.echo(f"User {user.email}: Invalid or corrupted face encoding")
            else:
                click.echo(f"User {user.email}: Valid encoding found")
                
    except Exception as e:
        click.echo(f"Error checking face encodings: {str(e)}")
        db.session.rollback()
        raise