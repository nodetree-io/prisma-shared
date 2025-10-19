"""
Search Operator for YOPO System

This module provides a search operator that is responsible for web search functionality.
The SearchOperator performs web searches to gather information from various online sources
and returns relevant search results based on the given query or criteria.

The operator can handle different types of search queries and retrieve information
from the web to support research and information gathering tasks.
"""
from typing import Dict, Any, Optional, List
import yaml

from src.core.operators.llm.llm_wrapped_agent import create_wrapped_agent
from src.core.operators.base_op import BaseOperator, OperatorResult
from src.tool.tool_manager import get_tools
from src.utils.logging import get_logger

logger = get_logger(name="SearchOperator")

class SearchOperator(BaseOperator):
    """
    A specialized search operator that leverages web search tools to gather information from online sources.
    
    This operator is designed specifically for web search functionality, using available search tools
    to retrieve relevant information based on user queries. It provides efficient access to web-based
    information and can handle various types of search requests including general queries, specific
    topic research, and fact-finding missions.
    
    Key Features:
    - Web search functionality using available search tools
    - Efficient information retrieval from online sources
    - Support for various search query types
    - Integration with search tools like Firecrawl
    - Structured search result processing
    """
    
    def __init__(self, 
                 prompt_path: Optional[str] = None,
                 **kwargs):
        """
        Initialize the Search Operator.
        
        Args:
            prompt_path: Optional path to YAML config file containing system prompt and description
            **kwargs: Additional parameters for LLM configuration
        """
        # Load system prompt from YAML if config_path is provided
        system_prompt = None
        description = "A specialized search operator for web search functionality"
        
        if prompt_path:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                system_prompt = config.get('system_prompt', None)
                description = config.get('description', description)

        name = "SearchOperator"
        super().__init__(name=name, description=description, system_prompt=system_prompt, **kwargs)

    def _build_workflow(self):
        """Build the search workflow with appropriate search tools."""
        # Get search-specific tools by default
        tools = get_tools(tool_base_names=["firecrawl_search"])
        
        return create_wrapped_agent(
            agent_type="react",
            llm_instance=self.llm_provider,
            tools=tools
        )

    async def arun(self, query: str, context: Optional[Dict[str, Any]] = None) -> OperatorResult:
        """
        Run the Search Operator with the given query.
        
        Args:
            query: Search query or task
            context: Additional context information for the search
        """
        # Build workflow with search tools
        result: Any = await self.worklfow.ainvoke(query=query, context=context)
        
        if isinstance(result, str):
            logger.info(f"{self.name} search completed")
            return OperatorResult(base_result=result)
        if isinstance(result, dict):
            final_message = result["messages"][-1].content
            logger.info(f"{self.name} search completed")
            return OperatorResult(base_result=final_message)
