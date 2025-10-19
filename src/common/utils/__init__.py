"""
Prisma Common Utils - Industrial-grade utilities for the Prisma platform.

This module provides comprehensive utilities including:
- Industrial-grade logging system with structured logging, performance monitoring, and alerting
- Environment-specific logging configurations
- Log monitoring and analysis tools
- Context-aware logging for distributed systems
"""

from .logging import (
    # Core logging classes
    LogLevel,
    LogCategory,
    LogContext,
    PerformanceMetrics,
    PrismaLogger,
    
    # Main functions
    get_logger,
    get_prisma_logger,
    set_trace_context,
    initialize_logging,
    
    # Structured logging functions
    log_with_context,
    performance_monitor,
    audit_log,
    security_log,
    business_log,
    
    # Legacy compatibility
    log_function_call,
    log_benchmark_progress,
    log_agent_action,
)

from .logging_config import (
    LoggingConfig,
    EnvironmentLogger,
    get_environment_logger,
    initialize_environment_logging,
)

from .log_monitor import (
    LogPattern,
    Alert,
    LogMetrics,
    LogMonitor,
    LogAnalyzer,
    DEFAULT_PATTERNS,
    create_default_monitor,
)

__all__ = [
    # Core logging
    'LogLevel',
    'LogCategory', 
    'LogContext',
    'PerformanceMetrics',
    'PrismaLogger',
    
    # Logger functions
    'get_logger',
    'get_prisma_logger',
    'set_trace_context',
    'initialize_logging',
    
    # Structured logging
    'log_with_context',
    'performance_monitor',
    'audit_log',
    'security_log',
    'business_log',
    
    # Legacy functions
    'log_function_call',
    'log_benchmark_progress', 
    'log_agent_action',
    
    # Configuration
    'LoggingConfig',
    'EnvironmentLogger',
    'get_environment_logger',
    'initialize_environment_logging',
    
    # Monitoring
    'LogPattern',
    'Alert',
    'LogMetrics',
    'LogMonitor',
    'LogAnalyzer',
    'DEFAULT_PATTERNS',
    'create_default_monitor',
]