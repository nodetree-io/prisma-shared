"""
Common SDK - Shared components for Prisma microservices.

This package provides a comprehensive SDK for the Prisma platform,
including operators, tools, utilities, and configuration management.

Usage Examples:
    # Configuration and logging
    from common import get_prisma_logger
    from common.config import Settings, get_settings
    
    # Operators
    from common.operators.research import DeepResearchOperator
    from common.operators.analysis import DataAnalysisOperator
    
    # Tools
    from common.tools.gmail import GmailTool
    from common.tools.calendar import CalendarTool
    
    # Utilities
    from common.utils.logging import get_prisma_logger
    from common.utils.validation import validate_email
"""

__version__ = "0.1.0"
__author__ = "Prisma Team"
__description__ = "Shared SDK for Prisma microservices platform"

# Core imports
try:
    from .config import Settings, get_settings
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

from .utils.logging import get_prisma_logger

# Make key components available at package level
__all__ = [
    # Version info
    "__version__",
    "__author__", 
    "__description__",
    
    # Core components
    "get_prisma_logger",
    
    # Submodules (for deep imports)
    "operators",
    "mcp", 
    "tools",
    "utils",
    "config",
]

# Import submodules to make them available
from . import utils

# Conditionally import other modules
try:
    from . import operators
    OPERATORS_AVAILABLE = True
except ImportError:
    OPERATORS_AVAILABLE = False

try:
    from . import mcp
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

try:
    from . import tools
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False

try:
    from . import config
    CONFIG_AVAILABLE = True
    # Add config exports to __all__ if available
    if CONFIG_AVAILABLE:
        __all__.extend(["Settings", "get_settings"])
except ImportError:
    CONFIG_AVAILABLE = False