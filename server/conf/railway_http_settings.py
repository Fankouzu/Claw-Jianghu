"""
Railway HTTP Service Settings
Exposes Evennia webserver on Railway's $PORT
"""
import os
from server.conf.base_settings import *
import dj_database_url

# Database connection - use DATABASE_URL from Railway
DATABASES = {
    "default": dj_database_url.config(conn_max_age=600)
}

# =============================================================================
# Network Configuration for HTTP Service
# =============================================================================

# Disable Telnet
TELNET_PORTS = []
TELNET_INTERFACES = []

# AMP - internal communication between Server and Portal
AMP_PORT = 4006
AMP_INTERFACE = "127.0.0.1"

# WebSocket - runs on internal port, clients connect via separate WS service
# Disable WebSocket on this service - it will be handled by the WS service
WEBSOCKET_CLIENT_PORT = 8001  # Internal only, won't be exposed
WEBSOCKET_CLIENT_INTERFACE = "127.0.0.1"  # Internal only
# URL for webclient to connect - points to the separate WS service
WEBSOCKET_CLIENT_URL = config(
    "WEBSOCKET_CLIENT_URL",
    default="wss://claw-jianghu-ws.up.railway.app"
)

# Web server (Portal HTTP) - expose on Railway's PORT
# Railway provides PORT environment variable
RAILWAY_PORT = int(os.environ.get("PORT", "4001"))
WEBSERVER_PORTS = [(RAILWAY_PORT, 5001)]
WEBSERVER_INTERFACES = ["0.0.0.0"]

# =============================================================================
# Security Settings
# =============================================================================

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*", cast=Csv())

# Trust Railway's proxy headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Debug mode
DEBUG = config("DEBUG", default=False, cast=bool)

# =============================================================================
# Session Configuration
# =============================================================================

# Allow sessions to work through proxy
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Ensure webclient is enabled
WEBCLIENT_ENABLED = True
WEBSOCKET_CLIENT_ENABLED = True