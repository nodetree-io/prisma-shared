"""
Format Operator for YOPO System

Responsible for converting input string data into specified output types and parsing them.
This operator handles data type conversion, formatting, and parsing operations to ensure
data compatibility across different components of the system.
"""
import json
import os
import asyncio
from typing import Dict, Any, Optional, List, TypedDict, Annotated, Union
import yaml
import ast
import re

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from src.common.operators.llm.llm_provider import llm_instance, LLMProvider
from src.common.operators.base_op import BaseOperator, OperatorResult
from src.common.utils.logging import get_logger

logger = get_logger(name="FormatOperator")

class FormatState(TypedDict):
    """State object for the Format workflow"""
    # Input
    input_data: str
    target_type: str
    format_schema: Optional[str]

    # Analysis results
    formatted_result: Optional[Any]
    error_msg: Optional[str]
    
    # Messages for LLM interaction
    messages: Annotated[List[BaseMessage], add_messages]


# Node Functions - Independent of the operator class
async def format_node(state: FormatState, llm_provider: LLMProvider) -> FormatState:
    """
    Node 1: Format input string data into specified target type.
    """
    logger.info("🔄 Starting format node...")
    
    input_data = state["input_data"]
    target_type = state["target_type"]
    format_schema = state["format_schema"]
    messages = state.get("messages", [])

    formatted_result = None

    logger.info(f"📊 Formatting input data to type: {target_type}")
    try:
        # If direct conversion failed or target type is complex, use LLM with retry logic
        max_retries = 3
        retry_count = 0
        formatted_result = None
        previous_error = None
        previous_response = None
        
        while retry_count < max_retries and formatted_result is None:
            user_prompt = f"""
Input: {input_data}
Target Type: {target_type}
Format Schema demands: {format_schema}

Previous attempt failed with error: {previous_error}
Previous response was: {previous_response}

Please convert the input data to the specified target type. Make sure to return valid JSON format.
"""

            messages.append({
                "role": "user",
                "content": user_prompt
            })
            
            logger.info(f"🚀 Sending format request to LLM provider (attempt {retry_count + 1}/{max_retries})...")
            # Get LLM response
            response = llm_provider.generate(messages)
            logger.info(f"✅ Received format response (length: {len(response)} chars)")
            
            # Try to parse LLM response
            try:
                # Clean the response
                clean_response = response.strip()
                
                # Extract JSON content using regex pattern
                json_pattern = r'```json\s*(.*?)\s*```'
                json_match = re.search(json_pattern, clean_response, re.DOTALL)
                
                if json_match:
                    json_content = json_match.group(1).strip()
                    try:
                        formatted_result = json.loads(json_content)
                        logger.info(f"✅ Successfully parsed JSON on attempt {retry_count + 1}")
                        break
                    except json.JSONDecodeError as json_error:
                        logger.warning(f"⚠️ Failed to parse extracted JSON: {json_error}")
                        previous_error = f"JSON parsing error: {json_error}"
                        previous_response = json_content
                else:
                    # Fallback: try to parse the entire response as JSON
                    try:
                        formatted_result = json.loads(clean_response)
                        logger.info(f"✅ Successfully parsed full response as JSON on attempt {retry_count + 1}")
                        break
                    except json.JSONDecodeError as json_error:
                            logger.warning(f"⚠️ Failed to parse with literal_eval: {json_error}")
                            previous_error = f"All parsing methods failed. JSON error and literal_eval error: {json_error}"
                            previous_response = clean_response
                        
            except Exception as parse_error:
                logger.warning(f"⚠️ Could not parse LLM response: {parse_error}")
                previous_error = f"General parsing error: {parse_error}"
                previous_response = response
            
            retry_count += 1

        # If all retries failed, use the last response as fallback
        if formatted_result is None:
            logger.error(f"❌ All {max_retries} parsing attempts failed, using raw response")
            formatted_result = response
        
        if not isinstance(formatted_result, dict):
            formatted_result = {"data": formatted_result}

        state.update({
            "formatted_result": formatted_result,
            "messages": messages + [AIMessage(content=str(formatted_result))]
        })
        logger.info("✅ Format node completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error in format node: {str(e)}")
        error_response = f"Format conversion failed: {str(e)}"
        state.update({
            "error_msg": error_response,
            "formatted_result": None,
            "messages": messages + [HumanMessage(content=f"Error: {str(e)}")]
        })
    
    return state

class FormatOperator(BaseOperator):
    """
    Format Operator for YOPO System
    
    A specialized operator designed for converting input string data into specified output types
    and parsing them. This operator handles data type conversion, formatting, and parsing operations
    to ensure data compatibility across different components of the system.
    
    The operator can convert string inputs to various data types including integers, floats,
    booleans, lists, dictionaries, and other complex data structures. It uses intelligent
    parsing techniques and can leverage LLM assistance for complex conversions.
    
    Key Features:
    - String to various data type conversion
    - Intelligent parsing and extraction
    - JSON and Python literal evaluation
    - LLM-assisted complex format conversion
    - Robust error handling and fallback mechanisms
    - Support for custom target types
    
    Use Cases:
    - Converting API response strings to structured data
    - Parsing user input into appropriate data types
    - Formatting data for downstream processing
    - Type conversion for data pipeline compatibility
    """
    
    def __init__(self, 
                 prompt_path: Optional[str] = None,
                 **kwargs):
        # Initialize defaults
        system_prompt = None
        description = None
        
        # Load prompts from YAML if path provided
        if prompt_path and os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                system_prompt = config.get('system_prompt', None)
                description = config.get('description', None)
        
        # Initialize base operator
        name = "FormatOperator"
        super().__init__(
            name=name, 
            description=description, 
            system_prompt=system_prompt, 
            **kwargs
        )

    def _build_workflow(self):
        """Build the LangGraph workflow for data formatting."""
        workflow = StateGraph(FormatState)
        
        # Create wrapper function that passes the required parameters
        async def _format_wrapper(state: FormatState) -> FormatState:
            return await format_node(state, self.llm_provider)
        
        # Add nodes
        workflow.add_node("formatter", _format_wrapper)
        
        # Define the workflow edges
        workflow.add_edge(START, "formatter")
        workflow.add_edge("formatter", END)
        
        return workflow.compile()

    async def arun(self, input_data: str, target_type: str, format_schema: Optional[str] = None) -> OperatorResult:
        """
        Run the format workflow to convert input string to specified type.
        
        Args:
            input_data: String data to be converted
            target_type: Target data type (e.g., "int", "float", "list", "dict", etc.)
            format_schema: Optional schema description for dict target_type. 
                          Describes the expected structure, keys, and value types of the dictionary.
                          Example: "{'name': str, 'age': int, 'active': bool}" or 
                          "Dictionary with 'id' (integer), 'title' (string), 'tags' (list of strings)"
        """
        self.worklfow = self._build_workflow()
        try:
            if not input_data:
                logger.warning("⚠️ No input data provided for formatting")
                return OperatorResult(
                    base_result="No input data provided for formatting",
                    metadata={"error": "empty input_data"}
                )
            
            logger.info(f"🎯 Starting format conversion for input_data: {input_data}, target_type: {target_type}, format_schema: {format_schema}")
            
            # Initialize state
            initial_state = FormatState(
                input_data=input_data,
                target_type=target_type,
                format_schema=format_schema,
                formatted_result=None,
                error_msg=None,
                messages=[]
            )
            
            # Run the workflow
            final_state = await self.worklfow.ainvoke(initial_state)
            
            logger.info(f"Final formatted result: {final_state['formatted_result']}")
            if final_state["error_msg"] is None:
                # Prepare result
                formatted_result = final_state["formatted_result"]

                target_type_result = formatted_result.get("data", formatted_result) if target_type != 'dict' else formatted_result
                
                logger.info(f"{self.name} Operator result: {target_type_result}")

                result = OperatorResult(
                    base_result=target_type_result,
                    metadata={"original_type": type(input_data).__name__, "target_type": target_type}
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
                base_result=f"Data formatting failed: {str(e)}"
            )