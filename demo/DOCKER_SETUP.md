# Docker Compose Setup for Local Testing

This directory contains a Docker Compose setup for local testing with Prometheus, Loki, and Tempo datasources, with three interconnected microservices generating realistic telemetry data.

## Services

### Observability Stack
- **Prometheus** (port 9090): Metrics database
- **Loki** (port 3100): Log aggregation system
- **Tempo** (port 3200): Distributed tracing backend
- **Grafana** (port 3000): Visualization platform

### Demo Applications
- **Frontend Service** (port 8001): User-facing service that initiates requests
- **Backend Service** (port 8002): API service with business logic and caching
- **Database Service** (port 8003): Simulates database operations

These three services communicate with each other (Frontend → Backend → Database) and generate comprehensive telemetry including Prometheus metrics, OpenTelemetry traces, and structured logs.

## Quick Start

1. Navigate to the demo directory:
```bash
cd demo
```

2. Start all services:
```bash
docker-compose up -d
```

3. Wait for services to be ready (about 30-60 seconds):
```bash
docker-compose ps
```

4. Access the services:
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100
- Tempo: http://localhost:3200
- Frontend App: http://localhost:8001
- Backend API: http://localhost:8002
- Database Service: http://localhost:8003

## Grafana Setup

Grafana is pre-configured with datasources:
- Prometheus (default)
- Loki
- Tempo

All datasources are automatically provisioned and ready to use.

## Stopping Services

From the `demo` directory:
```bash
docker-compose down
```

To also remove volumes (this will delete all data):
```bash
docker-compose down -v
```

## Telemetry Data Generation

The three microservices generate realistic telemetry data:

### Metrics (Prometheus)
Each service exposes `/metrics` endpoint with:
- **Frontend**: Request counters, duration histograms, active users, error rates
- **Backend**: API metrics, cache hit/miss rates, database call metrics, processing time
- **Database**: Query execution metrics, connection pool stats, slow query detection, table sizes

### Logs (Loki)
All services send structured logs to Loki with:
- Multiple log levels (INFO, DEBUG, WARN, ERROR)
- Service-specific labels
- Request correlation information
- Business context (user IDs, product IDs, etc.)

### Traces (Tempo)
OpenTelemetry traces showing the complete request flow:
- Distributed traces across all three services
- Parent-child span relationships
- Trace propagation through HTTP calls
- Custom attributes for debugging

### Automatic Traffic Generation
The frontend service automatically generates simulated user traffic, creating realistic request patterns across all services.

## Testing the Services

You can manually trigger requests:

```bash
# Trigger a request through all services
curl http://localhost:8001/

# Fetch user information
curl http://localhost:8001/user/123

# Fetch product information
curl http://localhost:8001/product/42

# Check service health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health

# View metrics
curl http://localhost:8001/metrics
```

## Exploring in Grafana

1. **Metrics**: Go to Explore → Prometheus
   ```
   rate(frontend_requests_total[5m])
   histogram_quantile(0.95, rate(backend_request_duration_seconds_bucket[5m]))
   backend_cache_operations_total
   ```

2. **Logs**: Go to Explore → Loki
   ```
   {service="frontend-service"}
   {service="backend-service", level="ERROR"}
   {service="database-service"} |= "slow query"
   ```

3. **Traces**: Go to Explore → Tempo
   - Search for traces or click on trace IDs from logs

## Troubleshooting

If services fail to start:
1. Check logs: `docker-compose logs <service-name>` (from the `demo` directory)
2. Ensure ports are not already in use
3. Check Docker has enough resources allocated

To view logs from all services (from the `demo` directory):
```bash
docker-compose logs -f
```

