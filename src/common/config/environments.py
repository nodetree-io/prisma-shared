"""
Environment configuration management for Prisma Common SDK.
Provides environment-specific configuration loading.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


def load_environment_config(environment: Optional[str] = None) -> Dict[str, Any]:
    """
    Load environment-specific configuration.
    
    Args:
        environment: Environment name (development, staging, production)
                   If None, uses ENVIRONMENT env var or defaults to 'development'
    
    Returns:
        Dictionary containing environment-specific configuration
    """
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'development')
    
    # Base configuration
    base_config = {
        'environment': environment,
        'debug': environment == 'development',
        'log_level': 'DEBUG' if environment == 'development' else 'INFO',
        'log_format': 'colorful' if environment == 'development' else 'json',
        'enable_metrics': True,
    }
    
    # Environment-specific overrides
    env_configs = {
        'development': {
            'debug': True,
            'log_level': 'DEBUG',
            'log_format': 'colorful',
            'log_file': 'logs/development.log',
            'log_enable_async': False,  # Disable async for easier debugging
            'service_port': 8000,
            'metrics_port': 9090,
        },
        'staging': {
            'debug': False,
            'log_level': 'INFO',
            'log_format': 'json',
            'log_file': '/app/logs/staging.log',
            'log_enable_async': True,
            'service_port': 8000,
            'metrics_port': 9090,
        },
        'production': {
            'debug': False,
            'log_level': 'WARNING',
            'log_format': 'json',
            'log_file': '/var/log/prisma/application.log',
            'log_enable_async': True,
            'log_max_file_size': 100 * 1024 * 1024,  # 100MB
            'log_backup_count': 10,
            'service_port': 8000,
            'metrics_port': 9090,
            'enable_metrics': True,
        }
    }
    
    # Merge configurations
    config = base_config.copy()
    if environment in env_configs:
        config.update(env_configs[environment])
    
    return config


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
    
    Returns:
        Dictionary containing configuration
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def get_environment_vars() -> Dict[str, Any]:
    """
    Get environment variables relevant to Prisma Common SDK.
    
    Returns:
        Dictionary containing environment variables
    """
    env_vars = {}
    
    # Common environment variables
    common_vars = [
        'APP_NAME',
        'APP_VERSION', 
        'ENVIRONMENT',
        'DEBUG',
        'LOG_LEVEL',
        'LOG_FORMAT',
        'LOG_FILE',
        'SERVICE_NAME',
        'SERVICE_VERSION',
        'SERVICE_PORT',
        'DATABASE_URL',
        'REDIS_URL',
        'SECRET_KEY',
        'LOG_MAX_FILE_SIZE',
        'LOG_BACKUP_COUNT',
        'LOG_ENABLE_ASYNC',
        'LOG_ENABLE_STRUCTLOG',
        'ENABLE_METRICS',
        'METRICS_PORT',
    ]
    
    for var in common_vars:
        value = os.getenv(var)
        if value is not None:
            env_vars[var] = value
    
    return env_vars


def validate_environment() -> bool:
    """
    Validate that the current environment is properly configured.
    
    Returns:
        True if environment is valid, False otherwise
    """
    environment = os.getenv('ENVIRONMENT', 'development')
    
    # Check required environment variables based on environment
    required_vars = {
        'development': [],
        'staging': ['SERVICE_NAME'],
        'production': ['SERVICE_NAME', 'SECRET_KEY']
    }
    
    if environment in required_vars:
        missing_vars = []
        for var in required_vars[environment]:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Missing required environment variables for {environment}: {missing_vars}")
            return False
    
    return True


def setup_environment():
    """
    Setup the environment for Prisma Common SDK.
    This function should be called at application startup.
    """
    # Validate environment
    if not validate_environment():
        raise RuntimeError("Environment validation failed")
    
    # Set default environment variables if not set
    defaults = {
        'ENVIRONMENT': 'development',
        'LOG_LEVEL': 'INFO',
        'LOG_FORMAT': 'json',
        'DEBUG': 'false',
    }
    
    for key, default_value in defaults.items():
        if not os.getenv(key):
            os.environ[key] = default_value
    
    # Create log directories if needed
    log_file = os.getenv('LOG_FILE')
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
