FROM python:3.11
LABEL authors="joslinthomas"

WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential \
    librdkafka-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ENVIRONMENT=docker

# Streamlit runs on port 8501 by default
CMD ["streamlit", "run", "apps_to_run/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
