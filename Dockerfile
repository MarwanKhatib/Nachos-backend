FROM python:3.11-slim

WORKDIR /app

# --- Add build dependencies ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libssl-dev \
    libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Set non-secret environment variable defaults
ENV DJANGO_SETTINGS_MODULE=backend.settings
ENV PORT=8000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

CMD ["/bin/bash", "start.sh"]
