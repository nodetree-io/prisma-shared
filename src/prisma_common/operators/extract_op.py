"""
Extract Operator for YOPO System

This module provides an extract operator that is responsible for extracting key parts 
from information sources. The ExtractOperator analyzes input data and identifies the 
most relevant and important sections, filtering out noise and focusing on essential content.

The operator can handle various types of information and extract specific elements 
based on the given criteria or context.
"""

import json
import os
import asyncio
from typing import Dict, Any, Optional, List, TypedDict, Annotated
import yaml

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from src.core.operators.llm.llm_provider import llm_instance, LLMProvider
from src.core.operators.base_op import BaseOperator, OperatorResult
from src.utils.logging import get_logger

logger = get_logger(name="ExtractOperator")

class ExtractState(TypedDict):
    """State object for the Extract workflow"""
    # Input
    content: str
    extract_object: str
    context: Optional[Dict[str, Any]]

    # Analysis results
    extracted_result: Optional[str]
    error_msg: Optional[str]
    
    # Messages for LLM interaction
    messages: Annotated[List[BaseMessage], add_messages]


# Node Functions - Independent of the operator class
async def content_extraction_node(state: ExtractState, llm_provider: LLMProvider) -> ExtractState:
    """
    Node 1: Extract relevant information from content based on the query.
    """
    logger.info("🔄 Starting content extraction node...")
    
    content = state["content"]
    extract_object = state["extract_object"]
    context = state.get("context")
    messages = state.get("messages", [])

    logger.info(f"📊 Extracting relevant information from content (length: {len(content)} chars)")
    
    try:
        # Prepare the extraction prompt
        user_prompt = f"""
Context: {json.dumps(context, indent=2) if context else "None"}

Content to Extract From:
{content}

Extract Object: {extract_object}

Provide a concise extraction that captures the essential information related to the query.
"""

        messages.append({
            "role": "user",
            "content": user_prompt
        })
        
        logger.info("🚀 Sending extraction request to LLM provider...")
        # Get LLM response
        response = llm_provider.generate(messages)
        logger.info(f"✅ Received extraction response (length: {len(response)} chars)")
        
        state.update({
            "extracted_result": response,
            "messages": messages + [AIMessage(content=response)]
        })
        logger.info("✅ Content extraction node completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error in content extraction node: {str(e)}")
        error_response = f"Extraction failed: {str(e)}"
        state.update({
            "error_msg": error_response,
            "extracted_result": None,
            "messages": messages + [HumanMessage(content=f"Error: {str(e)}")]
        })
    
    return state

class ExtractOperator(BaseOperator):
    """
    Extract Operator for YOPO System
    
    A specialized operator designed for extracting relevant information from input content
    based on a given query. The ExtractOperator analyzes the provided content and identifies
    the most pertinent sections that directly relate to the user's query.
    
    The operator uses intelligent filtering to remove noise and focus on essential content
    that answers the user's question or addresses their specific needs.
    
    Key Features:
    - Query-focused content extraction
    - Intelligent filtering of relevant information
    - Context-aware analysis
    - Noise reduction and content optimization
    - Support for various content formats
    
    Use Cases:
    - Extracting key information from long documents
    - Filtering relevant data from large datasets
    - Summarizing content based on specific queries
    - Content preprocessing for further analysis
    """
    
    def __init__(self, 
                 prompt_path: Optional[str] = None,
                 **kwargs):
        # Load prompts from YAML if path provided
        if prompt_path and os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                system_prompt = config.get('system_prompt', None)
                description = config.get('description', None)
        
        # Initialize base operator
        name = "ExtractOperator"
        super().__init__(
            name=name, 
            description=description, 
            system_prompt=system_prompt, 
            **kwargs
        )

    def _build_workflow(self):
        """Build the LangGraph workflow for content extraction."""
        workflow = StateGraph(ExtractState)
        
        # Create wrapper function that passes the required parameters
        async def _extraction_wrapper(state: ExtractState) -> ExtractState:
            return await content_extraction_node(state, self.llm_provider)
        
        # Add nodes
        workflow.add_node("content_extractor", _extraction_wrapper)
        
        # Define the workflow edges
        workflow.add_edge(START, "content_extractor")
        workflow.add_edge("content_extractor", END)
        
        return workflow.compile()

    async def arun(self, content: str, extract_object: str , context: Optional[Dict[str, Any]] = None) -> OperatorResult:
        """
        Run the extraction workflow to extract relevant information from content.
        
        Args:
            content: Input content to extract information from
            extract_object: The specific object or information type to extract from the content
            context: Additional context for extraction
        """
        self.worklfow = self._build_workflow()
        try:
            if not content:
                logger.warning("⚠️ No content provided for extraction")
                return OperatorResult(
                    base_result="No content provided for extraction",
                    metadata={"error": "empty_content"}
                )
            
            logger.info(f"🎯 Starting content extraction for content: {content}\n and extract_object: {extract_object}")
            
            # Initialize state
            initial_state = ExtractState(
                content=content,
                extract_object=extract_object,
                context=context,
                extracted_result=None,
                error_msg=None,
                messages=[]
            )
            
            # Run the workflow
            final_state = await self.worklfow.ainvoke(initial_state)
            
            if final_state["error_msg"] is None:
                # Prepare result
                extracted_result = final_state["extracted_result"]
                
                # Extract the base result
                if extracted_result:
                    base_result = str(extracted_result)
                else:
                    base_result = "No relevant information could be extracted"
                
                logger.info(f"{self.name} Operator result: {base_result}...")

                result = OperatorResult(
                    base_result=base_result
                )
            else:
                logger.error(f"{self.name} Operator failed: {final_state['error_msg']}")
                result = OperatorResult(
                    base_result=final_state["error_msg"]
                )
            
            return result
            
        except Exception as e:
            logger.error(f"{self.name} Operator failed: {str(e)}")
            return OperatorResult(
                base_result=f"Content extraction failed: {str(e)}"
            )