# Mahjong Winner

[Website](https://joanne-09.github.io/Mahjong-Winner/)

Mahjong Winner is a full-stack web application that uses computer vision to recognize Mahjong tiles from images and calculate game state. The app features real-time synchronization between players during a match.

## Tech Stack

### Frontend
- **Framework:** React 19 + TypeScript
- **Bundler:** Vite
- **Networking:** Axios (REST), Socket.IO Client (Real-time updates)
- **Deployment:** GitHub Pages

### Backend
- **Core:** Python 3.10 + Flask
- **Machine Learning:** PyTorch + YOLOv11 (Ultralytics) for object detection
- **Real-time:** Flask-SocketIO (Eventlet)
- **Database:** SQLAlchemy (SQLite locally)
- **Deployment:** Docker container deployed on Render (images hosted on GitHub Container Registry)

## Local Development

### 1. Prerequisites
- Node.js (v20+)
- Python (v3.10+)
- Git

### 2. Backend Setup
The backend runs the YOLO inference engine and socket server.

```bash
# 1. Navigate to your project root, then create a virtual environment
python -m venv venv

# 2. Activate the environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the Flask server 
# It will automatically run on http://127.0.0.1:5000
python backend/app.py
```

### 3. Frontend Setup
In a **new terminal window**, set up the React client.

```bash
# 1. Navigate to the frontend folder
cd frontend

# 2. Install Node dependencies
npm install

# 3. Start the Vite dev server
# It will proxy API requests to http://127.0.0.1:5000 by default (via config)
npm run dev
```
Open the `http://localhost:5173` URL shown in your terminal to view the app!


## Deployment Guide

This project is configured with a fully automated CI/CD pipeline using GitHub Actions.

### 1. Backend Deployment (Render & Docker)
The backend is packaged into a Docker container and stored in the GitHub Container Registry (`ghcr.io`).

1. **GitHub Package Visibility:** Make sure your `mahjong-backend` package inside your repository is set to **Public** visibility.
2. **Action Trigger:** Any push to the `master` branch that modifies `backend/**`, `Dockerfile`, or `requirements.txt` will automatically build and publish a new Docker image.
3. **Render Deployment:**
   - Go to [Render.com](https://render.com) and create a **New Web Service**.
   - Select "Existing image" and input your GitHub image URL: `ghcr.io/YOUR_GITHUB_USERNAME/mahjong-winner/mahjong-backend:latest`.
   - Render will pull and run the backend!

### 2. Frontend Deployment (GitHub Pages)
The Vite frontend compiles static assets and serves them globally for free via GitHub Pages.

1. **Configure Repository Secret:**
   - Before deploying, go to your GitHub Repo -> **Settings** -> **Secrets and variables** -> **Actions**.
   - Create a new secret called `BACKEND_API_URL`.
   - Set the value to your deployed Render URL (e.g., `https://mahjong-backend-xyz.onrender.com`). *Do not include a trailing slash.*
2. **Enable Pages permission:**
   - Go to Repo -> **Settings** -> **Pages**.
   - Set the source to **GitHub Actions**.
3. **Action Trigger:**
   - Any push to the `master` branch modifying `frontend/**` triggers the builder.
   - Vite will statically inject the `BACKEND_API_URL` during build.
   - The result is automatically published to your GitHub Pages URL!
