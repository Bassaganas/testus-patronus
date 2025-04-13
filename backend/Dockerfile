# syntax=docker/dockerfile:1.4
FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install basic tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    black \
    flake8 \
    mypy \
    isort \
    pylint

# Create non-root user
RUN useradd -m -s /bin/bash vscode \
    && chown -R vscode:vscode /app

USER vscode

# Production stage
FROM base as production
COPY . /app
RUN mkdir -p /app/data/db /app/data/uploads
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 