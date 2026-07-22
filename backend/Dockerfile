# ==========================================
# BASE STAGE
# ==========================================
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ==========================================
# DEVELOPMENT STAGE
# ==========================================
FROM base AS development

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command to run development server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==========================================
# PRODUCTION STAGE
# ==========================================
FROM base AS production

# Copy application code
COPY . .

# Create a non-privileged user and adjust permissions
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Command to run production server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
