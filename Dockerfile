# Stage 1: Base image for Python 3.8+ on Alpine
FROM python:3.11-alpine AS python-env

# Set environment variables for consistent builds
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PARQET_DATA_DIR=/app/data \
    PARQET_OUTPUT_DIR=/app/output \
    PARQET_LOG_DIR=/app/logs \
    PARQET_CONFIG_FILE=/app/config.json \
    PARQET_TIMEZONE=Europe/Zurich \
    PARQET_LOG_LEVEL=INFO \
    PARQET_LOG_TO_CONSOLE=true

# Install system dependencies required for pdfplumber
RUN apk add --no-cache \
    bash \
    build-base \
    gcc \
    libffi-dev \
    musl-dev \
    openssl-dev \
    python3-dev \
    py3-pip \
    runit \
    doas \
    jpeg-dev \
    zlib-dev \
    && pip install --no-cache-dir --upgrade pip

# Copy and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Add runtime arguments for user and group IDs
ARG DDE_UID=1000
ARG DDE_GID=1000

# Create app directory structure
RUN mkdir -p /app/data /app/output /app/logs

# Create a dummy configure script if none exists
RUN echo '#!/bin/sh' > /tmp/configure-image-default.sh && \
    echo 'echo "Using default configuration - no DDE setup"' >> /tmp/configure-image-default.sh && \
    chmod +x /tmp/configure-image-default.sh

# Try to copy DDE and rootfs files (will fail silently if they don't exist)
# We'll handle this in the RUN command
COPY .dde/configure-image.sh /tmp/configure-image.sh
COPY rootfs/base/ /tmp/rootfs/

# Run configuration script
RUN if [ -f /tmp/configure-image.sh ]; then \
        chmod +x /tmp/configure-image.sh && \
        /tmp/configure-image.sh && \
        echo "DDE configuration applied"; \
    else \
        /tmp/configure-image-default.sh; \
    fi && \
    if [ -d /tmp/rootfs ] && [ "$(ls -A /tmp/rootfs)" ]; then \
        cp -r /tmp/rootfs/* / && \
        echo "Rootfs files copied"; \
    fi && \
    rm -rf /tmp/.dde /tmp/rootfs /tmp/configure-image*.sh

# Set working directory
WORKDIR /app

# Copy application code
COPY app/ /app/app/
COPY tests/ /app/tests/

# Copy config example (user should provide actual config)
COPY .env.example /app/.env.example

# Create placeholder config.json
RUN echo '{}' > /app/config.json.example

# Set permissions
RUN chown -R ${DDE_UID}:${DDE_GID} /app 2>/dev/null || true

# Default command to run the parser
CMD ["python", "-m", "app.main"]
