# 🌌 OMNISPHERE DOCKERFILE 🌌
# Multi-stage Alpine + Python slim build for production

# Build stage
FROM python:3.10-alpine AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    python3-dev \
    postgresql-dev \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev \
    harfbuzz-dev \
    fribidi-dev \
    libimagequant-dev \
    libxcb-dev \
    libpng-dev \
    git \
    cmake \
    make \
    g++ \
    linux-headers

# Copy requirements files
COPY requirements.txt requirements.in ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip pip-tools && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.10-alpine AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Create non-root user
RUN addgroup -g 1001 -S omnisphere && \
    adduser -S omnisphere -u 1001 -G omnisphere

# Install runtime dependencies
RUN apk add --no-cache \
    postgresql-client \
    jpeg \
    zlib \
    freetype \
    lcms2 \
    openjpeg \
    tiff \
    tk \
    tcl \
    harfbuzz \
    fribidi \
    libimagequant \
    libxcb \
    libpng \
    ffmpeg \
    curl \
    && rm -rf /var/cache/apk/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=omnisphere:omnisphere . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/uploads && \
    chown -R omnisphere:omnisphere /app

# Switch to non-root user
USER omnisphere

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Development stage (optional)
FROM production AS development

# Switch back to root for development tools
USER root

# Install development dependencies
RUN apk add --no-cache \
    vim \
    bash \
    git \
    openssh-client

# Copy development requirements and install
COPY requirements-dev.in ./
RUN pip install --no-cache-dir pip-tools && \
    pip-compile requirements-dev.in && \
    pip install --no-cache-dir -r requirements-dev.txt

# Switch back to app user
USER omnisphere

# Override command for development
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
