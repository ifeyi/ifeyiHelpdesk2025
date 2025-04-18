import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _
# Add these imports at the top of your settings.py
import ldap
from django_auth_ldap.config import LDAPSearch, ActiveDirectoryGroupType, GroupOfNamesType
import logging

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Read secret from file
def read_secret(secret_name):
    filename = os.environ.get(f'{secret_name}_FILE')
    if filename and os.path.isfile(filename):
        with open(filename) as f:
            return f.read().strip()
    return os.environ.get(secret_name, '')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = read_secret('django_secret_key') or 'django-insecure-key-for-dev'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = ['*']  # Allow all hosts for development

# Application definition
INSTALLED_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'corsheaders',
    'django_prometheus',
    #'debug_toolbar',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'drf_yasg',
    'crispy_forms',
    'crispy_bootstrap5', 
    
    # Local apps
    'accounts',
    'tickets',
    'articles',
    'comments',
    'core',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'helpdesk.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.global_context',
            ],
        },
    },
]

# Changed to match the project structure
WSGI_APPLICATION = 'helpdesk.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'cfchelpdeskdb'),
        'USER': os.environ.get('DB_USER', 'cfchelpdeskuser'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'cfcD_bl0cag5sPass'),
        'HOST': os.environ.get('DB_HOST', 'postgres'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Use a simple SQLite database for development/testing
if os.environ.get('USE_SQLITE', 'False').lower() == 'true':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Cache settings - use local memory cache for now to simplify things
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Authentication
AUTH_USER_MODEL = 'accounts.User'

# Django AllAuth Config
SITE_ID = 1
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Changed to 'none' for easier development

# Internationalization
LANGUAGE_CODE = 'en'  # default language

LANGUAGES = [
    ('en', _('English')),
    ('fr', _('Français')),
]

MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
MODELTRANSLATION_LANGUAGES = ('en', 'fr')

TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Rest Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
}

# Django Debug Toolbar
INTERNAL_IPS = ['127.0.0.1']

# CORS settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',
    'http://localhost',
]

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'accounts:ldap'

# Security settings - disabled for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Active Directory Authentication Configuration
# ---------------------------------------------

# LDAP server URI
AUTH_LDAP_SERVER_URI = "ldap://192.168.6.90"  # Replace with your actual AD server address

# Service account for LDAP queries
AUTH_LDAP_BIND_DN = "CN=Ifeyi BATINDEK BATOANEN admin,OU=IT-ADMIN,OU=CFC-Users,DC=creditfoncier,DC=cm"
AUTH_LDAP_BIND_PASSWORD = os.environ.get('AD_BIND_PASSWORD', '@dm1n_CFC')

# User search configuration - adjust the search base to match your AD structure
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "OU=CFC-Users,DC=creditfoncier,DC=cm",  # Base DN - modify to match your AD structure
    ldap.SCOPE_SUBTREE,
    "(sAMAccountName=%(user)s)",  # Filter to find the user
)

# Active Directory specific settings
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0,  # Required for Active Directory
    ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,  # Skip certificate validation if needed
}

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
    "username": "sAMAccountName",  # This is critical - must match login username
}

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "OU=CFC-Users,DC=creditfoncier,DC=cm", 
    ldap.SCOPE_SUBTREE,
    "(objectClass=group)",
)
AUTH_LDAP_GROUP_TYPE = ActiveDirectoryGroupType()

# Replace your current AUTH_LDAP_USER_FLAGS_BY_GROUP section with this:

# Map Active Directory groups to user flags
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_active": "CN=Active Users,OU=CFC-Users,DC=creditfoncier,DC=cm",  # All domain users are active
    "is_staff": "CN=Staff Users,OU=CFC-Users,DC=creditfoncier,DC=cm",   # IT admins are staff
    "is_superuser": "CN=Super Users,OU=CFC-Users,DC=creditfoncier,DC=cm"  # Domain admins are superusers
}

# Add these new settings for mapping AD groups to user types
AUTH_LDAP_FIND_GROUP_PERMS = True

AUTH_LDAP_ALWAYS_UPDATE_USER = True  

AUTHENTICATION_BACKENDS = [
    'accounts.ldap_backend.CustomLDAPBackend',  # Add the LDAP backend first
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Create logs directory if it doesn't exist
log_dir = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure file handler
ldap_handler = logging.FileHandler(os.path.join(log_dir, 'ldap_debug.log'))
ldap_handler.setLevel(logging.DEBUG)

# Add formatter to make logs more readable
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ldap_handler.setFormatter(formatter)

# Optional: Set up logging for troubleshooting LDAP
logger = logging.getLogger('django_auth_ldap')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)  

auth_logger = logging.getLogger('django.contrib.auth')
auth_logger.addHandler(logging.StreamHandler())
auth_logger.setLevel(logging.DEBUG)

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.creditfoncier.cm'  
EMAIL_PORT = 587  
EMAIL_USE_TLS = True  
EMAIL_HOST_USER = 'cfc_cloud@creditfoncier.cm'  
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'Pa$$w0rd')  
DEFAULT_FROM_EMAIL = 'CFC Helpdesk <helpdesk@creditfoncier.cm>'

# For development/testing, you can use the console backend to see emails in the console
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Add this to the TEMPLATES section in settings.py
# Replace the existing context_processors with this updated one
