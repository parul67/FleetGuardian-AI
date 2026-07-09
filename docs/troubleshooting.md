# Troubleshooting

Common issues and their solutions for **FleetGuardian AI**.

---

## Docker Compose Issues

### ❌ Backend container exits immediately

**Symptom**: `docker compose ps` shows `backend` as `Exited`.

**Diagnosis**:
```bash
docker compose logs backend
```

**Common causes**:
- `DATABASE_URL` is incorrect → verify `.env` values match `postgres` service.
- Missing `.env` file → `cp .env.example .env` and fill in values.
- Port 8000 already in use → `netstat -aon | findstr :8000` (Windows).

---

### ❌ PostgreSQL connection refused

**Symptom**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Fix**: The backend starts before Postgres is ready. The `depends_on: condition: service_healthy` in `docker-compose.yml` should handle this, but if not:
```bash
docker compose restart backend
```

Also confirm the `POSTGRES_HOST` is set to `postgres` (the service name), not `localhost`.

---

### ❌ Nginx returns 502 Bad Gateway

**Symptom**: Frontend loads but API calls return 502.

**Diagnosis**:
```bash
docker compose logs frontend
# Check if backend is reachable from within the network
docker compose exec frontend wget -qO- http://backend:8000/health
```

**Fix**: Ensure the `backend` container is healthy before the `frontend` container starts:
```bash
docker compose restart frontend
```

---

### ❌ Grafana dashboard not provisioned

**Symptom**: Grafana loads but the FleetGuardian dashboard is missing.

**Fix**: Verify provisioning volumes are mounted correctly:
```bash
docker compose exec grafana ls /etc/grafana/provisioning/dashboards/
```
Expected: `dashboard.yml` and `fleetguardian_dashboard.json`.

If missing, ensure `grafana/provisioning/` directory exists in the project root and restart:
```bash
docker compose restart grafana
```

---

## Backend / Python Issues

### ❌ `ModuleNotFoundError` when running locally

**Fix**: Make sure `PYTHONPATH` is set:
```powershell
$env:PYTHONPATH = "."
python -m uvicorn app.main:app --reload
```

---

### ❌ OpenCV import fails (`libGL.so.1: cannot open shared object file`)

**Symptom**: Occurs in Docker or headless environments.

**Fix**: The `Dockerfile.backend` installs `libgl1-mesa-glx` and `libglib2.0-0`. Rebuild the image:
```bash
docker compose build --no-cache backend
```

---

### ❌ pytest fails with database errors

**Fix**: For local testing without Docker, use SQLite:
```bash
DATABASE_URL=sqlite:///./test.db pytest tests/ -v --basetemp=./tmp_pytest
```

---

## Frontend Issues

### ❌ `npm run build` fails with TypeScript errors

**Fix**:
```bash
cd frontend
npm ci          # Clean install
npm run build   # Check output
```

Verify TypeScript version compatibility – the project requires `typescript ~6.0.2`.

---

### ❌ API calls fail with CORS error in local dev

**Symptom**: Browser console shows `CORS policy: No 'Access-Control-Allow-Origin'`

**Fix**: Ensure the backend's `BACKEND_CORS_ORIGINS` includes your frontend URL:
```dotenv
BACKEND_CORS_ORIGINS=http://localhost,http://localhost:5173,http://localhost:3000
```

---

## GitHub Actions CI Issues

### ❌ `docker compose config` fails in CI

**Symptom**: CI job `docker-build` fails on the config validation step.

**Fix**: Ensure `.env.example` has values for all variables used in `docker-compose.yml`. The CI step uses the `${VAR:-default}` fallback syntax which doesn't require an actual `.env` file.

---

## Getting Help

1. Check container logs: `docker compose logs <service-name>`
2. Inspect running containers: `docker compose ps`
3. Open a shell in a container: `docker compose exec <service-name> sh`
4. Open an issue on [GitHub](https://github.com/YOUR_USERNAME/FleetGuardian-AI/issues)
