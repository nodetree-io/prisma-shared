"""
Industrial Logging System Usage Examples
Demonstrates various features of the Prisma industrial logging system.
"""

import time
import asyncio
from datetime import datetime
from prisma_common.utils.logging import (
    get_prisma_logger,
    set_trace_context,
    LogLevel,
    LogCategory,
    PerformanceMetrics,
    performance_monitor,
    audit_log,
    security_log,
    business_log,
    initialize_logging
)
from prisma_common.utils.logging_config import get_environment_logger
from prisma_common.utils.log_monitor import create_default_monitor, LogPattern


def basic_logging_example():
    """Basic logging example."""
    print("=== Basic Logging Example ===")
    
    # Get a logger
    logger = get_prisma_logger("example.basic")
    
    # Basic logging
    logger.info("Application started")
    logger.debug("Debug information")
    logger.warning("This is a warning")
    logger.error("This is an error")
    logger.critical("Critical error occurred")


def structured_logging_example():
    """Structured logging with context."""
    print("\n=== Structured Logging Example ===")
    
    logger = get_prisma_logger("example.structured")
    
    # Set trace context
    context = set_trace_context(
        user_id="user123",
        session_id="session456",
        request_id="req789",
        service_name="example-service"
    )
    
    # Log with business context
    business_log(
        logger,
        "User login successful",
        metrics={'login_duration_ms': 150, 'user_type': 'premium'},
        context={'ip_address': '192.168.1.100', 'user_agent': 'Mozilla/5.0'}
    )
    
    # Security logging
    security_log(
        logger,
        "Failed login attempt",
        LogLevel.WARNING,
        user_id="user123",
        ip_address="192.168.1.200",
        details={'attempts': 3, 'locked': False}
    )
    
    # Audit logging
    audit_log(
        logger,
        "CREATE",
        "user_profile",
        user_id="user123",
        details={'profile_id': 'prof456', 'fields_updated': ['name', 'email']}
    )


@performance_monitor(get_prisma_logger("example.performance"), "data_processing")
def process_data(data_size: int):
    """Example function with performance monitoring."""
    print(f"\n=== Performance Monitoring Example ===")
    
    # Simulate data processing
    time.sleep(0.1)  # Simulate work
    
    if data_size > 1000:
        # Simulate memory allocation
        time.sleep(0.05)
    
    return f"Processed {data_size} records"


def performance_logging_example():
    """Performance logging example."""
    logger = get_prisma_logger("example.performance")
    
    # Function with performance monitoring decorator
    result = process_data(500)
    print(f"Result: {result}")
    
    result = process_data(2000)  # This will take longer
    print(f"Result: {result}")


def environment_logging_example():
    """Environment-specific logging example."""
    print("\n=== Environment Logging Example ===")
    
    # Get environment-aware logger
    env_logger = get_environment_logger("example.environment", "development")
    
    env_logger.info("This is a development log message")
    env_logger.debug("Debug message (only visible in development)")
    
    # Security logging
    env_logger.security("Suspicious activity detected", "CRITICAL", 
                       user_id="user123", ip_address="10.0.0.1")
    
    # Performance logging
    env_logger.performance("api_call", 250.5, endpoint="/api/users", method="GET")


async def async_logging_example():
    """Async logging example."""
    print("\n=== Async Logging Example ===")
    
    logger = get_prisma_logger("example.async")
    
    async def async_operation():
        logger.info("Starting async operation")
        await asyncio.sleep(0.1)
        logger.info("Async operation completed")
    
    await async_operation()


def log_monitoring_example():
    """Log monitoring example."""
    print("\n=== Log Monitoring Example ===")
    
    # Create a log monitor (this would normally monitor a real log file)
    logger = get_prisma_logger("example.monitoring")
    
    def alert_handler(alert):
        print(f"ALERT: {alert.message}")
        print(f"Severity: {alert.severity}")
        print(f"Pattern: {alert.pattern_name}")
        print(f"Count: {alert.count}")
    
    # In a real scenario, you would monitor an actual log file
    # monitor = create_default_monitor("/var/log/prisma/application.log", alert_handler)
    # monitor.start_monitoring()
    
    # Simulate some log events that would trigger monitoring
    logger.error("Database connection failed")
    logger.warning("High memory usage detected")
    logger.critical("Out of memory error")


def error_handling_example():
    """Error handling and logging example."""
    print("\n=== Error Handling Example ===")
    
    logger = get_prisma_logger("example.error_handling")
    
    try:
        # Simulate an error
        raise ValueError("This is a test error")
    except Exception as e:
        logger.error(
            "Error in data processing",
            exc_info=True,
            extra={
                'error_type': type(e).__name__,
                'error_message': str(e),
                'operation': 'data_processing',
                'input_data_size': 1000
            }
        )


def context_management_example():
    """Context management example."""
    print("\n=== Context Management Example ===")
    
    logger = get_prisma_logger("example.context")
    
    # Set different contexts for different operations
    context1 = set_trace_context(user_id="user1", operation="user_management")
    with context1:
        logger.info("User profile updated")
        logger.info("User preferences saved")
    
    context2 = set_trace_context(user_id="user2", operation="payment_processing")
    with context2:
        logger.info("Payment initiated")
        logger.info("Payment completed")
    
    # Global context
    set_trace_context(service_name="api-gateway", version="1.2.0")
    logger.info("API request received")
    logger.info("API response sent")


def main():
    """Run all logging examples."""
    print("Industrial Logging System Examples")
    print("=" * 50)
    
    # Initialize logging with custom configuration
    initialize_logging({
        'log_level': 'DEBUG',
        'log_format': 'colorful',  # Use colorful format for examples
        'enable_async': True
    })
    
    # Run examples
    basic_logging_example()
    structured_logging_example()
    performance_logging_example()
    environment_logging_example()
    asyncio.run(async_logging_example())
    log_monitoring_example()
    error_handling_example()
    context_management_example()
    
    print("\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    main()
