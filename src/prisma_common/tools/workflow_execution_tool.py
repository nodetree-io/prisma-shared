"""
Workflow Execution Tool for YOPO System

This module provides a specialized tool for executing workflow code with full access
to the YOPO system's operators and modules. Unlike the generic code_act_tool, this
tool runs in the current Python environment and can access all YOPO system components.
"""

import asyncio
import sys
import traceback
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from src.tool.base_tool import YOPOBaseTool, BaseToolConfig
from src.utils.logging import get_logger

# Add project root to path for imports
_current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_current_dir))

# Import YOPO system components
from src.core.operators.operator_manager import get_operator_instance
from src.tool.tool_manager import get_tools

logger = get_logger(__name__)


class WorkflowExecutionResult(BaseModel):
    """
    Result model for workflow execution operations.
    
    This model represents the result of executing workflow code.
    """
    output: Optional[str] = Field(default=None, description="The output from executing the workflow")
    error: Optional[str] = Field(default=None, description="Any error that occurred during execution")
    success: bool = Field(default=False, description="Whether the execution was successful")


class WorkflowExecutionTool(YOPOBaseTool):
    """
    Workflow execution tool implementation for running workflow code with full YOPO system access.
    
    This tool allows execution of workflow code in the current Python environment,
    providing access to all YOPO operators, tools, and system components.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the workflow execution tool.
        
        Args:
            **kwargs: Additional configuration parameters
        """
        config = BaseToolConfig(
            name="workflow_execution",
            description="Tool for executing workflow code with full access to YOPO system components",
            **kwargs
        )
        super().__init__(config)
    
    def get_langchain_tools(self) -> List[BaseTool]:
        """Create LangChain tools for workflow execution functionality."""
        
        @tool
        def execute_workflow_code(workflow_code: str, user_query: str):
            """
            Execute workflow code with full access to YOPO system components.
            
            This tool allows execution of workflow code in the current Python environment,
            providing access to all YOPO operators, tools, and system components. Unlike
            the generic code_act_tool, this tool can access the real YOPO system.
            
            Args:
                workflow_code: The workflow Python code to execute
                user_query: The user query to pass to the workflow
                
            Returns:
                WorkflowExecutionResult: Result containing output or error information
            """
            try:
                logger.info(f"Executing workflow code for query: {user_query}")
                
                # Create a namespace for the workflow execution
                workflow_namespace = {
                    '__builtins__': __builtins__,
                    'get_operator_instance': get_operator_instance,
                    'get_tools': get_tools,
                    'asyncio': asyncio,
                    'sys': sys,
                    'Path': Path,
                    'logger': logger,
                }
                # Execute the workflow code in the namespace
                exec(workflow_code, workflow_namespace)
                
                # Find and instantiate the Workflow class
                if 'Workflow' not in workflow_namespace:
                    raise ValueError("Workflow class not found in the provided code")
                
                WorkflowClass = workflow_namespace['Workflow']
                workflow_instance = WorkflowClass()
                
                # Check if the workflow has an async __call__ method
                if asyncio.iscoroutinefunction(workflow_instance.__call__):
                    # Execute async workflow
                    result = asyncio.run(workflow_instance(user_query))
                else:
                    # Execute sync workflow
                    result = workflow_instance(user_query)
                
                logger.info("Workflow execution completed successfully")
                
                return WorkflowExecutionResult(
                    output=str(result),
                    error=None,
                    success=True
                )
                
            except Exception as e:
                error_msg = f"Workflow execution failed: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
                
                return WorkflowExecutionResult(
                    output=None,
                    error=error_msg,
                    success=False
                )
        
        return [execute_workflow_code]
