# ── Base Image ─────────────────────────────────────────────────────────────────
FROM python:3.10-slim AS base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (build-essential for compiling embeddings if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# ── Backend Stage ─────────────────────────────────────────────────────────────
FROM base AS backend

# Expose FastAPI backend port
EXPOSE 8000

# Run FastAPI backend app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ── Frontend Stage ────────────────────────────────────────────────────────────
FROM base AS frontend

# Expose Streamlit frontend port
EXPOSE 8501

# Run Streamlit dashboard
CMD ["streamlit", "run", "frontend/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
