import multiprocessing
import os

bind = "0.0.0.0:8000"

# Dynamically set workers based on CPU cores
workers = multiprocessing.cpu_count() * 2 + 1

# Security Headers
secure_scheme_headers = {'X-Forwarded-Proto': 'https'}

# Prevent Slowloris DoS Attacks
timeout = 30  # Kill workers if they hang longer than 30 seconds
keepalive = 5  # Keep connections open for 5 seconds (reduce if under attack)

# Limit Request Sizes to Prevent Abuse
limit_request_line = 4094  # Max size of HTTP request line
limit_request_fields = 100  # Max number of HTTP headers
limit_request_field_size = 8190  # Max size of an HTTP header field

# Logging
accesslog = '-'  # Log to stdout (good for Docker)
errorlog = '-' 
loglevel = 'info'

# Graceful Worker Restarts (Useful for memory leaks)
max_requests = 1000
max_requests_jitter = 50  # Add randomness to avoid all workers restarting at once

# Worker Class (use 'gthread' if you expect many concurrent requests but low CPU)
worker_class = 'sync'  # Alternatives: 'gthread', 'gevent' if using async views
