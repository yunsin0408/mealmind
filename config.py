import os
import requests
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
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

class DevelopmentConfig(Config):
    sqlLite_db_url = os.getenv('DATABASE_URL')
    if not sqlLite_db_url:
        raise RuntimeError(
            "No database URL configured for development. "
            "Set the DATABASE_URL environment variable "
            "to a SQLite connection string in your Vercel project settings."
        )
    SQLALCHEMY_DATABASE_URI = sqlLite_db_url

class ProductionConfig(Config):
    _db_url = os.getenv('POSTGRES_DB_DATABASE_URL') 
    if not _db_url:
        raise RuntimeError(
            "No database URL configured for production. "
            "Set the POSTGRES_DB_DATABASE_URL or DATABASE_URL environment variable "
            "to a PostgreSQL connection string in your Vercel project settings."
        )
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url