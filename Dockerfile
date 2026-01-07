FROM python:3.12-slim AS builder
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOG_FILE=/app/logs/app.log

RUN useradd -m appuser

COPY --from=builder /install /usr/local

WORKDIR /app
COPY . .

RUN mkdir -p /app/logs \
    && chown -R appuser:appuser /app/logs \
    && chmod +x scripts/start.sh

USER appuser