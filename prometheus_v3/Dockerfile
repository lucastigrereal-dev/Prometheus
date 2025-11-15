# ============================================================================
# PROMETHEUS V3 - DOCKERFILE
# Multi-stage build for optimized production image
# ============================================================================

# Stage 1: Builder
FROM python:3.11-slim as builder

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================================
# Stage 2: Runtime
FROM python:3.11-slim

# Labels
LABEL maintainer="Prometheus Team"
LABEL version="3.0"
LABEL description="Prometheus V3 - Universal AI Assistant"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PROMETHEUS_ENV=production \
    PORT=8000

# Create user
RUN useradd -m -u 1000 prometheus && \
    mkdir -p /app /app/data /app/logs /app/backups && \
    chown -R prometheus:prometheus /app

# Set work directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    ffmpeg \
    tesseract-ocr \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/prometheus/.local

# Copy application
COPY --chown=prometheus:prometheus . .

# Make scripts executable
RUN chmod +x scripts/*.sh

# Switch to prometheus user
USER prometheus

# Add local bin to PATH
ENV PATH=/home/prometheus/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Volumes
VOLUME ["/app/data", "/app/logs", "/app/backups"]

# Expose ports
EXPOSE 8000 9090

# Entry point
ENTRYPOINT ["python", "-m", "prometheus_v3"]

# Default command
CMD ["--mode", "production"]
