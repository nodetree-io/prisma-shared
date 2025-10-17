"""
Logging configuration for different environments.
Provides environment-specific logging setups for development, staging, and production.
"""

import os
import logging.config
from typing import Dict, Any, Optional
from pathlib import Path


class LoggingConfig:
    """Centralized logging configuration for Prisma platform."""
    
    # Base configuration
    BASE_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d, "thread": %(thread)d, "process": %(process)d}',
                'datefmt': '%Y-%m-%dT%H:%M:%S.%fZ'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'json',
                'filename': '/var/log/prisma/application.log',
                'maxBytes': 104857600,  # 100MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'json',
                'filename': '/var/log/prisma/error.log',
                'maxBytes': 104857600,  # 100MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'audit_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'json',
                'filename': '/var/log/prisma/audit.log',
                'maxBytes': 104857600,  # 100MB
                'backupCount': 10,
                'encoding': 'utf8'
            },
            'security_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'WARNING',
                'formatter': 'json',
                'filename': '/var/log/prisma/security.log',
                'maxBytes': 104857600,  # 100MB
                'backupCount': 10,
                'encoding': 'utf8'
            },
            'performance_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'json',
                'filename': '/var/log/prisma/performance.log',
                'maxBytes': 104857600,  # 100MB
                'backupCount': 5,
                'encoding': 'utf8'
            }
        },
        'loggers': {
            'prisma': {
                'level': 'DEBUG',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'prisma.audit': {
                'level': 'INFO',
                'handlers': ['audit_file'],
                'propagate': False
            },
            'prisma.security': {
                'level': 'WARNING',
                'handlers': ['security_file'],
                'propagate': False
            },
            'prisma.performance': {
                'level': 'INFO',
                'handlers': ['performance_file'],
                'propagate': False
            },
            'prisma.error': {
                'level': 'ERROR',
                'handlers': ['error_file'],
                'propagate': False
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console']
        }
    }
    
    @classmethod
    def get_development_config(cls) -> Dict[str, Any]:
        """Get logging configuration for development environment."""
        config = cls.BASE_CONFIG.copy()
        
        # Development-specific overrides
        config['handlers']['console']['level'] = 'DEBUG'
        config['handlers']['console']['formatter'] = 'detailed'
        config['loggers']['prisma']['level'] = 'DEBUG'
        config['root']['level'] = 'DEBUG'
        
        # Use local file paths for development
        log_dir = Path.cwd() / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        config['handlers']['file']['filename'] = str(log_dir / 'application.log')
        config['handlers']['error_file']['filename'] = str(log_dir / 'error.log')
        config['handlers']['audit_file']['filename'] = str(log_dir / 'audit.log')
        config['handlers']['security_file']['filename'] = str(log_dir / 'security.log')
        config['handlers']['performance_file']['filename'] = str(log_dir / 'performance.log')
        
        return config
    
    @classmethod
    def get_staging_config(cls) -> Dict[str, Any]:
        """Get logging configuration for staging environment."""
        config = cls.BASE_CONFIG.copy()
        
        # Staging-specific overrides
        config['handlers']['console']['level'] = 'INFO'
        config['handlers']['console']['formatter'] = 'json'
        config['loggers']['prisma']['level'] = 'INFO'
        config['root']['level'] = 'INFO'
        
        # Use container-friendly paths
        config['handlers']['file']['filename'] = '/app/logs/application.log'
        config['handlers']['error_file']['filename'] = '/app/logs/error.log'
        config['handlers']['audit_file']['filename'] = '/app/logs/audit.log'
        config['handlers']['security_file']['filename'] = '/app/logs/security.log'
        config['handlers']['performance_file']['filename'] = '/app/logs/performance.log'
        
        return config
    
    @classmethod
    def get_production_config(cls) -> Dict[str, Any]:
        """Get logging configuration for production environment."""
        config = cls.BASE_CONFIG.copy()
        
        # Production-specific overrides
        config['handlers']['console']['level'] = 'WARNING'
        config['handlers']['console']['formatter'] = 'json'
        config['loggers']['prisma']['level'] = 'INFO'
        config['root']['level'] = 'WARNING'
        
        # Production log paths
        config['handlers']['file']['filename'] = '/var/log/prisma/application.log'
        config['handlers']['error_file']['filename'] = '/var/log/prisma/error.log'
        config['handlers']['audit_file']['filename'] = '/var/log/prisma/audit.log'
        config['handlers']['security_file']['filename'] = '/var/log/prisma/security.log'
        config['handlers']['performance_file']['filename'] = '/var/log/prisma/performance.log'
        
        # Add syslog handler for production
        config['handlers']['syslog'] = {
            'class': 'logging.handlers.SysLogHandler',
            'level': 'WARNING',
            'formatter': 'json',
            'address': '/dev/log',
            'facility': 'local7'
        }
        
        # Route critical logs to syslog
        config['loggers']['prisma.error']['handlers'].append('syslog')
        config['loggers']['prisma.security']['handlers'].append('syslog')
        
        return config
    
    @classmethod
    def get_config(cls, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get logging configuration for the specified environment."""
        if environment is None:
            environment = os.getenv('ENVIRONMENT', 'development')
        
        environment = environment.lower()
        
        if environment == 'production' or environment == 'prod':
            return cls.get_production_config()
        elif environment == 'staging' or environment == 'stage':
            return cls.get_staging_config()
        else:
            return cls.get_development_config()
    
    @classmethod
    def setup_logging(cls, environment: Optional[str] = None):
        """Setup logging configuration for the current environment."""
        config = cls.get_config(environment)
        
        # Ensure log directories exist
        for handler_config in config['handlers'].values():
            if 'filename' in handler_config:
                log_file = Path(handler_config['filename'])
                log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Apply configuration
        logging.config.dictConfig(config)
        
        # Log configuration setup
        logger = logging.getLogger('prisma')
        logger.info(f"Logging configured for environment: {environment or 'default'}")


# Environment-specific logging utilities
class EnvironmentLogger:
    """Environment-aware logger wrapper."""
    
    def __init__(self, name: str, environment: Optional[str] = None):
        self.name = name
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.logger = logging.getLogger(name)
        
        # Set up environment-specific configuration
        self._setup_environment_logging()
    
    def _setup_environment_logging(self):
        """Setup environment-specific logging behavior."""
        if self.environment == 'production':
            # In production, reduce noise and focus on important events
            self.logger.setLevel(logging.INFO)
        elif self.environment == 'staging':
            # In staging, log more details for testing
            self.logger.setLevel(logging.DEBUG)
        else:
            # In development, log everything
            self.logger.setLevel(logging.DEBUG)
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(msg, *args, **kwargs)
    
    def audit(self, action: str, resource: str, **details):
        """Log audit event."""
        audit_logger = logging.getLogger('prisma.audit')
        audit_logger.info(f"AUDIT: {action} on {resource}", extra=details)
    
    def security(self, event: str, severity: str = 'WARNING', **details):
        """Log security event."""
        security_logger = logging.getLogger('prisma.security')
        level = getattr(logging, severity.upper(), logging.WARNING)
        security_logger.log(level, f"SECURITY: {event}", extra=details)
    
    def performance(self, operation: str, duration_ms: float, **metrics):
        """Log performance metrics."""
        perf_logger = logging.getLogger('prisma.performance')
        perf_logger.info(f"PERFORMANCE: {operation} took {duration_ms}ms", extra=metrics)


def get_environment_logger(name: str, environment: Optional[str] = None) -> EnvironmentLogger:
    """Get an environment-aware logger."""
    return EnvironmentLogger(name, environment)


# Initialize logging on import
def initialize_environment_logging(environment: Optional[str] = None):
    """Initialize environment-specific logging."""
    LoggingConfig.setup_logging(environment)


# Auto-initialize based on environment
initialize_environment_logging()
