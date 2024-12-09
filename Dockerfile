# Stage 1: Base image for Python 3.13 on Alpine
FROM python:3.13-alpine AS python-env

# Set environment variables for consistent builds
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
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
    && pip install --no-cache-dir --upgrade pip

# Copy and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Add runtime arguments for user and group IDs
ARG DDE_UID=1000
ARG DDE_GID=1000

# Copy configuration scripts and base files
COPY .dde/configure-image.sh /tmp/configure-image.sh
COPY rootfs/base/ /

# Configure the image (e.g., create users, permissions)
RUN /tmp/configure-image.sh

# Set working directory
WORKDIR $PROJECT_DIR

# Set entrypoint to use runsvdir for service management
ENTRYPOINT ["runsvdir", "-P", "/etc/service"]
