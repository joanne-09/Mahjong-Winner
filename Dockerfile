FROM python:3.10-slim

WORKDIR /app
ENV MEDIA_ROOT=/data/media \
    UPLOAD_FOLDER=/data/media/uploads \
    OUTPUT_FOLDER=/data/media/outputs \
    MEDIA_RETENTION_SECONDS=3600 \
    MAX_UPLOAD_MB=8

# Install system dependencies required for OpenCV, PyTorch, etc.
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies (use no-cache to keep image small)
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./backend/

WORKDIR /app/backend

# Inform Docker that the container listens on the specified port
EXPOSE 5000
VOLUME ["/data"]

# Use Gunicorn with eventlet to support Flask-SocketIO
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=5)"]
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--timeout", "300", "--bind", "0.0.0.0:5000", "app:app"]
