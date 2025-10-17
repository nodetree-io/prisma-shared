# Prisma Common

[![CI](https://github.com/prisma-platform/prisma-shared/actions/workflows/ci.yml/badge.svg)](https://github.com/prisma-platform/prisma-shared/actions/workflows/ci.yml)

Shared components for Prisma microservices architecture.

## Installation

```bash
# Local development
uv pip install -e .

# Install from private GitHub repository
pip install git+https://github.com/nodetree-io/prisma-shared.git

# Install from specific branch
pip install git+https://github.com/nodetree-io/prisma-shared.git@main

# For development
git clone https://github.com/nodetree-io/prisma-shared.git
cd prisma-shared
uv pip install -e .
```

> ⚠️ **Private Repository**: This is a private repository for internal use only. GitHub access required.

## Usage

```python
from prisma_common.utils.logging import get_logger
from prisma_common.config import Settings, get_settings

# Initialize logger
logger = get_logger(__name__)

# Load configuration
settings = get_settings()

# Use logger
logger.info("Application started")
logger.error("An error occurred", extra={"error_code": "E001"})
```

## Modules

- **config**: Pydantic configuration management and environment settings
- **utils**: Logging system and configuration loaders

## Development

```bash
# Install in development mode
uv pip install -e .

# Run tests
uv run python -m pytest tests/

# Build package
uv build
```
