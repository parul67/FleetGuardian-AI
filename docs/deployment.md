# Deployment Guide

This guide covers production deployment of **FleetGuardian AI** using Docker Compose.

---

## Prerequisites

- Docker Desktop ≥ 24 with Compose v2 (`docker compose` not `docker-compose`)
- A Linux/macOS host (or WSL2 on Windows)
- Minimum: **2 CPU cores, 4 GB RAM** (8 GB recommended for full monitoring stack)

---

## 1. Environment Configuration

```bash
cp .env.example .env
```

Open `.env` and update every `CHANGE_ME_*` value:

```dotenv
POSTGRES_PASSWORD=<strong-random-password>
SECRET_KEY=<output-of: python -c "import secrets; print(secrets.token_hex(32))">
GRAFANA_PASSWORD=<secure-grafana-password>
```

> **⚠️ Never commit `.env` to version control.**

---

## 2. Build & Start

```bash
# Build all images and start in detached mode
docker compose up -d --build

# Watch startup logs
docker compose logs -f

# Check container health
docker compose ps
```

Expected output – all containers should show `healthy` or `running`:

```
NAME                        STATUS          PORTS
fleetguardian-postgres      healthy         5432/tcp
fleetguardian-backend       healthy         8000/tcp
fleetguardian-frontend      running         0.0.0.0:80->80/tcp
fleetguardian-prometheus    running         0.0.0.0:9090->9090/tcp
fleetguardian-grafana       running         0.0.0.0:3000->3000/tcp
```

---

## 3. Verify Services

| URL | Expected |
|---|---|
| http://localhost | FleetGuardian Dashboard |
| http://localhost/api/v1 | API root |
| http://localhost/api/docs | FastAPI Swagger UI |
| http://localhost/health | `{"status": "healthy"}` |
| http://localhost:9090 | Prometheus |
| http://localhost:3000 | Grafana (admin / your password) |

---

## 4. Connecting to an External PostgreSQL (AWS RDS, etc.)

Update `.env` to point to your managed database:

```dotenv
POSTGRES_HOST=your-rds-endpoint.us-east-1.rds.amazonaws.com
POSTGRES_PORT=5432
POSTGRES_USER=fleetadmin
POSTGRES_PASSWORD=<your-rds-password>
POSTGRES_DB=fleetguardian
DATABASE_URL=postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
```

Then remove or comment out the `postgres` service in `docker-compose.yml` and remove the `depends_on` reference in `backend`.

---

## 5. Useful Commands

```bash
# Stop all services
docker compose down

# Stop and remove volumes (⚠️ deletes database data)
docker compose down -v

# Restart a single service
docker compose restart backend

# View logs for a specific service
docker compose logs -f backend

# Open a shell in the backend container
docker compose exec backend bash

# Run database migrations (if using Alembic)
docker compose exec backend alembic upgrade head
```

---

## 6. Scaling the Backend

For higher throughput, scale backend replicas (requires a load balancer update in Nginx):

```bash
docker compose up -d --scale backend=3
```

---

## 7. Adding HTTPS (Let's Encrypt)

To add TLS with Certbot:

1. Install `certbot` on your host and obtain a certificate.
2. Update `nginx/default.conf` to listen on port 443 and reference the certificate paths.
3. Add a volume mount in `docker-compose.yml` for the `/etc/letsencrypt` directory.

See `nginx/default.conf` for the modular comment sections indicating where to add SSL configuration.
