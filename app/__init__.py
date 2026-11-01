import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler
from config import Config

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

@login_manager.user_loader
def load_user(user_id):
    from app.models.models import User
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)
    
    # Register template filters
    from app.utils.template_filters import register_template_filters
    register_template_filters(app)
    
    # Set up logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/smart_elect.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Smart-Elect startup')
    
    with app.app_context():
        # Register blueprints
        from app.routes import auth, main, admin, notifications
        app.register_blueprint(auth.bp)
        app.register_blueprint(main.bp)
        app.register_blueprint(admin.bp)
        app.register_blueprint(notifications.bp)
        
        # Register CLI commands
        from app.cli import create_admin, update_face_encoding, check_face_encodings
        app.cli.add_command(create_admin)
        app.cli.add_command(update_face_encoding)
        app.cli.add_command(check_face_encodings)
        
        # Create database tables
        db.create_all()
        
        # Register error handlers
        @app.errorhandler(500)
        def internal_error(error):
            db.session.rollback()
            app.logger.error('Server Error: %s', str(error))
            return render_template('errors/500.html'), 500

        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('errors/404.html'), 404

        return app