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
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///mealmind.db')

class ProductionConfig(Config):
    _db_url = os.getenv('POSTGRES_DB_DATABASE_URL')
    if not _db_url:
        raise RuntimeError(
            "No database URL configured for production. "
            "Set the POSTGRES_DB_DATABASE_URL environment variable "
            "to a PostgreSQL connection string in your Vercel project settings."
        )
    # Vercel/Neon supplies 'postgres://' — SQLAlchemy 1.4+ requires 'postgresql://'
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

    try:
        from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

        _parsed = urlparse(_db_url)
        _qs = parse_qs(_parsed.query)
        _qs.pop('channel_binding', None)

        if _parsed.hostname and _parsed.hostname.startswith('ep-'):
            _endpoint_id = _parsed.hostname.split('.')[0]
            existing_options = (_qs.get('options') or [''])[0]
            if f'endpoint={_endpoint_id}' not in existing_options:
                new_options = f'endpoint={_endpoint_id}'
                if existing_options:
                    new_options = existing_options + ' ' + new_options
                _qs['options'] = [new_options]

        _db_url = urlunparse(_parsed._replace(query=urlencode(_qs, doseq=True)))
    except Exception:
        pass

    SQLALCHEMY_DATABASE_URI = _db_url