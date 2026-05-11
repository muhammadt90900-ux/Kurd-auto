import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///kurdauto.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    GMAIL_USER = os.environ.get('GMAIL_USER', '')
    GMAIL_PASS = os.environ.get('GMAIL_PASS', '')

    # Payment gateways
    FASTPAY_STORE_ID = os.environ.get('FASTPAY_STORE_ID', '')
    FASTPAY_STORE_PASSWORD = os.environ.get('FASTPAY_STORE_PASSWORD', '')
    FASTPAY_BASE_URL = os.environ.get('FASTPAY_BASE_URL', 'https://staging-apigw-merchant.fast-pay.iq')
    NASS_USERNAME = os.environ.get('NASS_USERNAME', '')
    NASS_PASSWORD = os.environ.get('NASS_PASSWORD', '')
    NASS_ENVIRONMENT = os.environ.get('NASS_ENVIRONMENT', 'UAT')
    FIB_API_KEY = os.environ.get('FIB_API_KEY', '')
    FIB_API_SECRET = os.environ.get('FIB_API_SECRET', '')
    FIB_BASE_URL = os.environ.get('FIB_BASE_URL', 'https://fib.dev.fib.iq')
