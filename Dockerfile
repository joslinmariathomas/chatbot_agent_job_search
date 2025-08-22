FROM python:3.11
LABEL authors="joslinthomas"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ENVIRONMENT=docker
CMD ["python", "main.py"]
