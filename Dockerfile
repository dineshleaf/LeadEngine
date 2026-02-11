# Stage 1: Build React frontend
FROM node:20-slim AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + serve frontend
FROM python:3.11-slim

# Install system dependencies for lxml, psycopg2, and DNS
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app ./app

# Copy built frontend into backend/static
COPY --from=frontend-builder /build/frontend/dist ./static

# Python env settings for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Railway provides PORT env var — default to 8000
ENV PORT=8000
EXPOSE 8000

# Use shell form so ${PORT} is expanded at runtime
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --log-level info
