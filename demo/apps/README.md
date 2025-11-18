# Grafana Demo Applications

This directory contains three interconnected microservices that demonstrate observability best practices by generating comprehensive telemetry data.

## Architecture

The system consists of three services that communicate with each other:

```
Frontend (8001) → Backend (8002) → Database (8003)
```

### Services

1. **Frontend Service** (`frontend/app.py`)
   - Port: 8001
   - Entry point for all requests
   - Calls the backend API service
   - Generates simulated user traffic

2. **Backend Service** (`backend/app.py`)
   - Port: 8002
   - Processes business logic
   - Implements caching layer
   - Calls the database service

3. **Database Service** (`database/app.py`)
   - Port: 8003
   - Simulates database operations
   - Implements query execution, transactions, and JOINs

## Telemetry Data Generated

Each service generates the following telemetry:

### Prometheus Metrics
- **Frontend**: Request counters, duration histograms, active users, error counters
- **Backend**: Request counters, duration histograms, database call counters, cache operations
- **Database**: Query counters, duration histograms, connection pool status, slow query detection, table sizes

All services expose metrics at `/metrics` endpoint.

### OpenTelemetry Traces
- Distributed traces across all three services
- Parent-child span relationships
- Trace propagation through HTTP calls
- Custom span attributes for business context
- Nested spans for sub-operations

Traces are exported to Tempo via OTLP gRPC (port 4317).

### Logs
- Structured logs sent to Loki
- Multiple log levels (INFO, DEBUG, WARN, ERROR)
- Service-specific labels
- Request correlation with traces

## Endpoints

### Frontend Service (http://localhost:8001)
- `GET /` - Home endpoint that triggers a call chain
- `GET /user/<user_id>` - Fetch user information
- `GET /product/<product_id>` - Fetch product information
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

### Backend Service (http://localhost:8002)
- `GET /api/data` - General data endpoint
- `GET /api/user/<user_id>` - User lookup with caching
- `GET /api/product/<product_id>` - Product lookup with caching
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

### Database Service (http://localhost:8003)
- `GET /db/query` - Execute general query
- `GET /db/user/<user_id>` - User database lookup
- `GET /db/product/<product_id>` - Product database lookup
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

## Running the Services

### Using Docker Compose

From the demo directory:

```bash
cd demo
docker-compose up -d
```

This will start:
- Prometheus (port 9090)
- Loki (port 3100)
- Tempo (port 3200)
- Grafana (port 3000)
- Frontend Service (port 8001)
- Backend Service (port 8002)
- Database Service (port 8003)

### Accessing the Services

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Frontend App**: http://localhost:8001

The frontend service automatically generates simulated traffic.

## Exploring the Telemetry

### In Grafana

1. **Metrics**: 
   - Go to Explore → Select "Prometheus"
   - Try queries like:
     - `rate(frontend_requests_total[5m])`
     - `histogram_quantile(0.95, rate(backend_request_duration_seconds_bucket[5m]))`
     - `database_connection_pool_active`

2. **Logs**:
   - Go to Explore → Select "Loki"
   - Try queries like:
     - `{service="frontend-service"}`
     - `{service="backend-service", level="ERROR"}`
     - `{service="database-service"} |= "slow query"`

3. **Traces**:
   - Go to Explore → Select "Tempo"
   - Search for traces or use trace ID from logs
   - View the complete request flow across all services

### Using curl

```bash
# Trigger a request that flows through all services
curl http://localhost:8001/

# Fetch a specific user
curl http://localhost:8001/user/123

# Fetch a specific product
curl http://localhost:8001/product/42

# Check metrics
curl http://localhost:8001/metrics
curl http://localhost:8002/metrics
curl http://localhost:8003/metrics
```

## Key Features

1. **Distributed Tracing**: Each request generates a trace that spans all three services
2. **Metric Correlation**: Metrics from all services are correlated in Prometheus
3. **Log Aggregation**: All logs are centralized in Loki with consistent labeling
4. **Caching Layer**: Backend implements caching with cache hit/miss metrics
5. **Error Simulation**: Services randomly generate errors for realistic testing
6. **Slow Query Detection**: Database service detects and logs slow queries
7. **Auto-Generated Traffic**: Frontend service generates simulated user traffic

## Stopping the Services

```bash
docker-compose down
```

To also remove volumes:

```bash
docker-compose down -v
```

