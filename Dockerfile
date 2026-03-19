FROM python:3.11

WORKDIR /usr/src

# Install Nginx for port unification
RUN apt-get update && apt-get install -y nginx gettext-base && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/TehomCD/evennia.git
RUN pip install -e evennia

WORKDIR /usr/src/arx

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Copy Nginx configuration
COPY docker/nginx.conf /etc/nginx/nginx.conf.template

RUN mkdir -p server/logs
RUN mkdir -p /var/logs

ENV PATH="/usr/src/arx/bin:${PATH}"
ENV PYTHONPATH="/usr/src/arx:${PYTHONPATH}"

RUN chmod +x -R /usr/src/arx/bin

# Create startup script that runs both Nginx and Evennia
RUN echo '#!/bin/bash\n\
set -e\n\
export PORT=${PORT:-8080}\n\
envsubst "\\$PORT" < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf\n\
echo "Starting Nginx on port $PORT..."\n\
nginx\n\
echo "Starting Evennia..."\n\
exec start\n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]