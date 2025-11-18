# Docker Compose Setup for Local Testing

This directory contains a Docker Compose setup for local testing with Prometheus, Loki, and Tempo datasources, all populated with fake demo data.

## Services

- **Prometheus** (port 9090): Metrics database
- **Loki** (port 3100): Log aggregation system
- **Tempo** (port 3200): Distributed tracing backend
- **Grafana** (port 3000): Visualization platform (optional)
- **fake-metrics**: Generates sample metrics for Prometheus
- **fake-logs**: Generates sample logs for Loki
- **fake-traces**: Generates sample traces for Tempo

## Quick Start

1. Start all services:
```bash
docker-compose up -d
```

2. Wait for services to be ready (about 30-60 seconds):
```bash
docker-compose ps
```

3. Access the services:
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100
- Tempo: http://localhost:3200

## Grafana Setup

Grafana is pre-configured with datasources:
- Prometheus (default)
- Loki
- Tempo

All datasources are automatically provisioned and ready to use.

## Stopping Services

```bash
docker-compose down
```

To also remove volumes (this will delete all data):
```bash
docker-compose down -v
```

## Data Generation

The fake data generators run continuously:
- **Metrics**: HTTP requests, CPU usage, memory usage, request duration, active connections
- **Logs**: Application logs from various services (web-server, api-server, database, cache, auth-service)
- **Traces**: Distributed traces with multiple spans showing service interactions

## Troubleshooting

If services fail to start:
1. Check logs: `docker-compose logs <service-name>`
2. Ensure ports are not already in use
3. Check Docker has enough resources allocated

To view logs from all services:
```bash
docker-compose logs -f
```

