"""
Railway game backend settings
Configured for single-port deployment via Nginx proxy
"""
from server.conf.base_settings import *
import dj_database_url

# Database connection - use DATABASE_URL from Railway
DATABASES = {
    "default": dj_database_url.config(conn_max_age=600)
}

# =============================================================================
# Network Configuration for Railway (single port via Nginx)
# =============================================================================

# Disable Telnet - Railway only uses web
TELNET_PORTS = []
TELNET_INTERFACES = []

# AMP - internal communication between Server and Portal
AMP_PORT = 4006
AMP_INTERFACE = "127.0.0.1"

# WebSocket - internal, proxied by Nginx at /ws path
WEBSOCKET_CLIENT_PORT = 4002
WEBSOCKET_CLIENT_INTERFACE = "127.0.0.1"
# This URL is used by the webclient to connect. Must match Nginx /ws location
# Set WEBSOCKET_CLIENT_URL env var to: wss://your-game-domain.com/ws
WEBSOCKET_CLIENT_URL = config(
    "WEBSOCKET_CLIENT_URL",
    default=None  # Must be set via environment variable
)

# Web server (Portal HTTP) - internal, proxied by Nginx
# Format: (external_port, internal_port)
WEBSERVER_PORTS = [(4001, 5001)]
WEBSERVER_INTERFACES = ["127.0.0.1"]

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