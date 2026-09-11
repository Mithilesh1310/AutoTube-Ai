# AutoTube AI Backend Dockerfile
FROM python:3.11-slim

# Install FFmpeg and system dependencies for multimedia rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend codebase
COPY backend/ /app/backend/

# Create persistent storage directories
RUN mkdir -p /app/storage/channels /app/storage/videos /app/storage/temp

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

# Run FastAPI production server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
