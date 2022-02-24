from datetime import date
from os import environ
import dotenv
import numpy as np
import matplotlib.pyplot as plt
import mpld3
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_apscheduler import APScheduler
from flask_login import LoginManager, UserMixin, login_required, logout_user, current_user, login_user
from flask_mail import Mail, Message
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from requests import Session
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
scheduler = APScheduler()


def init_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    load_dotenv()
    mail.init_app(app)

    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)


    # scheduler.add_job(func=database, trigger="interval", days=7)
    scheduler.init_app(app)
    scheduler.start()

    with app.app_context():
        # Include our Routes
        from . import routes
        from . import auth

        db.create_all()
        # Register Blueprints
        app.register_blueprint(routes.app_bp)
        # app.register_blueprint(admin.admin_bp)

        return app


