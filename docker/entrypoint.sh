#!/bin/bash
set -e

# Replace PORT environment variable in nginx config
export PORT=${PORT:-8000}
envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Create necessary directories
mkdir -p /app/server/logs /var/log/nginx

# Start Nginx in background
echo "Starting Nginx..."
nginx

# Start Evennia Server and Portal
# We need to start both, then keep the container running
cd /app

echo "Starting Evennia Server and Portal..."
# Start both server and portal
evennia start --settings=server.conf.railway_settings

# Wait for Evennia to be ready
echo "Waiting for Evennia to start..."
sleep 5

# Check if Evennia is running
if evennia status --settings=server.conf.railway_settings 2>/dev/null | grep -q "running"; then
    echo "Evennia started successfully"
else
    echo "Warning: Evennia status check failed, continuing anyway..."
fi

# Keep container running by following the main log
echo "Container is ready. Following logs..."
exec tail -f /app/server/logs/server.log /app/server/logs/portal.log 2>/dev/null || exec tail -f /dev/null