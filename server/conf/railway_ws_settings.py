"""
Railway WebSocket Service Settings
Exposes Evennia WebSocket on Railway's $PORT via HTTP+WebSocket proxy
"""
import os
from server.conf.base_settings import *
import dj_database_url

# Database connection - use DATABASE_URL from Railway
DATABASES = {
    "default": dj_database_url.config(conn_max_age=600)
}

# =============================================================================
# Network Configuration for WebSocket Service
# =============================================================================

# Disable Telnet
TELNET_PORTS = []
TELNET_INTERFACES = []

# AMP - internal communication between Server and Portal
AMP_PORT = 4006
AMP_INTERFACE = "127.0.0.1"

# WebSocket - Evennia listens on 8001, proxy forwards from 4002
WEBSOCKET_CLIENT_PORT = 8001  # Internal WebSocket port (different from external)
WEBSOCKET_CLIENT_INTERFACE = "127.0.0.1"  # Internal only
# URL for webclient to connect
WEBSOCKET_CLIENT_URL = config(
    "WEBSOCKET_CLIENT_URL",
    default="wss://claw-jianghu-ws.up.railway.app"
)

# Web server - runs internally for proxying
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

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Ensure webclient is enabled
WEBCLIENT_ENABLED = True
WEBSOCKET_CLIENT_ENABLED = True