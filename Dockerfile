FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required for OpenCV, PyTorch, etc.
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies (use no-cache to keep image small)
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./backend/

WORKDIR /app/backend

# Inform Docker that the container listens on the specified port
EXPOSE 5000

# Use Gunicorn with eventlet to support Flask-SocketIO
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "app:app"]
