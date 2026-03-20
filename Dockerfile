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

ENV PATH="/usr/src/arx/bin:${PATH}"
ENV PYTHONPATH="/usr/src/arx:${PYTHONPATH}"

RUN chmod +x -R /usr/src/arx/bin

# HTTP service (default)
CMD ["start-http"]