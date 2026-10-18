# ============================================================
# Smart Health - Google Cloud Run Production Dockerfile
# Multi-stage secure build with non-root runtime
# ============================================================

FROM python:3.13-slim AS runner

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Environment defaults for Cloud Run
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    APP_ENV=production

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Security: Create non-root system user and assign workspace ownership
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup --no-create-home appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8080

# Cloud Run healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/healthz || exit 1

# Launch uvicorn dynamically binding to the port injected by Cloud Run ($PORT)
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
