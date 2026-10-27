# Multi-stage production Dockerfile for E-Cüzdan
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY configuration/dependencies/requirements.txt requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

# Final runtime image
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --home-dir /home/ecuzdan --shell /bin/bash ecuzdan

COPY --from=builder /root/.local /home/ecuzdan/.local
ENV PATH=/home/ecuzdan/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application source
COPY --chown=ecuzdan:ecuzdan . /app

# Ensure runtime directories exist with proper permissions
RUN mkdir -p /app/instance /app/logs /app/backups \
    && chown -R ecuzdan:ecuzdan /app

USER ecuzdan

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:5000/healthz || exit 1

CMD ["sh", "-c", "exec gunicorn -b 0.0.0.0:5000 -w ${GUNICORN_WORKERS:-1} --threads ${GUNICORN_THREADS:-4} --worker-class gthread --timeout 120 --access-logfile - --error-logfile - wsgi:app"]
