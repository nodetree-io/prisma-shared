"""
Simple Test Operator - No external dependencies
Used for testing package installation
"""

from src.common.operators.base_op import BaseOperator, OperatorResult
from typing import Optional, Dict, Any


class SimpleTestOperator(BaseOperator):
    """
    A minimal test operator with no external dependencies.
    Used to verify package installation and operator discovery.
    """
    
    def __init__(self, prompt_path: Optional[str] = None, **kwargs):
        """Initialize the test operator."""
        super().__init__(
            name="SimpleTestOperator",
            description="A simple test operator with no dependencies",
            system_prompt="You are a simple test operator",
            **kwargs
        )
    
    def _build_workflow(self):
        """Build workflow - not needed for this simple test operator."""
        return None
    
    async def arun(self, message: str = "test") -> OperatorResult:
        """
        Run a simple test operation.
        
        Args:
            message: Test message to echo
            
        Returns:
            OperatorResult with the echoed message
        """
        return OperatorResult(
            base_result=f"Test operator executed successfully: {message}"
        )

