FROM python:3.11

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

# Install nginx for WebSocket proxy (used by WS service)
RUN apt-get update && apt-get install -y nginx gettext-base && rm -rf /var/lib/apt/lists/*

# Copy nginx configs
COPY docker/nginx-ws.conf /etc/nginx/nginx-ws.conf.template

ENV PATH="/usr/src/arx/bin:${PATH}"
ENV PYTHONPATH="/usr/src/arx:${PYTHONPATH}"

RUN chmod +x -R /usr/src/arx/bin

# Universal start script - detects service type from DJANGO_SETTINGS_MODULE
CMD ["start-railway"]