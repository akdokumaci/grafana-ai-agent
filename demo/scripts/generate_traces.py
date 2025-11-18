#!/usr/bin/env python3
"""
Generate fake traces and send them to Tempo via OTLP.
"""

import time
import random
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

# Configure OTLP exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="http://tempo:4317",
    insecure=True
)

# Create resource with service name
resource = Resource.create({
    "service.name": "demo-service",
    "service.version": "1.0.0",
    "deployment.environment": "demo"
})

# Set up tracer provider
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Add span processor
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

def generate_trace():
    """Generate a fake trace with multiple spans."""
    services = ['web-server', 'api-server', 'database', 'cache', 'auth-service']
    operations = {
        'web-server': ['handle_request', 'render_template', 'process_response'],
        'api-server': ['process_api_call', 'validate_request', 'execute_business_logic'],
        'database': ['execute_query', 'prepare_statement', 'fetch_results'],
        'cache': ['get_from_cache', 'set_in_cache', 'invalidate_cache'],
        'auth-service': ['authenticate_user', 'validate_token', 'refresh_session']
    }
    
    # Root span
    service = random.choice(services)
    root_operation = random.choice(operations[service])
    
    with tracer.start_as_current_span(
        root_operation,
        attributes={
            "service.name": service,
            "http.method": random.choice(['GET', 'POST', 'PUT', 'DELETE']),
            "http.url": f"/api/{random.choice(['users', 'products', 'orders'])}",
            "http.status_code": random.choice([200, 201, 400, 404, 500]),
        }
    ) as root_span:
        # Simulate some work
        time.sleep(random.uniform(0.01, 0.1))
        
        # Child spans
        num_child_spans = random.randint(1, 3)
        for i in range(num_child_spans):
            child_service = random.choice(services)
            child_operations = operations.get(child_service, ['generic_operation'])
            child_operation = random.choice(child_operations)
            
            with tracer.start_as_current_span(
                child_operation,
                attributes={
                    "service.name": child_service,
                    "operation.type": random.choice(['read', 'write', 'compute']),
                }
            ) as child_span:
                # Simulate work
                time.sleep(random.uniform(0.005, 0.05))
                
                # Sometimes add another nested span
                if random.random() < 0.3:
                    nested_operation = random.choice(operations.get(child_service, ['nested_op']))
                    with tracer.start_as_current_span(
                        nested_operation,
                        attributes={
                            "service.name": child_service,
                            "nested": True
                        }
                    ) as nested_span:
                        time.sleep(random.uniform(0.001, 0.02))

def generate_traces_continuously():
    """Continuously generate traces."""
    while True:
        try:
            generate_trace()
            # Generate traces at varying intervals
            time.sleep(random.uniform(0.5, 2.0))
        except Exception as e:
            print(f"Error generating trace: {e}")
            time.sleep(1)

if __name__ == '__main__':
    print("Starting trace generator...")
    print("Sending traces to Tempo at http://tempo:4317")
    
    # Wait for Tempo to be ready
    import requests
    max_retries = 30
    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.get("http://tempo:3200/ready", timeout=2)
            if response.status_code == 200:
                print("Tempo is ready!")
                break
        except:
            pass
        retry_count += 1
        time.sleep(2)
        print(f"Waiting for Tempo to be ready... ({retry_count}/{max_retries})")
    
    try:
        generate_traces_continuously()
    except KeyboardInterrupt:
        print("\nShutting down...")

