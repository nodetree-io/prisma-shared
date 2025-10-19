"""
Settings configuration for Prisma Common SDK.
Provides Pydantic-based configuration management.
"""

import os
from typing import Optional, Dict, Any, List
from pydantic import BaseSettings, Field, validator
from pydantic_settings import BaseSettings as PydanticBaseSettings


class Settings(PydanticBaseSettings):
    """Main settings class for Prisma Common SDK."""
    
    # Application settings
    app_name: str = Field(default="Prisma Common SDK", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format (json/colorful)")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    log_max_file_size: int = Field(default=100 * 1024 * 1024, description="Max log file size in bytes")
    log_backup_count: int = Field(default=5, description="Number of backup log files")
    log_enable_async: bool = Field(default=True, description="Enable async logging")
    log_enable_structlog: bool = Field(default=True, description="Enable structlog")
    
    # Service settings
    service_name: Optional[str] = Field(default=None, description="Service name")
    service_version: Optional[str] = Field(default=None, description="Service version")
    service_port: int = Field(default=8000, description="Service port")
    
    # Database settings (if needed)
    database_url: Optional[str] = Field(default=None, description="Database URL")
    
    # External service settings
    redis_url: Optional[str] = Field(default=None, description="Redis URL")
    
    # Monitoring settings
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Metrics port")
    
    # Security settings
    secret_key: Optional[str] = Field(default=None, description="Secret key for encryption")
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed_envs = ['development', 'staging', 'production']
        if v not in allowed_envs:
            raise ValueError(f'Environment must be one of: {allowed_envs}')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of: {allowed_levels}')
        return v.upper()
    
    @validator('log_format')
    def validate_log_format(cls, v):
        """Validate log format."""
        allowed_formats = ['json', 'colorful']
        if v not in allowed_formats:
            raise ValueError(f'Log format must be one of: {allowed_formats}')
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Environment variable mapping
        fields = {
            'app_name': {'env': 'APP_NAME'},
            'app_version': {'env': 'APP_VERSION'},
            'environment': {'env': 'ENVIRONMENT'},
            'debug': {'env': 'DEBUG'},
            'log_level': {'env': 'LOG_LEVEL'},
            'log_format': {'env': 'LOG_FORMAT'},
            'log_file': {'env': 'LOG_FILE'},
            'log_max_file_size': {'env': 'LOG_MAX_FILE_SIZE'},
            'log_backup_count': {'env': 'LOG_BACKUP_COUNT'},
            'log_enable_async': {'env': 'LOG_ENABLE_ASYNC'},
            'log_enable_structlog': {'env': 'LOG_ENABLE_STRUCTLOG'},
            'service_name': {'env': 'SERVICE_NAME'},
            'service_version': {'env': 'SERVICE_VERSION'},
            'service_port': {'env': 'SERVICE_PORT'},
            'database_url': {'env': 'DATABASE_URL'},
            'redis_url': {'env': 'REDIS_URL'},
            'enable_metrics': {'env': 'ENABLE_METRICS'},
            'metrics_port': {'env': 'METRICS_PORT'},
            'secret_key': {'env': 'SECRET_KEY'},
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def update_settings(**kwargs) -> Settings:
    """Update settings with new values."""
    global _settings
    if _settings is None:
        _settings = Settings()
    
    # Update settings with new values
    for key, value in kwargs.items():
        if hasattr(_settings, key):
            setattr(_settings, key, value)
    
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings
