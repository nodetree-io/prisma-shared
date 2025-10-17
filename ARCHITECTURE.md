# Prisma Shared Architecture

## Overview

The `prisma-shared` repository provides lightweight, shared components for the Prisma microservices platform. It focuses on common utilities and configuration management that are used across all microservices.

## Design Principles

### 1. **Lightweight and Focused**
- Only includes essential shared components
- No heavy infrastructure dependencies
- Fast installation and minimal footprint

### 2. **Separation of Concerns**
- **Configuration Management**: Environment settings and validation
- **Utilities**: Logging, helpers, and common functions
- **Infrastructure**: Handled by separate `prisma-infra` repository

### 3. **Microservice Independence**
- Each microservice can use shared components without tight coupling
- No shared business logic or domain-specific code
- Pure utility and configuration functions

## Package Structure

```
prisma_common/
├── config/           # Configuration management
│   ├── settings.py   # Pydantic settings classes
│   └── environments/ # Environment-specific configs
└── utils/            # Common utilities
    ├── logging.py    # Logging system
    └── helpers.py    # Utility functions
```

## Components

### Configuration Module (`prisma_common.config`)

**Purpose**: Centralized configuration management using Pydantic.

**Features**:
- Environment-based configuration loading
- Type validation and conversion
- Default value management
- Environment variable integration

**Usage**:
```python
from prisma_common.config import Settings, get_settings

# Load configuration
settings = get_settings()

# Access configuration values
db_url = settings.database_url
api_key = settings.openai_api_key
```

### Utilities Module (`prisma_common.utils`)

**Purpose**: Common utilities and helpers used across services.

**Features**:
- Structured logging with context
- Configuration loading helpers
- Common validation functions
- Error handling utilities

**Usage**:
```python
from prisma_common.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Use structured logging
logger.info("Processing request", extra={
    "user_id": "123",
    "action": "create_workflow"
})
```

## What's NOT Included

### Infrastructure Components
- **Database clients** → Handled by `prisma-infra`
- **Storage abstractions** → Handled by `prisma-infra`
- **AWS service clients** → Handled by `prisma-infra`
- **Message queue clients** → Handled by `prisma-infra`

### Business Logic
- **Domain models** → Each service manages its own
- **API schemas** → Each service defines its own
- **Business rules** → Service-specific implementations

### Heavy Dependencies
- **Database drivers** → Not included in shared package
- **Cloud SDKs** → Not included in shared package
- **Framework-specific code** → Service-specific implementations

## Benefits of This Approach

### 1. **Faster Development**
- Lightweight package with minimal dependencies
- Quick installation and updates
- No version conflicts with infrastructure components

### 2. **Better Separation**
- Infrastructure concerns isolated in `prisma-infra`
- Business logic stays in individual services
- Clear boundaries between shared and service-specific code

### 3. **Easier Maintenance**
- Smaller surface area for changes
- Less risk of breaking changes
- Clear ownership of components

### 4. **Flexible Deployment**
- Services can use different infrastructure configurations
- Infrastructure can evolve independently
- Services can be deployed to different environments

## Migration Strategy

When migrating from the old monolithic structure:

1. **Keep in prisma-shared**:
   - `src/utils/logging.py` → `prisma_common/utils/logging.py`
   - `src/config/settings.py` → `prisma_common/config/settings.py`
   - `src/config/environments/` → `prisma_common/config/environments/`

2. **Move to prisma-infra**:
   - `src/infrastructure/database/` → Infrastructure Terraform modules
   - `src/infrastructure/storage/` → Infrastructure Terraform modules
   - Database clients and connection management

3. **Keep in individual services**:
   - Business logic and domain models
   - Service-specific API schemas
   - Service-specific configurations

## Usage in Microservices

### Build Service
```python
from prisma_common.config import Settings
from prisma_common.utils.logging import get_logger

# Service-specific configuration extends base settings
class BuildServiceSettings(Settings):
    s3_bucket: str
    max_file_size: int = 10 * 1024 * 1024  # 10MB

settings = BuildServiceSettings()
logger = get_logger(__name__)
```

### Replay Service
```python
from prisma_common.config import Settings
from prisma_common.utils.logging import get_logger

class ReplayServiceSettings(Settings):
    execution_timeout: int = 300  # 5 minutes
    max_concurrent_executions: int = 10

settings = ReplayServiceSettings()
logger = get_logger(__name__)
```

### Experience Service
```python
from prisma_common.config import Settings
from prisma_common.utils.logging import get_logger

class ExperienceServiceSettings(Settings):
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    vector_dimensions: int = 1536

settings = ExperienceServiceSettings()
logger = get_logger(__name__)
```

This architecture ensures that `prisma-shared` remains focused, lightweight, and maintainable while providing essential shared functionality for the Prisma microservices platform.
