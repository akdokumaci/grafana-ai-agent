#!/usr/bin/env python3
"""
Frontend Service - Initiates requests and calls backend API
Generates Prometheus metrics, OpenTelemetry traces, and logs to Loki
"""

import time
import random
import requests
import json
from datetime import datetime
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
import threading

app = Flask(__name__)

# Service configuration
SERVICE_NAME = "frontend-service"
BACKEND_URL = "http://backend:8002"
LOKI_URL = "http://loki:3100/loki/api/v1/push"

# Prometheus metrics
request_counter = Counter(
    'frontend_requests_total',
    'Total number of requests to frontend',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'frontend_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint']
)

active_users = Gauge(
    'frontend_active_users',
    'Number of active users'
)

error_counter = Counter(
    'frontend_errors_total',
    'Total number of errors',
    ['type']
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

def send_log_to_loki(level, message, extra_labels=None):
    """Send log entry to Loki."""
    timestamp_ns = int(time.time() * 1e9)
    
    labels = {
        "job": "frontend-service",
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

@app.route('/')
def home():
    """Home endpoint that calls backend."""
    start_time = time.time()
    
    with tracer.start_as_current_span("frontend_home_request") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.route", "/")
        
        try:
            send_log_to_loki("INFO", "Processing home page request")
            
            # Call backend service
            response = requests.get(f"{BACKEND_URL}/api/data", timeout=5)
            
            duration = time.time() - start_time
            request_duration.labels(endpoint="/").observe(duration)
            request_counter.labels(method="GET", endpoint="/", status=response.status_code).inc()
            
            send_log_to_loki(
                "INFO",
                f"Home request completed in {duration:.3f}s with status {response.status_code}"
            )
            
            return jsonify({
                "service": SERVICE_NAME,
                "backend_response": response.json(),
                "duration": duration
            }), 200
            
        except Exception as e:
            error_counter.labels(type="backend_error").inc()
            send_log_to_loki("ERROR", f"Error calling backend: {str(e)}")
            span.set_attribute("error", True)
            return jsonify({"error": str(e)}), 500

@app.route('/user/<user_id>')
def get_user(user_id):
    """Get user information by calling backend."""
    start_time = time.time()
    
    with tracer.start_as_current_span("frontend_get_user") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.route", "/user/<user_id>")
        span.set_attribute("user.id", user_id)
        
        try:
            send_log_to_loki("INFO", f"Fetching user {user_id}")
            
            # Call backend to get user data
            response = requests.get(f"{BACKEND_URL}/api/user/{user_id}", timeout=5)
            
            duration = time.time() - start_time
            request_duration.labels(endpoint="/user").observe(duration)
            request_counter.labels(method="GET", endpoint="/user", status=response.status_code).inc()
            
            send_log_to_loki(
                "INFO",
                f"User {user_id} fetch completed in {duration:.3f}s",
                {"user_id": user_id}
            )
            
            return jsonify({
                "service": SERVICE_NAME,
                "user_data": response.json(),
                "duration": duration
            }), 200
            
        except Exception as e:
            error_counter.labels(type="backend_error").inc()
            send_log_to_loki("ERROR", f"Error fetching user {user_id}: {str(e)}")
            return jsonify({"error": str(e)}), 500

@app.route('/product/<product_id>')
def get_product(product_id):
    """Get product information by calling backend."""
    start_time = time.time()
    
    with tracer.start_as_current_span("frontend_get_product") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.route", "/product/<product_id>")
        span.set_attribute("product.id", product_id)
        
        try:
            send_log_to_loki("INFO", f"Fetching product {product_id}")
            
            # Call backend
            response = requests.get(f"{BACKEND_URL}/api/product/{product_id}", timeout=5)
            
            duration = time.time() - start_time
            request_duration.labels(endpoint="/product").observe(duration)
            request_counter.labels(method="GET", endpoint="/product", status=response.status_code).inc()
            
            send_log_to_loki("INFO", f"Product {product_id} fetch completed in {duration:.3f}s")
            
            return jsonify({
                "service": SERVICE_NAME,
                "product_data": response.json(),
                "duration": duration
            }), 200
            
        except Exception as e:
            error_counter.labels(type="backend_error").inc()
            send_log_to_loki("ERROR", f"Error fetching product {product_id}: {str(e)}")
            return jsonify({"error": str(e)}), 500

def simulate_traffic():
    """Simulate user traffic in the background."""
    endpoints = [
        "/",
        f"/user/{random.randint(1, 100)}",
        f"/product/{random.randint(1, 50)}"
    ]
    
    time.sleep(10)  # Wait for services to start
    
    while True:
        try:
            # Simulate active users
            active_users.set(random.randint(10, 100))
            
            # Make random requests
            endpoint = random.choice(endpoints)
            url = f"http://localhost:8001{endpoint}"
            
            try:
                response = requests.get(url, timeout=5)
                print(f"Traffic simulation: {endpoint} -> {response.status_code}")
            except:
                pass
            
            time.sleep(random.uniform(1, 5))
            
        except Exception as e:
            print(f"Error in traffic simulation: {e}")
            time.sleep(5)

if __name__ == '__main__':
    send_log_to_loki("INFO", f"{SERVICE_NAME} starting up")
    
    # Start background traffic simulation
    traffic_thread = threading.Thread(target=simulate_traffic, daemon=True)
    traffic_thread.start()
    
    app.run(host='0.0.0.0', port=8001)

