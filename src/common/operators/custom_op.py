"""
General Agent for YOPO System

A general-purpose agent that can handle various types of queries and tasks.
This agent provides flexible functionality for common use cases.
"""

from typing import Dict, Any, Optional, List
import yaml

from .llm.llm_wrapped_agent import create_wrapped_agent
from .base_op import BaseOperator, OperatorResult
from ..utils.logging import get_logger

logger = get_logger(name="CustomOperator")

class CustomOperator(BaseOperator):
    """
    A general-purpose AI operator that leverages available MCP tools to efficiently complete a wide variety of tasks.
    
    This operator prioritizes practical action over theoretical analysis, using a tool-first approach to deliver
    quick and effective solutions across different domains including research, file processing, data analysis,
    and general problem-solving. It acts as a versatile interface to the MCP (Model Context Protocol) ecosystem,
    providing users with access to specialized tools and capabilities through natural language interaction.
    
    Key Features:
    - Tool-first problem solving approach
    - Efficient task completion using available MCP tools
    - Flexible handling of diverse query types
    - Direct and results-focused communication
    - Robust error handling and alternative solution finding
    """
    
    def __init__(self, 
                 prompt_path: str,
                 **kwargs):
        """
        Initialize the MCP Operator.
        
        Args:
            prompt_path: Path to YAML config file containing system prompt and description
            tools: List of tools/MCPs available to the operator
            **kwargs: Additional parameters for LLM configuration
        """
        # Load system prompt from YAML if config_path is provided
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            description = config.get('description', None)

        name = "CustomOperator"
        super().__init__(name=name, description=description, **kwargs)

    def _build_workflow(self, tools: Optional[List] = None, mcp_servers: Optional[List] = None):
        if not mcp_servers:
            return create_wrapped_agent(
                agent_type="react",
                llm_instance=self.llm_provider,
                tools=tools if tools else []
            )
        if mcp_servers:
            return create_wrapped_agent(
                agent_type="mcp",
                llm_instance=self.llm_provider,
                mcps=mcp_servers
            )

    async def arun(self, query: str, context: Optional[Dict[str, Any]] = None, tools: Optional[List] = None, mcp_servers: Optional[List] = None) -> OperatorResult:
        """
        Run the Custom Operator with the given query.
        
        Args:
            query: User query or task
            context: Additional context information
            tools: List of tools available to the operator
            mcp_servers: List of MCP servers available to the operator
        """
        # Default: ReAct Agent
        logger.info(f"🎯 Starting custom operator for query: {query}, context: {context}, tools: {tools}, mcp_servers: {mcp_servers}")
        workflow = self._build_workflow(tools=tools, mcp_servers=mcp_servers)
        result: Any = await workflow.ainvoke(query=query, context=context)
        
        if isinstance(result, str):
            logger.info(f"{self.name} Operator result: {result}")
            return OperatorResult(base_result=result)
        if isinstance(result, dict):
            final_message = result["messages"][-1].content
            logger.info(f"{self.name} Operator result: {final_message}")
            return OperatorResult(base_result=final_message)


        
