# Industrial Logging System

## Overview

The Prisma Industrial Logging System is a comprehensive, enterprise-grade logging solution designed for microservices architectures. It provides structured logging, performance monitoring, real-time alerting, and distributed tracing capabilities.

## Features

### 🏗️ **Structured Logging**
- JSON-formatted logs for production environments
- Colorful console output for development
- Context-aware logging with distributed tracing
- Automatic log rotation and compression

### 📊 **Performance Monitoring**
- Automatic performance metrics collection
- Memory and CPU usage tracking
- Request/response time monitoring
- Database query performance tracking

### 🚨 **Real-time Alerting**
- Configurable log pattern monitoring
- Threshold-based alerting
- Multiple alert channels (Email, Slack, PagerDuty)
- Alert acknowledgment and resolution tracking

### 🔍 **Log Analysis**
- Real-time log analysis
- Historical log pattern analysis
- Error rate monitoring
- Performance trend analysis

### 🌐 **Distributed Tracing**
- Request tracing across microservices
- Span correlation and context propagation
- Performance bottleneck identification
- Service dependency mapping

## Quick Start

### Basic Usage

```python
from prisma_common.utils.logging import get_prisma_logger, initialize_logging

# Initialize logging system
initialize_logging({
    'log_level': 'INFO',
    'log_format': 'json',
    'log_file': '/var/log/prisma/application.log'
})

# Get a logger
logger = get_prisma_logger("my.service")

# Basic logging
logger.info("Application started")
logger.error("An error occurred", extra={'error_code': 'E001'})
```

### Structured Logging with Context

```python
from prisma_common.utils.logging import (
    set_trace_context, 
    business_log, 
    security_log, 
    audit_log
)

# Set distributed tracing context
context = set_trace_context(
    user_id="user123",
    session_id="session456", 
    request_id="req789",
    service_name="user-service"
)

# Business event logging
business_log(
    logger,
    "User profile updated",
    metrics={'duration_ms': 150, 'fields_updated': 3},
    context={'profile_id': 'prof123'}
)

# Security event logging
security_log(
    logger,
    "Failed login attempt",
    LogLevel.WARNING,
    user_id="user123",
    ip_address="192.168.1.100",
    details={'attempts': 3}
)

# Audit logging
audit_log(
    logger,
    "DELETE",
    "user_account",
    user_id="user123",
    details={'account_id': 'acc456', 'reason': 'user_request'}
)
```

### Performance Monitoring

```python
from prisma_common.utils.logging import performance_monitor

@performance_monitor(logger, "data_processing")
def process_large_dataset(data):
    """Function with automatic performance monitoring."""
    # Your processing logic here
    return processed_data

# Manual performance logging
from prisma_common.utils.logging import PerformanceMetrics

metrics = PerformanceMetrics(
    duration_ms=250.5,
    memory_usage_mb=128.5,
    cpu_usage_percent=15.2,
    db_queries=5
)

log_with_context(
    logger, LogLevel.INFO,
    "Database query completed",
    category=LogCategory.PERFORMANCE,
    metrics=metrics
)
```

## Configuration

### Environment-based Configuration

The logging system automatically configures itself based on the `ENVIRONMENT` variable:

- **Development**: Colorful console output, DEBUG level
- **Staging**: JSON format, INFO level, file logging
- **Production**: JSON format, WARNING+ level, syslog integration

### Custom Configuration

```python
from prisma_common.utils.logging_config import LoggingConfig

# Custom configuration
config = LoggingConfig.get_production_config()
logging.config.dictConfig(config)
```

### YAML Configuration

```yaml
# config/logging.yaml
production:
  handlers:
    file:
      class: logging.handlers.RotatingFileHandler
      level: INFO
      formatter: json
      filename: /var/log/prisma/application.log
      maxBytes: 104857600
      backupCount: 10
```

## Log Monitoring

### Real-time Monitoring

```python
from prisma_common.utils.log_monitor import create_default_monitor

def alert_handler(alert):
    print(f"ALERT: {alert.message}")
    # Send to Slack, Email, etc.

# Create monitor with default patterns
monitor = create_default_monitor(
    "/var/log/prisma/application.log",
    alert_handler
)

# Start monitoring
monitor.start_monitoring()

# Check active alerts
active_alerts = monitor.get_active_alerts()
for alert in active_alerts:
    print(f"Active: {alert.pattern_name} - {alert.count} occurrences")
```

### Custom Monitoring Patterns

```python
from prisma_common.utils.log_monitor import LogPattern, LogMonitor

# Define custom patterns
patterns = [
    LogPattern(
        name="api_errors",
        pattern=r'"level":\s*"ERROR".*"api"',
        severity="ERROR",
        threshold=5,
        time_window_minutes=5
    ),
    LogPattern(
        name="slow_queries", 
        pattern=r'query.*took.*[5-9]\d{3,}ms',
        severity="WARNING",
        threshold=3,
        time_window_minutes=10
    )
]

monitor = LogMonitor("/var/log/prisma/application.log", patterns)
monitor.start_monitoring()
```

## Log Categories

The system supports different log categories for better organization:

- **SYSTEM**: System-level events
- **APPLICATION**: Application logic events  
- **SECURITY**: Security-related events
- **AUDIT**: Audit trail events
- **PERFORMANCE**: Performance metrics
- **BUSINESS**: Business logic events
- **ERROR**: Error events
- **API**: API-related events
- **DATABASE**: Database operations
- **EXTERNAL**: External service calls

## Distributed Tracing

### Setting Trace Context

```python
from prisma_common.utils.logging import set_trace_context

# Set context for a request
context = set_trace_context(
    trace_id="550e8400-e29b-41d4-a716-446655440000",
    span_id="6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    user_id="user123",
    request_id="req789",
    service_name="api-gateway"
)

# All subsequent logs will include this context
logger.info("Processing request")  # Includes trace context
```

### Context Propagation

```python
# In microservice A
context = set_trace_context(
    trace_id="trace123",
    user_id="user456"
)

# Make HTTP call to microservice B
headers = {
    'X-Trace-ID': context.trace_id,
    'X-User-ID': context.user_id
}

# In microservice B
trace_id = request.headers.get('X-Trace-ID')
user_id = request.headers.get('X-User-ID')

set_trace_context(
    trace_id=trace_id,
    user_id=user_id,
    service_name="user-service"
)
```

## Alerting

### Default Alert Patterns

The system includes pre-configured alert patterns for common issues:

- **High Error Rate**: >10 errors in 5 minutes
- **Database Connection Errors**: Connection failures
- **Memory Leaks**: Memory exhaustion warnings
- **Authentication Failures**: Failed login attempts
- **API Rate Limiting**: Rate limit violations
- **Slow Queries**: Database performance issues
- **External Service Failures**: Third-party service errors

### Alert Management

```python
# Get active alerts
active_alerts = monitor.get_active_alerts()

# Acknowledge an alert
monitor.acknowledge_alert(alert_id)

# Resolve an alert
monitor.resolve_alert(alert_id)

# Get metrics summary
metrics = monitor.get_metrics_summary()
print(f"Error rate: {metrics['error_count']} errors/minute")
```

## Performance Considerations

### Asynchronous Logging

The system uses asynchronous logging by default for high-performance scenarios:

```python
# Enable async logging (default)
initialize_logging({
    'enable_async': True,
    'max_queue_size': 10000
})
```

### Log Rotation

Automatic log rotation prevents disk space issues:

```python
# Configure rotation
initialize_logging({
    'max_file_size': 100 * 1024 * 1024,  # 100MB
    'backup_count': 5
})
```

### Memory Usage

The monitoring system tracks memory usage:

```python
# Memory usage is automatically tracked
metrics = monitor.get_metrics_summary()
print(f"Memory usage: {metrics['memory_usage_mb']} MB")
```

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI
from prisma_common.utils.logging import get_prisma_logger, set_trace_context

app = FastAPI()
logger = get_prisma_logger("api")

@app.middleware("http")
async def logging_middleware(request, call_next):
    # Set trace context
    context = set_trace_context(
        request_id=request.headers.get("X-Request-ID"),
        service_name="api-gateway"
    )
    
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    logger.info(f"Response: {response.status_code}")
    return response
```

### Database Integration

```python
from sqlalchemy import event
from prisma_common.utils.logging import get_prisma_logger

logger = get_prisma_logger("database")

@event.listens_for(Engine, "before_cursor_execute")
def log_sql_queries(conn, cursor, statement, parameters, context, executemany):
    logger.debug(f"SQL Query: {statement}", extra={
        'parameters': parameters,
        'executemany': executemany
    })

@event.listens_for(Engine, "after_cursor_execute") 
def log_query_timing(conn, cursor, statement, parameters, context, executemany):
    duration = time.time() - context._start_time
    logger.info(f"Query completed in {duration:.3f}s", extra={
        'duration_ms': duration * 1000,
        'statement': statement[:100]
    })
```

## Best Practices

### 1. Use Appropriate Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Something unexpected happened but application continues
- **ERROR**: Error occurred but application can continue
- **CRITICAL**: Serious error, application may not be able to continue

### 2. Include Context
Always include relevant context in your logs:

```python
# Good
logger.error("Database connection failed", extra={
    'database': 'postgresql',
    'host': 'db.example.com',
    'port': 5432,
    'error_code': 'CONN_REFUSED'
})

# Bad
logger.error("Database connection failed")
```

### 3. Use Structured Logging
Prefer structured logging over string formatting:

```python
# Good
logger.info("User action", extra={
    'user_id': user_id,
    'action': 'login',
    'ip_address': request.remote_addr
})

# Bad
logger.info(f"User {user_id} performed {action} from {ip_address}")
```

### 4. Monitor Performance
Use performance monitoring decorators for critical functions:

```python
@performance_monitor(logger, "user_authentication")
def authenticate_user(username, password):
    # Authentication logic
    pass
```

### 5. Set Up Alerting
Configure appropriate alerting for your environment:

```python
# Set up monitoring for critical patterns
monitor = create_default_monitor(log_file_path, alert_handler)
monitor.start_monitoring()
```

## Troubleshooting

### Common Issues

1. **Log files not rotating**: Check file permissions and disk space
2. **High memory usage**: Reduce queue size or enable async logging
3. **Missing logs**: Check log level configuration and handler setup
4. **Alert spam**: Adjust thresholds or disable noisy patterns

### Debug Mode

Enable debug mode for troubleshooting:

```python
initialize_logging({
    'log_level': 'DEBUG',
    'log_format': 'colorful'
})
```

### Log Analysis

Use the built-in log analyzer:

```python
from prisma_common.utils.log_monitor import LogAnalyzer

analyzer = LogAnalyzer()
stats = analyzer.analyze_log_file("/var/log/prisma/application.log")
print(f"Total errors: {stats['error_count']}")
print(f"Top errors: {stats['top_errors']}")
```

## Migration from Basic Logging

If you're migrating from basic logging, follow these steps:

1. **Install dependencies**:
   ```bash
   pip install structlog psutil
   ```

2. **Update imports**:
   ```python
   # Old
   from prisma_common.utils.logging import get_logger
   
   # New  
   from prisma_common.utils.logging import get_prisma_logger
   ```

3. **Initialize logging**:
   ```python
   from prisma_common.utils.logging import initialize_logging
   initialize_logging()
   ```

4. **Add structured context**:
   ```python
   # Add trace context where needed
   set_trace_context(user_id=user_id, request_id=request_id)
   ```

5. **Enable monitoring**:
   ```python
   monitor = create_default_monitor(log_file_path)
   monitor.start_monitoring()
   ```

This industrial logging system provides enterprise-grade logging capabilities while maintaining ease of use and performance. It's designed to scale with your application and provide the visibility needed for production operations.
