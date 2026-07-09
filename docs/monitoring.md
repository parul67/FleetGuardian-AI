# Monitoring Guide

FleetGuardian AI ships with **Prometheus** and **Grafana** for production-grade observability.

---

## Architecture

```
FastAPI backend
  └── /metrics endpoint  (prometheus-fastapi-instrumentator)
        └── scraped by Prometheus (every 10s)
                  └── visualised in Grafana (pre-built dashboard)
```

---

## Access URLs

| Tool | URL | Credentials |
|---|---|---|
| Prometheus | http://localhost:9090 | None (open) |
| Grafana | http://localhost:3000 | admin / `GRAFANA_PASSWORD` from `.env` |

---

## Pre-built Dashboard

A **FleetGuardian AI – API & System Metrics** dashboard is automatically provisioned in Grafana (under the `FleetGuardian AI` folder) with:

| Panel | Metric |
|---|---|
| Total HTTP Requests | `http_requests_total` |
| Active WebSocket Connections | `websocket_connections_active` |
| Error Rate (5xx) | `rate(http_requests_total{status=~"5.."}[5m])` |
| Request Rate (req/s) | `rate(http_requests_total[1m])` |
| Latency P50 / P95 / P99 (ms) | histogram_quantile on `http_request_duration_seconds_bucket` |
| CPU Usage | `rate(process_cpu_seconds_total[1m])` |
| Memory RSS | `process_resident_memory_bytes` |

---

## Prometheus Targets

Navigate to **http://localhost:9090/targets** to see the scrape status.

Expected targets:
- `prometheus` (localhost:9090) – **UP**
- `fleetguardian-backend` (backend:8000) – **UP**

If `fleetguardian-backend` shows **DOWN**, verify the backend is running:
```bash
docker compose logs backend
curl http://localhost/health
```

---

## Adding Custom Metrics

You can add custom application metrics using the `prometheus-fastapi-instrumentator` or the `prometheus_client` library directly:

```python
from prometheus_client import Counter, Histogram

alert_counter = Counter(
    "fleetguardian_alerts_total",
    "Total number of safety alerts triggered",
    ["severity", "alert_type"]
)

# In your alert service:
alert_counter.labels(severity="HIGH", alert_type="drowsiness").inc()
```

---

## Grafana Alerts

To configure alerting rules in Grafana:

1. Navigate to **Alerting → Alert rules** in Grafana.
2. Create a new alert rule using the Prometheus data source.
3. Set notification channels (Email, Slack, PagerDuty) under **Contact points**.

Example alert: Notify when error rate > 1 req/s for 2 minutes.

---

## Retention

Prometheus is configured with a **15-day** retention policy by default.
To change it, update the `--storage.tsdb.retention.time` flag in `docker-compose.yml`.
