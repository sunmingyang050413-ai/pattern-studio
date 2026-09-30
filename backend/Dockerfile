FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jre-headless tini && rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYSPARK_PYTHON=/usr/local/bin/python PYTHONPATH=/app
WORKDIR /app
COPY backend/requirements.txt backend/requirements-lock.txt ./
RUN pip install --no-cache-dir -r requirements-lock.txt
COPY backend/ .
COPY scripts/ ./scripts/
RUN useradd --uid 10001 --create-home app && mkdir -p /data && chown -R app:app /app /data
USER app
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "30"]
