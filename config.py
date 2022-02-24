from os import environ
from dotenv import load_dotenv
load_dotenv()

class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "America/New_York"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = environ.get('SQLALCHEMY_DATABASE_URI')
    # SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL')
    MAIL_SERVER = ENV[‘AUTH_TOKEN’]
    MAIL_PORT = 465
    MAIL_USERNAME = ENV[‘AUTH_TOKEN’]
    MAIL_PASSWORD = 'ENV[‘AUTH_TOKEN’]
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    SECRET_KEY = environ.get('APP_SECRET_KEY')