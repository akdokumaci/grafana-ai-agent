#!/usr/bin/env python3
"""
Generate fake logs and send them to Loki.
"""

import time
import random
import requests
import json
from datetime import datetime

LOKI_URL = "http://loki:3100/loki/api/v1/push"

def generate_log_entry(service, level, message):
    """Generate a log entry."""
    timestamp_ns = int(time.time() * 1e9)
    
    log_entry = {
        "streams": [{
            "stream": {
                "job": "fake-logs",
                "service": service,
                "level": level,
                "environment": "demo"
            },
            "values": [[str(timestamp_ns), message]]
        }]
    }
    
    return log_entry

def send_logs_to_loki(log_entry):
    """Send log entry to Loki."""
    try:
        response = requests.post(
            LOKI_URL,
            json=log_entry,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending logs to Loki: {e}")

def generate_logs():
    """Continuously generate fake logs."""
    services = ['web-server', 'api-server', 'database', 'cache', 'auth-service']
    log_levels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
    
    log_templates = {
        'web-server': [
            'Processing request: {method} {path}',
            'Request completed in {duration}ms',
            'User {user_id} logged in',
            'Cache miss for key: {key}',
            'Response status: {status}'
        ],
        'api-server': [
            'API call: {endpoint}',
            'Rate limit check: {user_id} - {allowed}',
            'Database query executed: {query}',
            'Authentication successful for user: {user_id}',
            'Validation error: {error}'
        ],
        'database': [
            'Query executed: SELECT * FROM {table}',
            'Connection pool: {active}/{max} connections',
            'Slow query detected: {query} took {duration}ms',
            'Transaction committed: {tx_id}',
            'Index scan on {table}.{index}'
        ],
        'cache': [
            'Cache hit: {key}',
            'Cache miss: {key}',
            'Cache eviction: {key}',
            'Cache size: {size}MB',
            'TTL expired for key: {key}'
        ],
        'auth-service': [
            'User authentication: {user_id} - {result}',
            'Token generated: {token_id}',
            'Token validation: {token_id} - {valid}',
            'Password reset requested: {user_id}',
            'Session expired: {session_id}'
        ]
    }
    
    while True:
        service = random.choice(services)
        level = random.choice(log_levels)
        
        # Select a template for this service
        templates = log_templates.get(service, ['Generic log message'])
        template = random.choice(templates)
        
        # Fill in template variables
        message = template.format(
            method=random.choice(['GET', 'POST', 'PUT', 'DELETE']),
            path=random.choice(['/api/users', '/api/products', '/health', '/metrics']),
            duration=random.randint(10, 500),
            user_id=f"user-{random.randint(1000, 9999)}",
            key=f"key-{random.randint(1, 100)}",
            status=random.choice([200, 201, 400, 404, 500]),
            endpoint=random.choice(['/users', '/products', '/orders']),
            allowed=random.choice([True, False]),
            query=f"SELECT * FROM table_{random.randint(1, 10)}",
            table=f"table_{random.randint(1, 10)}",
            active=random.randint(5, 20),
            max=25,
            tx_id=f"tx-{random.randint(10000, 99999)}",
            index=f"idx_{random.randint(1, 5)}",
            size=random.randint(100, 1000),
            result=random.choice(['success', 'failed']),
            token_id=f"token-{random.randint(100000, 999999)}",
            valid=random.choice([True, False]),
            session_id=f"session-{random.randint(10000, 99999)}",
            error=random.choice(['Invalid input', 'Missing field', 'Type mismatch'])
        )
        
        log_entry = generate_log_entry(service, level, message)
        send_logs_to_loki(log_entry)
        
        # Generate multiple logs per iteration
        time.sleep(random.uniform(0.5, 2.0))

if __name__ == '__main__':
    print("Starting log generator...")
    print(f"Sending logs to Loki at {LOKI_URL}")
    
    # Wait for Loki to be ready
    max_retries = 30
    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.get("http://loki:3100/ready", timeout=2)
            if response.status_code == 200:
                print("Loki is ready!")
                break
        except:
            pass
        retry_count += 1
        time.sleep(2)
        print(f"Waiting for Loki to be ready... ({retry_count}/{max_retries})")
    
    try:
        generate_logs()
    except KeyboardInterrupt:
        print("\nShutting down...")

