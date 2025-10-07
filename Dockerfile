# Use official Python image
FROM python:3.10-slim

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    wget \
    ca-certificates \
    tesseract-ocr \
    poppler-utils \
    gcc \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install playwright chromium WITHOUT system deps (we installed them above)
RUN playwright install chromium

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Set working directory to app folder
WORKDIR /app/app

# Start command - shell form allows environment variable expansion
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}
