"""
Tests for the Industrial Logging System.
"""

import pytest
import tempfile
import json
import os
from datetime import datetime
from pathlib import Path

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
from prisma_common.utils.log_monitor import LogPattern, LogMonitor, LogAnalyzer


class TestIndustrialLogging:
    """Test suite for industrial logging system."""
    
    def setup_method(self):
        """Setup for each test."""
        # Create temporary log file
        self.temp_log = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        self.temp_log.close()
        
        # Initialize logging with temp file
        initialize_logging({
            'log_level': 'DEBUG',
            'log_format': 'colorful',
            'log_file': self.temp_log.name,
            'enable_async': False  # Disable async for testing
        })
    
    def teardown_method(self):
        """Cleanup after each test."""
        # Clean up temp file
        if os.path.exists(self.temp_log.name):
            os.unlink(self.temp_log.name)
    
    def test_basic_logging(self):
        """Test basic logging functionality."""
        logger = get_prisma_logger("test.basic")
        
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
        # Verify log file contains messages
        with open(self.temp_log.name, 'r') as f:
            content = f.read()
            assert "Test info message" in content
            assert "Test warning message" in content
            assert "Test error message" in content
    
    def test_structured_logging(self):
        """Test structured logging with context."""
        logger = get_prisma_logger("test.structured")
        
        # Set trace context
        context = set_trace_context(
            user_id="test_user",
            session_id="test_session",
            request_id="test_request"
        )
        
        logger.info("Structured log message", extra={'custom_field': 'test_value'})
        
        # Verify context is set
        assert context.user_id == "test_user"
        assert context.session_id == "test_session"
        assert context.request_id == "test_request"
    
    def test_business_logging(self):
        """Test business event logging."""
        logger = get_prisma_logger("test.business")
        
        business_log(
            logger,
            "User purchase completed",
            metrics={'amount': 99.99, 'currency': 'USD'},
            context={'product_id': 'prod123', 'user_id': 'user456'}
        )
        
        # Verify business log was written
        with open(self.temp_log.name, 'r') as f:
            content = f.read()
            assert "User purchase completed" in content
    
    def test_security_logging(self):
        """Test security event logging."""
        logger = get_prisma_logger("test.security")
        
        security_log(
            logger,
            "Suspicious login attempt",
            LogLevel.WARNING,
            user_id="test_user",
            ip_address="192.168.1.100",
            details={'attempts': 5, 'locked': True}
        )
        
        # Verify security log was written
        with open(self.temp_log.name, 'r') as f:
            content = f.read()
            assert "Suspicious login attempt" in content
    
    def test_audit_logging(self):
        """Test audit event logging."""
        logger = get_prisma_logger("test.audit")
        
        audit_log(
            logger,
            "DELETE",
            "user_account",
            user_id="test_user",
            details={'account_id': 'acc123', 'reason': 'violation'}
        )
        
        # Verify audit log was written
        with open(self.temp_log.name, 'r') as f:
            content = f.read()
            assert "DELETE on user_account" in content
    
    def test_performance_monitoring(self):
        """Test performance monitoring decorator."""
        logger = get_prisma_logger("test.performance")
        
        @performance_monitor(logger, "test_operation")
        def test_function():
            return "test_result"
        
        result = test_function()
        assert result == "test_result"
        
        # Verify performance log was written
        with open(self.temp_log.name, 'r') as f:
            content = f.read()
            assert "Operation completed: test_operation" in content
    
    def test_context_manager(self):
        """Test context manager functionality."""
        logger = get_prisma_logger("test.context")
        
        context = set_trace_context(user_id="context_user")
        
        with context:
            logger.info("Context message")
        
        # Verify context was used
        assert context.user_id == "context_user"
    
    def test_environment_logger(self):
        """Test environment-aware logger."""
        env_logger = get_environment_logger("test.env", "development")
        
        env_logger.info("Environment test message")
        env_logger.debug("Debug message")
        
        # Verify logs were written
        with open(self.temp_log.name, 'r') as f:
            content = f.read()
            assert "Environment test message" in content
    
    def test_log_pattern(self):
        """Test log pattern functionality."""
        pattern = LogPattern(
            name="test_pattern",
            pattern=r"ERROR.*test",
            severity="ERROR",
            threshold=1,
            time_window_minutes=5
        )
        
        assert pattern.name == "test_pattern"
        assert pattern.severity == "ERROR"
        assert pattern.threshold == 1
        assert pattern.compiled_pattern is not None
    
    def test_log_monitor(self):
        """Test log monitor functionality."""
        # Create a monitor (won't actually monitor the temp file in this test)
        patterns = [
            LogPattern(
                name="error_pattern",
                pattern=r"ERROR",
                severity="ERROR",
                threshold=1,
                time_window_minutes=1
            )
        ]
        
        monitor = LogMonitor(self.temp_log.name, patterns)
        
        # Test pattern addition
        monitor.add_pattern(LogPattern(
            name="warning_pattern",
            pattern=r"WARNING",
            severity="WARNING",
            threshold=1,
            time_window_minutes=1
        ))
        
        assert len(monitor.patterns) == 2
        
        # Test pattern removal
        monitor.remove_pattern("warning_pattern")
        assert len(monitor.patterns) == 1
    
    def test_log_analyzer(self):
        """Test log analyzer functionality."""
        # Write some test log entries
        with open(self.temp_log.name, 'w') as f:
            f.write('{"timestamp": "2024-01-01T10:00:00Z", "level": "INFO", "message": "Test message"}\n')
            f.write('{"timestamp": "2024-01-01T10:01:00Z", "level": "ERROR", "message": "Test error"}\n')
            f.write('{"timestamp": "2024-01-01T10:02:00Z", "level": "WARNING", "message": "Test warning"}\n')
        
        analyzer = LogAnalyzer()
        stats = analyzer.analyze_log_file(self.temp_log.name)
        
        assert stats['total_lines'] == 3
        assert stats['error_count'] == 1
        assert stats['warning_count'] == 1
    
    def test_performance_metrics(self):
        """Test performance metrics."""
        metrics = PerformanceMetrics(
            duration_ms=150.5,
            memory_usage_mb=128.0,
            cpu_usage_percent=25.5,
            db_queries=3,
            external_calls=2
        )
        
        assert metrics.duration_ms == 150.5
        assert metrics.memory_usage_mb == 128.0
        assert metrics.cpu_usage_percent == 25.5
        assert metrics.db_queries == 3
        assert metrics.external_calls == 2


class TestLoggingIntegration:
    """Integration tests for logging system."""
    
    def test_full_workflow(self):
        """Test complete logging workflow."""
        # Create temporary log file
        temp_log = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        temp_log.close()
        
        try:
            # Initialize logging
            initialize_logging({
                'log_level': 'DEBUG',
                'log_format': 'json',
                'log_file': temp_log.name,
                'enable_async': False
            })
            
            # Get logger
            logger = get_prisma_logger("integration.test")
            
            # Set context
            context = set_trace_context(
                user_id="integration_user",
                service_name="test_service"
            )
            
            # Log various events
            logger.info("Integration test started")
            
            business_log(
                logger,
                "User action performed",
                metrics={'duration_ms': 100},
                context={'action': 'test_action'}
            )
            
            security_log(
                logger,
                "Security event",
                LogLevel.WARNING,
                user_id="integration_user"
            )
            
            audit_log(
                logger,
                "CREATE",
                "test_resource",
                user_id="integration_user"
            )
            
            # Verify logs were written in JSON format
            with open(temp_log.name, 'r') as f:
                lines = f.readlines()
                
                # Should have at least 4 log entries
                assert len(lines) >= 4
                
                # Parse first JSON log entry
                first_log = json.loads(lines[0])
                assert first_log['level'] == 'INFO'
                assert first_log['message'] == 'Integration test started'
                
                # Verify trace context is included
                assert first_log.get('user_id') == 'integration_user'
                assert first_log.get('service_name') == 'test_service'
        
        finally:
            # Clean up
            if os.path.exists(temp_log.name):
                os.unlink(temp_log.name)


if __name__ == "__main__":
    pytest.main([__file__])
