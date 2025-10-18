from . import get_env_variable


DEBUG = True

ROOT_URLCONF = 'Streamvault.urls'

SECRET_KEY = get_env_variable("SECRET_KEY")

ALLOWED_HOSTS = get_env_variable("ALLOWED_HOSTS")

ADMIN_SITE_URL = get_env_variable("ADMIN_SITE_URL")
