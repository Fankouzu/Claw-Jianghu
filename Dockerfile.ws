FROM python:3.11

# Force rebuild - timestamp: 2026-03-21T01:00:00
ARG REBUILD_TRIGGER=2

WORKDIR /usr/src

RUN git clone https://github.com/TehomCD/evennia.git
RUN pip install -e evennia

WORKDIR /usr/src/arx

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p server/logs
RUN mkdir -p /var/logs

# Install nginx for WebSocket proxy
RUN apt-get update && apt-get install -y nginx gettext-base && rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/src/arx/bin:${PATH}"
ENV PYTHONPATH="/usr/src/arx:${PYTHONPATH}"

RUN chmod +x -R /usr/src/arx/bin

# Copy nginx config for WebSocket
COPY docker/nginx-ws.conf /etc/nginx/nginx.conf.template

# WebSocket service
CMD ["start-ws"]