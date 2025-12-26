# Builder stage
# Builder stage
FROM python:3.11-slim as builder


# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Install dependencies to user directory to easily avoid test packages if needed,
# or just for clean separation. Here we install everything but could filter.
RUN pip install --no-cache-dir --no-compile --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (runtime only)
# libpq5 for PostgreSQL
# ffmpeg for video processing
# libmagic1 for python-magic
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Cloud Run expects the container to listen on $PORT (default 8080)
# We use 'exec' to ensure gunicorn receives signals correctly.
# We bind to 0.0.0.0:$PORT
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 4 app:create_app()