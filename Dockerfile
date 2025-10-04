# Use official Python image
FROM python:3.10-slim

# Install system dependencies for weasyprint, playwright, and OCR
RUN apt-get update && apt-get install -y \
    # WeasyPrint dependencies
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    # Playwright dependencies
    wget \
    gnupg \
    ca-certificates \
    # OCR dependencies
    tesseract-ocr \
    poppler-utils \
    # Build tools
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install playwright chromium
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Change to app directory
WORKDIR /app/app

# Expose port
EXPOSE 8080

# Start command using shell form to expand $PORT variable
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}
