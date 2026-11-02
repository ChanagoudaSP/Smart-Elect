import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
      # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 280
    
    # Flask-Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    # On a dev machine without SMTP credentials, don't block election creation
    # trying to send announcement emails. Set MAIL_SUPPRESS_SEND=false to enable.
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'true').lower() == 'true'
    
    # Application settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # Security settings
    # Set SESSION_COOKIE_SECURE=true only when serving over HTTPS.
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True