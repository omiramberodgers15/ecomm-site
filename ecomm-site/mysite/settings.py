from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file if present

BASE_DIR = Path(__file__).resolve().parent.parent

# Use environment variables for secrets
SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    # Django default apps
    'django.contrib.admin',
    'django.contrib.sites',  # required by allauth
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Your apps
    'cart',
    'core',
    'payments',
    'chat',

    # Allauth apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

# =============================
# AUTHENTICATION / ALLAUTH
# =============================
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Default
    'allauth.account.auth_backends.AuthenticationBackend',  # Allauth
]

SITE_ID = 1

# URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/cart/checkout/'       # redirect after login
LOGOUT_REDIRECT_URL = '/'                     # redirect after logout

ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_QUERY_EMAIL = True

ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']

ACCOUNT_LOGIN_REDIRECT_URL = '/cart/checkout/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_SIGNUP_REDIRECT_URL = '/cart/checkout/'

# Google OAuth
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.environ.get("GOOGLE_CLIENT_ID", ""),
            'secret': os.environ.get("GOOGLE_CLIENT_SECRET", ""),
            'key': ''
        }
    }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = f"Ecomm Marketplace <{EMAIL_HOST_USER}>"

# DPO Payment Settings
DPO_MERCHANT_ID = os.environ.get("DPO_MERCHANT_ID", "")
DPO_API_KEY = os.environ.get("DPO_API_KEY", "")
DPO_SITE_NAME = os.environ.get("DPO_SITE_NAME", "")
DPO_PAYMENT_URL = 'https://payments.dpo.co.ug/v1/checkout'
DPO_END_POINT = "https://sandbox.dpo.co.ke/"
DPO_PUBLIC_KEY = os.environ.get("DPO_PUBLIC_KEY", "")
DPO_SECRET_KEY = os.environ.get("DPO_SECRET_KEY", "")
DPO_COMPANY_TOKEN = os.environ.get("DPO_COMPANY_TOKEN", "")
DPO_PAYMENT_CURRENCY = "UGX"
DPO_PAYMENT_TIME_LIMIT = 30
DPO_SERVICE_TYPE = "express"
