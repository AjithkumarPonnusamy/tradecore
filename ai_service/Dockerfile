FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (ffmpeg is required for audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy source code
COPY . .

# Create a non-privileged user and adjust permissions
RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /root/.cache/huggingface \
    && chown -R appuser:appuser /app /root/.cache

USER appuser

# Expose port for FastAPI
EXPOSE 8001

# Container Healthcheck
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

