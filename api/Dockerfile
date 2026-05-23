FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    APP_BASE_URL=http://127.0.0.1:8010 \
    WEB_ORIGIN=http://127.0.0.1:5173 \
    DATA_DIR=/data

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /data/uploads /data/frames /data/exports \
    && chown -R appuser:appuser /data /app

USER appuser

EXPOSE 8010
VOLUME ["/data"]

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
