FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data persistence
RUN mkdir -p /data/output /data/temp /data/vector_db

# Set environment variables
ENV PYTHONPATH=/app
ENV OUTPUT_DIR=/data/output
ENV TEMP_DIR=/data/temp
ENV VECTOR_DB_PATH=/data/vector_db
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "src.api.server"]
