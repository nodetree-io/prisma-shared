#!/usr/bin/env python3
"""
Simple test script for industrial logging system.
"""

import tempfile
import os
from prisma_common.utils.logging import (
    get_prisma_logger,
    initialize_logging,
    set_trace_context,
    LogLevel,
    business_log,
    security_log,
    audit_log
)


def test_basic_logging():
    """Test basic logging functionality."""
    print("Testing basic logging...")
    
    # Create temporary log file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as temp_file:
        temp_file.close()
        
        try:
            # Initialize logging with file output
            initialize_logging({
                'log_level': 'DEBUG',
                'log_format': 'colorful',
                'log_file': temp_file.name,
                'enable_async': False
            })
            
            # Get logger
            logger = get_prisma_logger("test.basic")
            
            # Test basic logging
            logger.info("Test info message")
            logger.warning("Test warning message")
            logger.error("Test error message")
            
            # Check if file was created and has content
            if os.path.exists(temp_file.name):
                with open(temp_file.name, 'r') as f:
                    content = f.read()
                    print(f"Log file content ({len(content)} chars):")
                    print(content[:500])  # Show first 500 chars
                    
                    # Verify messages are in file
                    if "Test info message" in content:
                        print("✅ Basic logging test PASSED")
                        return True
                    else:
                        print("❌ Basic logging test FAILED - messages not found in file")
                        return False
            else:
                print("❌ Basic logging test FAILED - log file not created")
                return False
                
        finally:
            # Clean up
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


def test_structured_logging():
    """Test structured logging with context."""
    print("\nTesting structured logging...")
    
    # Initialize logging
    initialize_logging({
        'log_level': 'DEBUG',
        'log_format': 'colorful',
        'enable_async': False
    })
    
    # Get logger
    logger = get_prisma_logger("test.structured")
    
    # Set trace context
    context = set_trace_context(
        user_id="test_user",
        session_id="test_session",
        request_id="test_request"
    )
    
    # Test structured logging
    logger.info("Structured log message", extra={'custom_field': 'test_value'})
    
    # Test business logging
    business_log(
        logger,
        "User action performed",
        metrics={'duration_ms': 100},
        context={'action': 'test_action'}
    )
    
    # Test security logging
    security_log(
        logger,
        "Security event",
        LogLevel.WARNING,
        user_id="test_user",
        ip_address="192.168.1.100"
    )
    
    # Test audit logging
    audit_log(
        logger,
        "CREATE",
        "test_resource",
        user_id="test_user",
        details={'resource_id': 'res123'}
    )
    
    print("✅ Structured logging test PASSED")
    return True


def test_performance_monitoring():
    """Test performance monitoring."""
    print("\nTesting performance monitoring...")
    
    from prisma_common.utils.logging import performance_monitor
    
    # Initialize logging
    initialize_logging({
        'log_level': 'DEBUG',
        'log_format': 'colorful',
        'enable_async': False
    })
    
    logger = get_prisma_logger("test.performance")
    
    # Test performance monitoring decorator
    @performance_monitor(logger, "test_operation")
    def test_function():
        import time
        time.sleep(0.01)  # Simulate work
        return "test_result"
    
    result = test_function()
    
    if result == "test_result":
        print("✅ Performance monitoring test PASSED")
        return True
    else:
        print("❌ Performance monitoring test FAILED")
        return False


def main():
    """Run all tests."""
    print("Industrial Logging System - Simple Tests")
    print("=" * 50)
    
    tests = [
        test_basic_logging,
        test_structured_logging,
        test_performance_monitoring,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests PASSED!")
        return 0
    else:
        print("❌ Some tests FAILED!")
        return 1


if __name__ == "__main__":
    exit(main())
