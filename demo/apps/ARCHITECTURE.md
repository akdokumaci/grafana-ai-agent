# Architecture Overview

## Service Communication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         User / Simulated Traffic                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP Requests
                             ▼
                   ┌──────────────────┐
                   │  Frontend Service │  Port 8001
                   │   (Flask App)     │
                   └────────┬─────────┘
                            │
                            │ HTTP: /api/data
                            │        /api/user/:id
                            │        /api/product/:id
                            ▼
                   ┌──────────────────┐
                   │  Backend Service  │  Port 8002
                   │   (Flask App)     │
                   │  + Cache Layer    │
                   └────────┬─────────┘
                            │
                            │ HTTP: /db/query
                            │        /db/user/:id
                            │        /db/product/:id
                            ▼
                   ┌──────────────────┐
                   │ Database Service  │  Port 8003
                   │   (Flask App)     │
                   │  + Simulated DB   │
                   └──────────────────┘
```

## Telemetry Flow

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Frontend        │      │  Backend         │      │  Database        │
│  Service         │      │  Service         │      │  Service         │
└────────┬─────────┘      └────────┬─────────┘      └────────┬─────────┘
         │                         │                          │
         │ Prometheus Metrics      │ Prometheus Metrics       │ Prometheus Metrics
         ├────────────────────────►├─────────────────────────►├──────────────┐
         │                         │                          │              │
         │ OpenTelemetry Traces    │ OpenTelemetry Traces     │ OpenTelemetry│
         ├────────────────────────►├─────────────────────────►├──────────────┤
         │                         │                          │              │
         │ Loki Logs               │ Loki Logs                │ Loki Logs    │
         ├────────────────────────►├─────────────────────────►├──────────────┤
         │                         │                          │              │
         ▼                         ▼                          ▼              ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │                    Observability Stack                                  │
    ├────────────────────┬──────────────────────┬────────────────────────────┤
    │   Prometheus       │      Loki            │         Tempo              │
    │   (Metrics)        │      (Logs)          │       (Traces)             │
    │   Port 9090        │      Port 3100       │       Port 3200            │
    └────────────────────┴──────────────────────┴────────────────────────────┘
                                       │
                                       │ Queries & Visualization
                                       ▼
                            ┌──────────────────┐
                            │     Grafana      │
                            │    Port 3000     │
                            └──────────────────┘
```

## Telemetry Details

### Frontend Service
**Metrics:**
- `frontend_requests_total` - Counter with labels: method, endpoint, status
- `frontend_request_duration_seconds` - Histogram with labels: endpoint
- `frontend_active_users` - Gauge
- `frontend_errors_total` - Counter with labels: type

**Traces:**
- `frontend_home_request` - Root span for home page
- `frontend_get_user` - Root span for user requests
- `frontend_get_product` - Root span for product requests

**Logs:**
- Request processing logs
- Backend call logs
- Error logs with full context

### Backend Service
**Metrics:**
- `backend_requests_total` - Counter with labels: method, endpoint, status
- `backend_request_duration_seconds` - Histogram with labels: endpoint
- `backend_database_calls_total` - Counter with labels: operation, status
- `backend_cache_operations_total` - Counter with labels: operation (hit/miss)
- `backend_processing_time_seconds` - Histogram with labels: operation

**Traces:**
- `backend_get_data` - Root span for data requests
- `backend_get_user` - Root span for user lookup
- `backend_get_product` - Root span for product lookup
- `validate_user_id` - Child span for validation
- `apply_pricing_rules` - Child span for business logic

**Logs:**
- Cache hit/miss logs
- Database query logs
- Business logic logs
- Error logs

### Database Service
**Metrics:**
- `database_queries_total` - Counter with labels: operation, table, status
- `database_query_duration_seconds` - Histogram with labels: operation, table
- `database_connection_pool_active` - Gauge
- `database_slow_queries_total` - Counter with labels: table
- `database_table_size_bytes` - Gauge with labels: table
- `database_transactions_total` - Counter with labels: status

**Traces:**
- `database_query` - Root span for queries
- `database_get_user` - Root span for user lookup
- `database_get_product` - Root span for product lookup
- `query_planning` - Child span for query planning
- `query_execution` - Child span for query execution
- `transaction_begin` - Child span for transaction start
- `transaction_commit` - Child span for transaction commit
- `join_inventory` - Child span for JOIN operations

**Logs:**
- Query execution logs
- Transaction logs
- Slow query warnings
- Error logs

## Request Flow Example

When a user accesses `http://localhost:8001/user/123`:

1. **Frontend Service** receives the request
   - Creates a trace with span `frontend_get_user`
   - Logs: "Fetching user 123"
   - Increments `frontend_requests_total` metric
   - Calls Backend: `GET http://backend:8002/api/user/123`

2. **Backend Service** receives the API call
   - Continues the trace with span `backend_get_user`
   - Logs: "Processing user request for ID: 123"
   - Checks cache (miss)
   - Increments `backend_cache_operations_total{operation="miss"}`
   - Creates child span `validate_user_id` for validation
   - Calls Database: `GET http://database:8003/db/user/123`

3. **Database Service** receives the query
   - Continues the trace with span `database_get_user`
   - Logs: "Querying user 123 from database"
   - Creates child spans:
     - `transaction_begin`
     - `query_planning`
     - `query_execution`
     - `transaction_commit`
   - Increments `database_queries_total{operation="SELECT", table="users"}`
   - Records query duration in histogram
   - Returns user data

4. **Backend Service** receives data
   - Caches the result
   - Logs: "User 123 request completed"
   - Returns to Frontend

5. **Frontend Service** receives data
   - Logs: "User 123 fetch completed"
   - Increments `frontend_request_duration_seconds`
   - Returns to user

The entire flow is captured in a single distributed trace with parent-child relationships, allowing you to see the complete request path and timing breakdown in Grafana.

## Key Features

1. **Distributed Tracing**: Complete request path visualization across all services
2. **Metric Correlation**: All metrics tagged with service names for easy correlation
3. **Structured Logging**: Consistent log format with service labels
4. **Cache Layer**: Demonstrates cache hit/miss patterns in metrics and logs
5. **Business Logic**: Shows nested spans for business operations
6. **Error Handling**: Proper error propagation through traces and logs
7. **Auto-Generated Traffic**: Frontend creates realistic traffic patterns
8. **Health Checks**: All services expose health endpoints

