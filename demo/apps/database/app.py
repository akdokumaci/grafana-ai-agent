#!/usr/bin/env python3
"""
Database Service - Simulates database operations
Generates Prometheus metrics, OpenTelemetry traces, and logs to Loki
"""

import time
import random
import requests
import json
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor

app = Flask(__name__)

# Service configuration
SERVICE_NAME = "database-service"
LOKI_URL = "http://loki:3100/loki/api/v1/push"

# Prometheus metrics
query_counter = Counter(
    'database_queries_total',
    'Total number of database queries',
    ['operation', 'table', 'status']
)

query_duration = Histogram(
    'database_query_duration_seconds',
    'Query execution duration in seconds',
    ['operation', 'table']
)

connection_pool = Gauge(
    'database_connection_pool_active',
    'Number of active database connections'
)

slow_queries = Counter(
    'database_slow_queries_total',
    'Number of slow queries detected',
    ['table']
)

table_size = Gauge(
    'database_table_size_bytes',
    'Estimated table size in bytes',
    ['table']
)

transaction_counter = Counter(
    'database_transactions_total',
    'Total number of transactions',
    ['status']
)

# OpenTelemetry setup
resource = Resource.create({
    "service.name": SERVICE_NAME,
    "service.version": "1.0.0",
    "deployment.environment": "demo"
})

otlp_exporter = OTLPSpanExporter(
    endpoint="http://tempo:4317",
    insecure=True
)

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument Flask
FlaskInstrumentor().instrument_app(app)

# Simulated database tables
tables = {
    'users': {},
    'products': {},
    'orders': {}
}

def send_log_to_loki(level, message, extra_labels=None):
    """Send log entry to Loki."""
    timestamp_ns = int(time.time() * 1e9)
    
    labels = {
        "job": "database-service",
        "service": SERVICE_NAME,
        "level": level,
        "environment": "demo"
    }
    
    if extra_labels:
        labels.update(extra_labels)
    
    log_entry = {
        "streams": [{
            "stream": labels,
            "values": [[str(timestamp_ns), message]]
        }]
    }
    
    try:
        requests.post(
            LOKI_URL,
            json=log_entry,
            headers={"Content-Type": "application/json"},
            timeout=2
        )
    except Exception as e:
        print(f"Error sending logs to Loki: {e}")

def simulate_query_execution(table_name, operation):
    """Simulate query execution with realistic delays."""
    # Simulate query planning
    with tracer.start_as_current_span("query_planning") as planning_span:
        time.sleep(random.uniform(0.001, 0.005))
        send_log_to_loki("DEBUG", f"Query plan generated for {table_name}")
    
    # Simulate query execution
    with tracer.start_as_current_span("query_execution") as execution_span:
        execution_time = random.uniform(0.01, 0.2)
        time.sleep(execution_time)
        
        # Track slow queries
        if execution_time > 0.15:
            slow_queries.labels(table=table_name).inc()
            send_log_to_loki("WARN", f"Slow query detected on {table_name}: {execution_time:.3f}s")
        
        execution_span.set_attribute("query.execution_time", execution_time)
        execution_span.set_attribute("table.name", table_name)

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": SERVICE_NAME}), 200

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    from flask import Response
    
    # Update connection pool gauge
    connection_pool.set(random.randint(5, 25))
    
    # Update table sizes
    for table_name in tables.keys():
        table_size.labels(table=table_name).set(random.randint(1000000, 100000000))
    
    return Response(generate_latest(), mimetype='text/plain')

@app.route('/db/query')
def execute_query():
    """Execute a general database query."""
    start_time = time.time()
    
    with tracer.start_as_current_span("database_query") as span:
        span.set_attribute("db.operation", "SELECT")
        span.set_attribute("db.system", "postgresql")
        
        try:
            send_log_to_loki("INFO", "Executing general query")
            
            # Start a transaction
            with tracer.start_as_current_span("transaction_begin"):
                send_log_to_loki("DEBUG", "Transaction started")
                transaction_counter.labels(status="begin").inc()
            
            # Simulate query execution
            simulate_query_execution("general", "SELECT")
            
            # Prepare result
            result = {
                "database": SERVICE_NAME,
                "timestamp": time.time(),
                "rows": random.randint(1, 100),
                "data": {
                    "id": random.randint(1, 1000),
                    "value": f"data_{random.randint(1, 100)}"
                }
            }
            
            # Commit transaction
            with tracer.start_as_current_span("transaction_commit"):
                send_log_to_loki("DEBUG", "Transaction committed")
                transaction_counter.labels(status="commit").inc()
            
            duration = time.time() - start_time
            query_duration.labels(operation="SELECT", table="general").observe(duration)
            query_counter.labels(operation="SELECT", table="general", status="success").inc()
            
            send_log_to_loki("INFO", f"Query completed in {duration:.3f}s")
            
            return jsonify(result), 200
            
        except Exception as e:
            transaction_counter.labels(status="rollback").inc()
            query_counter.labels(operation="SELECT", table="general", status="error").inc()
            send_log_to_loki("ERROR", f"Query failed: {str(e)}")
            span.set_attribute("error", True)
            return jsonify({"error": str(e)}), 500

@app.route('/db/user/<user_id>')
def get_user(user_id):
    """Get user from database."""
    start_time = time.time()
    
    with tracer.start_as_current_span("database_get_user") as span:
        span.set_attribute("db.operation", "SELECT")
        span.set_attribute("db.table", "users")
        span.set_attribute("user.id", user_id)
        
        try:
            send_log_to_loki("INFO", f"Querying user {user_id} from database")
            
            # Start transaction
            with tracer.start_as_current_span("transaction_begin"):
                transaction_counter.labels(status="begin").inc()
            
            # Check if user exists in cache
            if user_id in tables['users']:
                send_log_to_loki("DEBUG", f"User {user_id} found in table cache")
            else:
                # Simulate user lookup
                simulate_query_execution("users", "SELECT")
                
                # Create user data
                tables['users'][user_id] = {
                    "id": user_id,
                    "name": f"User {user_id}",
                    "email": f"user{user_id}@example.com",
                    "created_at": time.time()
                }
            
            user_data = tables['users'][user_id]
            
            # Commit transaction
            with tracer.start_as_current_span("transaction_commit"):
                transaction_counter.labels(status="commit").inc()
            
            duration = time.time() - start_time
            query_duration.labels(operation="SELECT", table="users").observe(duration)
            query_counter.labels(operation="SELECT", table="users", status="success").inc()
            
            send_log_to_loki("INFO", f"User {user_id} query completed in {duration:.3f}s")
            
            return jsonify({
                "database": SERVICE_NAME,
                "user": user_data
            }), 200
            
        except Exception as e:
            transaction_counter.labels(status="rollback").inc()
            query_counter.labels(operation="SELECT", table="users", status="error").inc()
            send_log_to_loki("ERROR", f"Error querying user {user_id}: {str(e)}")
            span.set_attribute("error", True)
            return jsonify({"error": str(e)}), 500

@app.route('/db/product/<product_id>')
def get_product(product_id):
    """Get product from database."""
    start_time = time.time()
    
    with tracer.start_as_current_span("database_get_product") as span:
        span.set_attribute("db.operation", "SELECT")
        span.set_attribute("db.table", "products")
        span.set_attribute("product.id", product_id)
        
        try:
            send_log_to_loki("INFO", f"Querying product {product_id} from database")
            
            # Start transaction
            with tracer.start_as_current_span("transaction_begin"):
                transaction_counter.labels(status="begin").inc()
            
            # Check if product exists in cache
            if product_id in tables['products']:
                send_log_to_loki("DEBUG", f"Product {product_id} found in table cache")
            else:
                # Simulate product lookup with possible JOIN
                simulate_query_execution("products", "SELECT")
                
                # Simulate JOIN with inventory table
                with tracer.start_as_current_span("join_inventory"):
                    time.sleep(random.uniform(0.005, 0.02))
                    send_log_to_loki("DEBUG", f"Joined product {product_id} with inventory data")
                
                # Create product data
                tables['products'][product_id] = {
                    "id": product_id,
                    "name": f"Product {product_id}",
                    "description": f"Description for product {product_id}",
                    "stock": random.randint(0, 1000),
                    "created_at": time.time()
                }
            
            product_data = tables['products'][product_id]
            
            # Commit transaction
            with tracer.start_as_current_span("transaction_commit"):
                transaction_counter.labels(status="commit").inc()
            
            duration = time.time() - start_time
            query_duration.labels(operation="SELECT", table="products").observe(duration)
            query_counter.labels(operation="SELECT", table="products", status="success").inc()
            
            send_log_to_loki("INFO", f"Product {product_id} query completed in {duration:.3f}s")
            
            return jsonify({
                "database": SERVICE_NAME,
                "product": product_data
            }), 200
            
        except Exception as e:
            transaction_counter.labels(status="rollback").inc()
            query_counter.labels(operation="SELECT", table="products", status="error").inc()
            send_log_to_loki("ERROR", f"Error querying product {product_id}: {str(e)}")
            span.set_attribute("error", True)
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    send_log_to_loki("INFO", f"{SERVICE_NAME} starting up")
    app.run(host='0.0.0.0', port=8003)

