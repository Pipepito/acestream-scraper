# Stage 1: Build frontend
FROM node:20-slim as frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY ../frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend source code
COPY ../frontend/ ./

# Build the frontend
RUN npm run build

# Stage 2: Build backend with frontend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FRONTEND_BUILD_PATH=frontend_build

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Create frontend build directory
RUN mkdir -p frontend_build

# Copy the built frontend from the frontend-builder stage
COPY --from=frontend-builder /app/frontend/build/ /app/frontend_build/

# Set up entrypoint
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
