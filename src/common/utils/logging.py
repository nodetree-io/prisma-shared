"""
Industrial-grade logging system for Prisma platform.
Provides structured logging, performance monitoring, error tracking, and audit trails.
"""

import logging
import logging.handlers
import json
import time
import traceback
import uuid
import os
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union, List, Callable
from pathlib import Path
from contextvars import ContextVar
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import functools

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

try:
    from colorama import init, Fore, Back, Style
    COLORAMA_AVAILABLE = True
    init(autoreset=True)
except ImportError:
    COLORAMA_AVAILABLE = False


class LogLevel(Enum):
    """Standardized log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Log categories for different types of events."""
    SYSTEM = "system"
    APPLICATION = "application"
    SECURITY = "security"
    AUDIT = "audit"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    ERROR = "error"
    API = "api"
    DATABASE = "database"
    EXTERNAL = "external"


@dataclass
class LogContext:
    """Structured log context."""
    trace_id: str
    span_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    service_name: Optional[str] = None
    operation: Optional[str] = None
    component: Optional[str] = None
    version: Optional[str] = None
    environment: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass


@dataclass
class PerformanceMetrics:
    """Performance metrics for logging."""
    duration_ms: float
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    request_size_bytes: Optional[int] = None
    response_size_bytes: Optional[int] = None
    cache_hits: Optional[int] = None
    cache_misses: Optional[int] = None
    db_queries: Optional[int] = None
    external_calls: Optional[int] = None


# Context variables for distributed tracing
_trace_context: ContextVar[LogContext] = ContextVar('trace_context', default=None)
_request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for production logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Extract structured data
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process,
        }
        
        # Add trace context if available
        trace_ctx = _trace_context.get()
        if trace_ctx:
            log_data.update(asdict(trace_ctx))
        
        # Add request context if available
        req_ctx = _request_context.get()
        if req_ctx:
            log_data.update(req_ctx)
        
        # Add extra fields from record
        if hasattr(record, 'category'):
            log_data['category'] = record.category.value if isinstance(record.category, LogCategory) else record.category
        
        if hasattr(record, 'metrics'):
            log_data['metrics'] = asdict(record.metrics) if isinstance(record.metrics, PerformanceMetrics) else record.metrics
        
        if hasattr(record, 'error_details'):
            log_data['error_details'] = record.error_details
        
        if hasattr(record, 'business_context'):
            log_data['business_context'] = record.business_context
        
        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 
                          'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage']:
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class ColorfulFormatter(logging.Formatter):
    """Colorful formatter for development and debugging."""
    
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Back.WHITE
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        if not COLORAMA_AVAILABLE:
            return super().format(record)
        
        log_color = self.COLORS.get(record.levelno, '')
        
        # Format with colors
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        formatted = f"{log_color}[{timestamp}] {record.levelname:8} {record.name:20} {record.getMessage()}{Style.RESET_ALL}"
        
        # Add trace info if available
        trace_ctx = _trace_context.get()
        if trace_ctx:
            formatted += f" {Fore.BLUE}[trace:{trace_ctx.trace_id[:8]}]"
        
        return formatted


class AsyncLogHandler(logging.Handler):
    """Asynchronous log handler for high-performance logging."""
    
    def __init__(self, target_handler: logging.Handler, max_queue_size: int = 10000):
        super().__init__()
        self.target_handler = target_handler
        self.queue = queue.Queue(maxsize=max_queue_size)
        self.thread = threading.Thread(target=self._process_logs, daemon=True)
        self.thread.start()
    
    def emit(self, record: logging.LogRecord):
        """Emit log record to queue."""
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            # Fallback to synchronous logging if queue is full
            self.target_handler.emit(record)
    
    def _process_logs(self):
        """Process logs from queue."""
        while True:
            try:
                record = self.queue.get(timeout=1)
                self.target_handler.emit(record)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                # Log error but don't crash the handler
                pass


class PrismaLogger:
    """Industrial-grade logger for Prisma platform."""
    
    _loggers: Dict[str, logging.Logger] = {}
    _initialized = False
    
    @classmethod
    def initialize(cls, 
                   log_level: str = "INFO",
                   log_format: str = "json",  # "json" or "colorful"
                   log_file: Optional[str] = None,
                   max_file_size: int = 100 * 1024 * 1024,  # 100MB
                   backup_count: int = 5,
                   enable_async: bool = True,
                   enable_structlog: bool = True):
        """Initialize the logging system."""
        # Always reinitialize to allow configuration changes
        cls._initialized = False
        
        # Configure structlog if available
        if enable_structlog and STRUCTLOG_AVAILABLE:
            cls._configure_structlog()
        
        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        if log_format == "json":
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(ColorfulFormatter())
        
        if enable_async:
            console_handler = AsyncLogHandler(console_handler)
        
        root_logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_file_size, backupCount=backup_count
            )
            file_handler.setFormatter(StructuredFormatter())
            
            if enable_async:
                file_handler = AsyncLogHandler(file_handler)
            
            root_logger.addHandler(file_handler)
        
        cls._initialized = True
    
    @classmethod
    def _configure_structlog(cls):
        """Configure structlog for structured logging."""
        if not STRUCTLOG_AVAILABLE:
            return
        
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    @classmethod
    def get_logger(cls, name: str, **kwargs) -> logging.Logger:
        """Get a configured logger instance."""
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def create_trace_context(cls, 
                           trace_id: Optional[str] = None,
                           span_id: Optional[str] = None,
                           user_id: Optional[str] = None,
                           session_id: Optional[str] = None,
                           request_id: Optional[str] = None,
                           service_name: Optional[str] = None,
                           operation: Optional[str] = None,
                           component: Optional[str] = None,
                           **extra) -> LogContext:
        """Create a new trace context."""
        return LogContext(
            trace_id=trace_id or str(uuid.uuid4()),
            span_id=span_id or str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            service_name=service_name or os.getenv('SERVICE_NAME', 'prisma-service'),
            operation=operation,
            component=component,
            version=os.getenv('SERVICE_VERSION', '1.0.0'),
            environment=os.getenv('ENVIRONMENT', 'development'),
            extra=extra or {}
        )
    
    @classmethod
    def set_trace_context(cls, context: LogContext):
        """Set the current trace context."""
        _trace_context.set(context)
    
    @classmethod
    def set_request_context(cls, **kwargs):
        """Set request-specific context."""
        current = _request_context.get()
        current.update(kwargs)
        _request_context.set(current)


def get_logger(name: str, **kwargs) -> logging.Logger:
    """Get a configured logger instance."""
    return PrismaLogger.get_logger(name, **kwargs)


def set_trace_context(**kwargs):
    """Set trace context for distributed logging."""
    context = PrismaLogger.create_trace_context(**kwargs)
    PrismaLogger.set_trace_context(context)
    return context


def log_with_context(logger: logging.Logger, 
                    level: LogLevel,
                    message: str,
                    category: Optional[LogCategory] = None,
                    metrics: Optional[PerformanceMetrics] = None,
                    error_details: Optional[Dict[str, Any]] = None,
                    business_context: Optional[Dict[str, Any]] = None,
                    **extra):
    """Log with structured context."""
    log_record = logger.makeRecord(
        logger.name, getattr(logging, level.value), "", 0, message, (), None
    )
    
    if category:
        log_record.category = category
    if metrics:
        log_record.metrics = metrics
    if error_details:
        log_record.error_details = error_details
    if business_context:
        log_record.business_context = business_context
    
    # Add extra fields
    for key, value in extra.items():
        setattr(log_record, key, value)
    
    logger.handle(log_record)


def performance_monitor(logger: logging.Logger, 
                       operation: str,
                       category: LogCategory = LogCategory.PERFORMANCE):
    """Decorator for performance monitoring."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = _get_memory_usage()
            
            try:
                result = func(*args, **kwargs)
                
                # Log success
                duration = (time.time() - start_time) * 1000
                end_memory = _get_memory_usage()
                
                metrics = PerformanceMetrics(
                    duration_ms=duration,
                    memory_usage_mb=end_memory - start_memory if end_memory and start_memory else None
                )
                
                log_with_context(
                    logger, LogLevel.INFO,
                    f"Operation completed: {operation}",
                    category=category,
                    metrics=metrics,
                    operation=operation
                )
                
                return result
                
            except Exception as e:
                # Log error
                duration = (time.time() - start_time) * 1000
                
                metrics = PerformanceMetrics(duration_ms=duration)
                error_details = {
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'traceback': traceback.format_exc()
                }
                
                log_with_context(
                    logger, LogLevel.ERROR,
                    f"Operation failed: {operation}",
                    category=LogCategory.ERROR,
                    metrics=metrics,
                    error_details=error_details,
                    operation=operation
                )
                
                raise
        
        return wrapper
    return decorator


def audit_log(logger: logging.Logger, 
              action: str,
              resource: str,
              user_id: Optional[str] = None,
              details: Optional[Dict[str, Any]] = None):
    """Log audit events."""
    business_context = {
        'audit_action': action,
        'audit_resource': resource,
        'audit_timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    if details:
        business_context.update(details)
    
    log_with_context(
        logger, LogLevel.INFO,
        f"Audit: {action} on {resource}",
        category=LogCategory.AUDIT,
        business_context=business_context,
        user_id=user_id
    )


def security_log(logger: logging.Logger,
                event: str,
                severity: LogLevel = LogLevel.WARNING,
                user_id: Optional[str] = None,
                ip_address: Optional[str] = None,
                details: Optional[Dict[str, Any]] = None):
    """Log security events."""
    business_context = {
        'security_event': event,
        'security_timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    if ip_address:
        business_context['ip_address'] = ip_address
    
    if details:
        business_context.update(details)
    
    log_with_context(
        logger, severity,
        f"Security: {event}",
        category=LogCategory.SECURITY,
        business_context=business_context,
        user_id=user_id
    )


def business_log(logger: logging.Logger,
                event: str,
                level: LogLevel = LogLevel.INFO,
                metrics: Optional[Dict[str, Any]] = None,
                context: Optional[Dict[str, Any]] = None):
    """Log business events."""
    business_context = {
        'business_event': event,
        'business_timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    if metrics:
        business_context['business_metrics'] = metrics
    
    if context:
        business_context.update(context)
    
    log_with_context(
        logger, level,
        f"Business: {event}",
        category=LogCategory.BUSINESS,
        business_context=business_context
    )


def _get_memory_usage() -> Optional[float]:
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return None


# Initialize logging system
def initialize_logging(config: Optional[Dict[str, Any]] = None):
    """Initialize the industrial logging system."""
    default_config = {
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'log_format': os.getenv('LOG_FORMAT', 'json'),
        'log_file': os.getenv('LOG_FILE'),
        'max_file_size': int(os.getenv('LOG_MAX_FILE_SIZE', 100 * 1024 * 1024)),
        'backup_count': int(os.getenv('LOG_BACKUP_COUNT', 5)),
        'enable_async': os.getenv('LOG_ENABLE_ASYNC', 'true').lower() == 'true',
        'enable_structlog': os.getenv('LOG_ENABLE_STRUCTLOG', 'true').lower() == 'true'
    }
    
    if config:
        default_config.update(config)
    
    PrismaLogger.initialize(**default_config)


# Convenience function for getting logger
def get_prisma_logger(name: str = None) -> logging.Logger:
    """Get a Prisma logger instance."""
    if name is None:
        name = __name__
    return get_logger(name)


# Legacy compatibility
def log_function_call(func_name: str, args: str = "", result: str = ""):
    """Log function calls for debugging."""
    logger = get_prisma_logger()
    log_with_context(
        logger, LogLevel.DEBUG,
        f"Function call: {func_name}({args}) -> {result}",
        category=LogCategory.APPLICATION,
        function_name=func_name
    )


def log_benchmark_progress(benchmark: str, case_num: int, total: int, score: float = None):
    """Log benchmark progress."""
    logger = get_prisma_logger()
    metrics = {'score': score} if score is not None else None
    business_log(
        logger, f"Benchmark {benchmark}: Case {case_num}/{total}",
        metrics=metrics,
        context={'benchmark': benchmark, 'case_num': case_num, 'total': total}
    )


def log_agent_action(agent_type: str, action: str, details: str = ""):
    """Log agent actions."""
    logger = get_prisma_logger()
    business_log(
        logger, f"Agent [{agent_type}]: {action}",
        context={'agent_type': agent_type, 'action': action, 'details': details}
    )


# Initialize on import
initialize_logging()
