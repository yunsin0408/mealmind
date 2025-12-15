from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import DevelopmentConfig
import requests
import json
import os
from flask_login import LoginManager
from flask_mail import Mail

db = SQLAlchemy()

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    CORS(app)
    app.config.from_object(config_class)


    db.init_app(app)

    # Setup login manager
    login_manager = LoginManager()
    login_manager.login_view = 'routes.login'
    login_manager.init_app(app)

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Setup mail
    mail = Mail()
    mail.init_app(app)
    # expose mail at package level for email_utils to import
    import app as _app
    _app.mail = mail
    # Import and register routes
    from .routes import routes_bp
    app.register_blueprint(routes_bp)

    return app