# Retador v2.0 - Dockerfile
# Multi-stage build for optimized production image

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Production
# ============================================
FROM python:3.11-slim as production

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 retador \
    && useradd --uid 1000 --gid retador --shell /bin/bash --create-home retador

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=retador:retador src/ ./src/
COPY --chown=retador:retador scripts/ ./scripts/
COPY --chown=retador:retador pyproject.toml .

# Install package in editable mode
RUN pip install -e .

# Switch to non-root user
USER retador

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "-m", "scripts.run"]
