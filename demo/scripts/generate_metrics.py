#!/usr/bin/env python3
"""
Generate fake metrics for Prometheus.
This script runs a simple HTTP server that exposes Prometheus metrics.
"""

import http.server
import socketserver
import time
import random
import threading
from prometheus_client import Counter, Gauge, Histogram, start_http_server, generate_latest

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

cpu_usage = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage',
    ['instance', 'cpu']
)

memory_usage = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes',
    ['instance']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

active_connections = Gauge(
    'active_connections',
    'Number of active connections',
    ['service']
)

def generate_metrics():
    """Continuously generate fake metrics."""
    instances = ['web-server-1', 'web-server-2', 'api-server-1', 'api-server-2', 'db-server-1']
    endpoints = ['/api/users', '/api/products', '/api/orders', '/health', '/metrics']
    methods = ['GET', 'POST', 'PUT', 'DELETE']
    status_codes = [200, 201, 400, 404, 500]
    services = ['web', 'api', 'database', 'cache']
    
    while True:
        # Simulate HTTP requests
        for _ in range(random.randint(5, 20)):
            method = random.choice(methods)
            endpoint = random.choice(endpoints)
            status = random.choice(status_codes)
            http_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
            request_duration.labels(method=method, endpoint=endpoint).observe(
                random.uniform(0.01, 3.0)
            )
        
        # Simulate CPU usage
        for instance in instances:
            for cpu in ['cpu0', 'cpu1', 'cpu2', 'cpu3']:
                cpu_usage.labels(instance=instance, cpu=cpu).set(
                    random.uniform(10, 90)
                )
        
        # Simulate memory usage
        for instance in instances:
            memory_usage.labels(instance=instance).set(
                random.randint(1000000000, 8000000000)  # 1GB to 8GB
            )
        
        # Simulate active connections
        for service in services:
            active_connections.labels(service=service).set(
                random.randint(10, 500)
            )
        
        time.sleep(5)

if __name__ == '__main__':
    # Start Prometheus metrics server
    start_http_server(8000)
    print("Started metrics server on port 8000")
    
    # Start generating metrics in background
    metrics_thread = threading.Thread(target=generate_metrics, daemon=True)
    metrics_thread.start()
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

