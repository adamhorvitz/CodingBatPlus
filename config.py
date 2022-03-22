from os import environ
from dotenv import load_dotenv
load_dotenv()

# Configuration for the application
class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "America/New_York"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = environ.get('SQLALCHEMY_DATABASE_URI')
    MAIL_SERVER = ENV[‘AUTH_TOKEN’]
    MAIL_PORT = 465
    MAIL_USERNAME = 'codingbatplus@gmail.com'
    MAIL_PASSWORD = 'NBPS2022'
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    SECRET_KEY = environ.get('APP_SECRET_KEY')