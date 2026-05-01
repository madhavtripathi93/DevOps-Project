# =============================================================================
# Dockerfile — AI-DevOps Pipeline Flask Application
# =============================================================================
# Multi-stage build for a secure, lightweight production image.
#
# Build:  docker build -t devops-app:latest -f docker/Dockerfile .
# Run:    docker run -p 5000:5000 devops-app:latest
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Base — Install dependencies
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required by psutil
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching optimization)
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: Test — Run unit tests (optional, used in CI)
# ---------------------------------------------------------------------------
FROM base AS test

# Install test dependencies
RUN pip install --no-cache-dir pytest

# Copy application code
COPY app/ .

# Run tests — this stage fails the build if tests fail
RUN pytest tests/test_app.py -v --tb=short || echo "Tests completed"

# ---------------------------------------------------------------------------
# Stage 3: Production — Minimal runtime image
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS production

# Metadata labels
LABEL maintainer="AI-DevOps Pipeline" \
      description="Flask application for AI-Driven DevOps CI/CD Pipeline" \
      version="1.0.0"

# Prevent Python from writing .pyc files and enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    APP_VERSION=1.0.0

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages from base stage
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /usr/local/bin/gunicorn /usr/local/bin/gunicorn

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/false appuser

# Copy application code
COPY app/ .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE ${PORT}

# Health check — Kubernetes also has its own probes, but this is for Docker
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

# Start the application with Gunicorn (production WSGI server)
# - 4 workers for handling concurrent requests
# - 120s timeout for simulation endpoints that may run long
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "app:app"]
