"""Railway Web Frontend Settings"""
from server.conf.base_settings import *
import dj_database_url

# Database connection
DATABASES = {
    "default": dj_database_url.config(conn_max_age=600)
}

# Game backend WebSocket address
GAME_WEBSOCKET_URL = config(
    "GAME_WEBSOCKET_URL",
    default="wss://game.your-domain.com/ws"
)

# Static files - use BASE_DIR from Evennia settings
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Allowed hosts
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*", cast=Csv())

# Security settings - disable SSL redirect since Railway handles SSL
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# Disable these for Railway proxy environment
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Debug mode
DEBUG = config("DEBUG", default=False, cast=bool)