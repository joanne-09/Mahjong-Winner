# Oracle Cloud Always Free Deployment

This setup is intended for an Oracle Ampere A1 VM, Docker Compose, and the bundled Nginx reverse proxy.

If you have not created the Oracle VM yet, start here first:

[Oracle Cloud VM Setup](./VM_SETUP.md)

If Oracle reports no A1 capacity and you want GitHub Actions to retry while your computer is off:

[GitHub Actions A1 Retry](./VM_SCRIPT.md)

## Recommended VM

- Use an Ampere A1 ARM instance, not the tiny AMD micro instance.
- Give the VM at least 2 OCPU and 8 GB RAM for the first build. YOLO + PyTorch can be heavy during image build.
- Open TCP ports 80 and 443 in the Oracle subnet security list. Also allow them in the VM firewall if UFW is enabled.

## First Deploy

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

Clone the repo, copy the environment file, and start the app:

```bash
cp .env.example .env
nano .env
```

For production, set `DATABASE_URL` to your Neon Postgres connection string:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
MEDIA_RETENTION_SECONDS=3600
MAX_UPLOAD_MB=8
```

Then start the app:

```bash
docker compose up -d --build
docker compose logs -f backend
```

The site is served by Nginx on port 80. The backend is only exposed inside Docker.

## Runtime Media

Uploaded and generated images are stored in the Docker named volume `mahjong_data`, under `/data/media`.

- Uploads: `/data/media/uploads`
- Generated result images: `/data/media/outputs`
- Cleanup TTL: `MEDIA_RETENTION_SECONDS` in `.env`
- Upload size limit: `MAX_UPLOAD_MB` in `.env`, mirrored by Nginx `client_max_body_size`

This keeps user images out of `backend/static` and out of the git working tree.

## TLS

Start with HTTP to verify the app. After your domain points to the VM, add TLS with either:

- Cloudflare proxy in front of the VM, or
- a certbot/acme companion for the Nginx container, or
- host-level Nginx/Caddy handling TLS and proxying to this compose stack.

Keep `/socket.io/` proxy headers when adding TLS because the game room uses WebSocket upgrades.
