FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir \
    fastapi==0.116.1 \
    uvicorn[standard]==0.35.0 \
    sqlalchemy==2.0.43 \
    "psycopg[binary]==3.2.9" \
    alembic==1.16.4 \
    pydantic==2.11.7 \
    pydantic-settings==2.10.1 \
    celery==5.5.3 \
    redis==6.4.0 \
    httpx==0.28.1 \
    python-multipart==0.0.20 \
    Pillow==11.3.0 \
    numpy==2.1.3 \
    google-auth-oauthlib==1.2.1 \
    google-api-python-client==2.149.0 \
    google-auth-httplib2==0.2.0 \
    requests==2.32.3

COPY . /app
