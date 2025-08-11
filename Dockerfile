# Multi-stage Dockerfile for LLM-Based Multi-Database Chatbot System
# Stage 1: Build stage with optimized base
FROM python:3.9-slim as builder
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_DISABLE_TELEMETRY=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install only essential build dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies globally (not --user)
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage with minimal footprint
FROM python:3.9-slim as runtime
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_DISABLE_TELEMETRY=1
ENV PYTHONUNBUFFERED=1

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

WORKDIR /app

# Copy Python packages from builder (global installation)
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files
COPY main.py .
COPY static/ ./static/
COPY templates/ ./templates/
COPY data/ ./data/
COPY healthcare.db ./data/healthcare.db
COPY requirements.txt .
COPY runtime.txt .

# Debug: List contents to see what was copied
RUN ls -la /app && echo "=== Data directory contents ===" && ls -la /app/data/ || echo "Data directory not found"

# Create app user and set permissions
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

# Switch to app user
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
