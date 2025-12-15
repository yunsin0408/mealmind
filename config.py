import os
import requests
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mealmind.db'
    HF_TOKEN = os.getenv("HF_TOKEN")
    HF_URL = "https://router.huggingface.co/v1/chat/completions"
    HF_MODEL = os.getenv('HF_MODEL')
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'false').lower() in ('1','true','yes')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() in ('1','true','yes')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

  