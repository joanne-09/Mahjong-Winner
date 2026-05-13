# Mahjong Winner

[Website](https://joanne-09.github.io/Mahjong-Winner/)

Mahjong Winner is a full-stack web application that uses computer vision to recognize Mahjong tiles from images and calculate game state. The app features real-time synchronization between players during a match.

## Tech Stack

### Frontend
- **Framework:** React 19 + TypeScript
- **Bundler:** Vite
- **Networking:** Axios (REST), Socket.IO Client (Real-time updates)
- **Deployment:** Static build served by Nginx in Docker; GitHub Pages is still possible for frontend-only hosting

### Backend
- **Core:** Python 3.10 + Flask
- **Machine Learning:** PyTorch + YOLOv11 (Ultralytics) for object detection
- **Real-time:** Flask-SocketIO (Eventlet)
- **Database:** SQLAlchemy with SQLite locally or Postgres via `DATABASE_URL`
- **Production DB:** Neon Postgres is recommended for now
- **Deployment:** Docker Compose on an Oracle Cloud Always Free Ampere A1 VM, with Nginx as the reverse proxy

## Local Development

### 1. Prerequisites
- Node.js (v20+)
- Python (v3.10+)
- Git

### 2. Backend Setup
The backend runs the YOLO inference engine, REST API, socket server, and database models.

By default, local development uses SQLite. To use Neon or another Postgres database, set `DATABASE_URL` before starting the backend.

```bash
python -m venv venv
pip install -r requirements.txt
```

Activate the environment:

```powershell
venv\Scripts\activate
```

```bash
source venv/bin/activate
```

Optional: use Neon/Postgres instead of local SQLite.

```powershell
$env:DATABASE_URL="postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require"
```

```bash
export DATABASE_URL="postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require"
```

Start the Flask server:

```bash
python backend/app.py
```

It runs on `http://127.0.0.1:5000`.

You can also put local backend environment variables in `backend/.env`. The app falls back to `sqlite:///local_development.db` when `DATABASE_URL` is not set.

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

The recommended production setup is:

- Oracle Cloud Always Free Ampere A1 VM for the app, Docker Compose, Nginx, image uploads, and generated result files.
- Neon Postgres for the database.

You do not need to move the database to Oracle right now. Neon is a managed Postgres service, so you do not have to maintain backups, upgrades, or a database container on the VM. Keeping the DB on Neon and the app on Oracle is the simplest reliable setup for this project.

Moving the DB into Oracle only makes sense if you specifically want everything under one cloud account, lower latency inside Oracle, or no external managed database. The tradeoff is more operations work. Oracle Autonomous Database is not a drop-in Postgres replacement for this app, and running your own Postgres container on the VM means you must manage backups and recovery yourself.

### 1. Database Setup (Neon)

1. Create or open your Neon project.
2. Copy the Postgres connection string.
3. Prefer the pooled connection string if Neon provides one and you expect multiple app instances later.
4. Make sure the URL includes SSL, for example:

```text
postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

The backend reads this value from `DATABASE_URL`. SQLAlchemy creates the current tables automatically on app startup with `db.create_all()`.

### 2. Backend Deployment (Oracle VM + Docker Compose)

Follow the Oracle VM guides:

- [Oracle Cloud VM setup](./deploy/oracle/VM_SETUP.md)
- [GitHub Actions A1 retry script](./deploy/oracle/VM_SCRIPT.md)
- [Oracle deployment steps](./deploy/oracle/VM_DEPLOY.md)

On the VM, clone the repo and create `.env` at the project root:

```bash
cp .env.example .env
nano .env
```

Set at least:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
MEDIA_RETENTION_SECONDS=3600
MAX_UPLOAD_MB=8
```

Start the stack:

```bash
docker compose up -d --build
docker compose logs -f backend
```

The backend listens only inside Docker. Nginx exposes the app on port `80` and proxies API, media, and Socket.IO traffic to the backend.

### 3. Runtime Media

Uploaded and generated images are stored in the Docker named volume `mahjong_data`, not in `backend/static`.

- Uploads: `/data/media/uploads`
- Generated outputs: `/data/media/outputs`
- Public URL path: `/media/...`
- Cleanup TTL: `MEDIA_RETENTION_SECONDS`

This keeps user files out of git and avoids filling the source tree on the VM.

### 4. Frontend Deployment

For Oracle VM deployment, the frontend is built into the Nginx image by `docker compose up -d --build`, so you do not need GitHub Pages.

If you still want to deploy the frontend separately on GitHub Pages, set the frontend build variable `VITE_API_URL` or the GitHub Actions secret used by your frontend workflow to your backend URL.
