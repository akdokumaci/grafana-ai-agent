#!/usr/bin/env python3
"""
Backend API Service - Processes business logic and calls database
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
from opentelemetry.instrumentation.requests import RequestsInstrumentor

app = Flask(__name__)

# Service configuration
SERVICE_NAME = "backend-service"
DATABASE_URL = "http://database:8003"
LOKI_URL = "http://loki:3100/loki/api/v1/push"

# Prometheus metrics
request_counter = Counter(
    'backend_requests_total',
    'Total number of requests to backend',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'backend_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint']
)

database_calls = Counter(
    'backend_database_calls_total',
    'Total number of database calls',
    ['operation', 'status']
)

cache_hits = Counter(
    'backend_cache_operations_total',
    'Cache operations',
    ['operation']
)

processing_time = Histogram(
    'backend_processing_time_seconds',
    'Business logic processing time',
    ['operation']
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

# Instrument Flask and Requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Simple in-memory cache
cache = {}

def send_log_to_loki(level, message, extra_labels=None):
    """Send log entry to Loki."""
    timestamp_ns = int(time.time() * 1e9)
    
    labels = {
        "job": "backend-service",
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

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": SERVICE_NAME}), 200

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    from flask import Response
    return Response(generate_latest(), mimetype='text/plain')

@app.route('/api/data')
def get_data():
    """Get general data endpoint."""
    start_time = time.time()
    
    with tracer.start_as_current_span("backend_get_data") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.route", "/api/data")
        
        try:
            send_log_to_loki("INFO", "Processing data request")
            
            # Check cache first
            cache_key = "general_data"
            if cache_key in cache:
                cache_hits.labels(operation="hit").inc()
                send_log_to_loki("INFO", "Cache hit for general data")
                span.set_attribute("cache.hit", True)
                
                duration = time.time() - start_time
                request_duration.labels(endpoint="/api/data").observe(duration)
                request_counter.labels(method="GET", endpoint="/api/data", status=200).inc()
                
                return jsonify({
                    "service": SERVICE_NAME,
                    "data": cache[cache_key],
                    "from_cache": True
                }), 200
            
            cache_hits.labels(operation="miss").inc()
            span.set_attribute("cache.hit", False)
            
            # Call database
            send_log_to_loki("INFO", "Calling database for general data")
            response = requests.get(f"{DATABASE_URL}/db/query", timeout=5)
            database_calls.labels(operation="read", status=response.status_code).inc()
            
            if response.status_code == 200:
                data = response.json()
                cache[cache_key] = data
                
                duration = time.time() - start_time
                request_duration.labels(endpoint="/api/data").observe(duration)
                request_counter.labels(method="GET", endpoint="/api/data", status=200).inc()
                
                send_log_to_loki("INFO", f"Data request completed in {duration:.3f}s")
                
                return jsonify({
                    "service": SERVICE_NAME,
                    "data": data,
                    "from_cache": False
                }), 200
            else:
                raise Exception(f"Database returned status {response.status_code}")
                
        except Exception as e:
            send_log_to_loki("ERROR", f"Error processing data request: {str(e)}")
            span.set_attribute("error", True)
            request_counter.labels(method="GET", endpoint="/api/data", status=500).inc()
            return jsonify({"error": str(e)}), 500

@app.route('/api/user/<user_id>')
def get_user(user_id):
    """Get user by ID."""
    start_time = time.time()
    
    with tracer.start_as_current_span("backend_get_user") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.route", "/api/user/<user_id>")
        span.set_attribute("user.id", user_id)
        
        try:
            send_log_to_loki("INFO", f"Processing user request for ID: {user_id}")
            
            # Check cache
            cache_key = f"user_{user_id}"
            if cache_key in cache:
                cache_hits.labels(operation="hit").inc()
                send_log_to_loki("INFO", f"Cache hit for user {user_id}")
                
                duration = time.time() - start_time
                request_duration.labels(endpoint="/api/user").observe(duration)
                request_counter.labels(method="GET", endpoint="/api/user", status=200).inc()
                
                return jsonify({
                    "service": SERVICE_NAME,
                    "user": cache[cache_key],
                    "from_cache": True
                }), 200
            
            cache_hits.labels(operation="miss").inc()
            
            # Validate user ID (business logic)
            with tracer.start_as_current_span("validate_user_id") as validation_span:
                processing_start = time.time()
                time.sleep(random.uniform(0.01, 0.05))  # Simulate validation
                processing_time.labels(operation="validation").observe(time.time() - processing_start)
                send_log_to_loki("DEBUG", f"Validated user ID: {user_id}")
            
            # Call database
            send_log_to_loki("INFO", f"Querying database for user {user_id}")
            response = requests.get(f"{DATABASE_URL}/db/user/{user_id}", timeout=5)
            database_calls.labels(operation="read", status=response.status_code).inc()
            
            if response.status_code == 200:
                user_data = response.json()
                cache[cache_key] = user_data
                
                duration = time.time() - start_time
                request_duration.labels(endpoint="/api/user").observe(duration)
                request_counter.labels(method="GET", endpoint="/api/user", status=200).inc()
                
                send_log_to_loki("INFO", f"User {user_id} request completed in {duration:.3f}s")
                
                return jsonify({
                    "service": SERVICE_NAME,
                    "user": user_data,
                    "from_cache": False
                }), 200
            else:
                raise Exception(f"Database returned status {response.status_code}")
                
        except Exception as e:
            send_log_to_loki("ERROR", f"Error processing user {user_id}: {str(e)}")
            span.set_attribute("error", True)
            request_counter.labels(method="GET", endpoint="/api/user", status=500).inc()
            return jsonify({"error": str(e)}), 500

@app.route('/api/product/<product_id>')
def get_product(product_id):
    """Get product by ID."""
    start_time = time.time()
    
    with tracer.start_as_current_span("backend_get_product") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.route", "/api/product/<product_id>")
        span.set_attribute("product.id", product_id)
        
        try:
            send_log_to_loki("INFO", f"Processing product request for ID: {product_id}")
            
            # Check cache
            cache_key = f"product_{product_id}"
            if cache_key in cache:
                cache_hits.labels(operation="hit").inc()
                send_log_to_loki("INFO", f"Cache hit for product {product_id}")
                
                duration = time.time() - start_time
                request_duration.labels(endpoint="/api/product").observe(duration)
                request_counter.labels(method="GET", endpoint="/api/product", status=200).inc()
                
                return jsonify({
                    "service": SERVICE_NAME,
                    "product": cache[cache_key],
                    "from_cache": True
                }), 200
            
            cache_hits.labels(operation="miss").inc()
            
            # Apply business logic
            with tracer.start_as_current_span("apply_pricing_rules") as pricing_span:
                processing_start = time.time()
                time.sleep(random.uniform(0.02, 0.08))  # Simulate pricing calculation
                processing_time.labels(operation="pricing").observe(time.time() - processing_start)
                send_log_to_loki("DEBUG", f"Applied pricing rules for product {product_id}")
            
            # Call database
            send_log_to_loki("INFO", f"Querying database for product {product_id}")
            response = requests.get(f"{DATABASE_URL}/db/product/{product_id}", timeout=5)
            database_calls.labels(operation="read", status=response.status_code).inc()
            
            if response.status_code == 200:
                product_data = response.json()
                
                # Add calculated price (business logic)
                product_data['calculated_price'] = random.uniform(10.0, 500.0)
                cache[cache_key] = product_data
                
                duration = time.time() - start_time
                request_duration.labels(endpoint="/api/product").observe(duration)
                request_counter.labels(method="GET", endpoint="/api/product", status=200).inc()
                
                send_log_to_loki("INFO", f"Product {product_id} request completed in {duration:.3f}s")
                
                return jsonify({
                    "service": SERVICE_NAME,
                    "product": product_data,
                    "from_cache": False
                }), 200
            else:
                raise Exception(f"Database returned status {response.status_code}")
                
        except Exception as e:
            send_log_to_loki("ERROR", f"Error processing product {product_id}: {str(e)}")
            span.set_attribute("error", True)
            request_counter.labels(method="GET", endpoint="/api/product", status=500).inc()
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    send_log_to_loki("INFO", f"{SERVICE_NAME} starting up")
    app.run(host='0.0.0.0', port=8002)

