from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url



# BASE DIRECTORY
# --------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
# Load .env BEFORE using env variables

load_dotenv(BASE_DIR / '.env') 

DATABASE_URL = os.environ.get("DATABASE_URL")

# --------------------------


# --------------------------
# SECURITY
# --------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")
#DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = ['ecomm-site-production.up.railway.app']
CSRF_TRUSTED_ORIGINS = ['https://ecomm-site-production.up.railway.app']

DEBUG = os.getenv('DEBUG') == 'True'

# --------------------------
# URL CONFIGURATION
# --------------------------
ROOT_URLCONF = 'mysite.urls'

# --------------------------
# INSTALLED APPS
# --------------------------
INSTALLED_APPS = [
    # Django default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # required by allauth
    'whitenoise.runserver_nostatic',

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

# --------------------------
# MIDDLEWARE
# --------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # Allauth middleware (required)
    'allauth.account.middleware.AccountMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# --------------------------
# TEMPLATES
# --------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # create 'templates' folder
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # required for admin & allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.categories_processor',


            ],
        },
    },
]

# --------------------------
# AUTHENTICATION / ALLAUTH
# --------------------------
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # default
    'allauth.account.auth_backends.AuthenticationBackend',  # allauth
]

SITE_ID = 1

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/cart/checkout/'
LOGOUT_REDIRECT_URL = '/'

ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_QUERY_EMAIL = True
ACCOUNT_SIGNUP_FIELDS = ['username', 'email', 'password1', 'password2']
ACCOUNT_LOGIN_METHOD = "email"  # or "username"
# then adjust ACCOUNT_SIGNUP_FIELDS accordingly



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


# --------------------------
# CART SETTINGS
# --------------------------
CART_SESSION_ID = 'cart'

# --------------------------
# DATABASES
# --------------------------

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True
    )
}



# --------------------------
# STATIC & MEDIA FILES
# --------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# --------------------------
# EMAIL SETTINGS
# --------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = f"WaziTrade Marketplace <{EMAIL_HOST_USER}>"

# --------------------------
# DPO PAYMENT SETTINGS
# --------------------------
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
