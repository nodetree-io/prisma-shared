"""
Synthesis Operator for YOPO System

This module provides a synthesis operator that is responsible for summarizing and 
consolidating various types of information, then outputting a comprehensive summary.

The SynthesisOperator takes multiple information sources and synthesizes them into
a coherent, well-structured summary that captures the key insights and findings.
"""
import json
import os
import asyncio
from typing import Dict, Any, Optional, List, TypedDict, Annotated
import yaml

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from src.common.operators.llm.llm_provider import llm_instance, LLMProvider
from src.common.operators.base_op import BaseOperator, OperatorResult
from src.common.utils.logging import get_logger

logger = get_logger(name="SynthesisOperator")

class SynthesisState(TypedDict):
    """State object for the Synthesis workflow"""
    # Input
    infos: List[str]
    context: Optional[Dict[str, Any]]

    # Analysis results
    synthesized_result: Optional[str]
    error_msg: Optional[str]
    
    # Messages for LLM interaction
    messages: Annotated[List[BaseMessage], add_messages]


# Node Functions - Independent of the operator class
async def synthesis_node(state: SynthesisState, llm_provider: LLMProvider) -> SynthesisState:
    """
    Node 1: Synthesize multiple infos into a comprehensive summary.
    """
    logger.info("🔄 Starting synthesis node...")
    
    infos = state["infos"]
    context = state.get("context")
    messages = state.get("messages", [])

    logger.info(f"📊 Synthesizing {len(infos)} input result(s)")
    
    try:
        # Prepare the synthesis prompt
        results_text = ""
        for i, result in enumerate(infos, 1):
            results_text += f"\n--- Input Result {i} ---\n"
            results_text += f"Content: {str(result)}\n"
        
        user_prompt = f"""
Context: {json.dumps(context, indent=2) if context else "None"}

infos to Synthesize:
{results_text}

Create a unified synthesis that combines the best elements from all infos.
"""

        messages.append({
            "role": "user",
            "content": user_prompt
        })
        
        logger.info("🚀 Sending synthesis request to LLM provider...")
        # Get LLM response
        response = llm_provider.generate(messages)
        logger.info(f"✅ Received synthesis response (length: {len(response)} chars)")
        
        state.update({
            "synthesized_result": response,
            "messages": messages + [AIMessage(content=response)]
        })
        logger.info("✅ Synthesis node completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error in synthesis node: {str(e)}")
        error_response = f"Synthesis failed: {str(e)}"
        state.update({
            "error_msg": error_response,
            "synthesized_result": None,
            "messages": messages + [HumanMessage(content=f"Error: {str(e)}")]
        })
    
    return state

class SynthesisOperator(BaseOperator):
    """
    Synthesis Operator for YOPO System
    
    A specialized operator designed for synthesizing and consolidating multiple infos
    into a comprehensive, coherent summary. The SynthesisOperator takes various information
    sources and combines them into a unified output that captures key insights while
    eliminating redundancy and maintaining logical structure.
    
    The operator uses intelligent consolidation to merge different results and create
    a well-organized final summary that addresses the original query comprehensively.
    
    Key Features:
    - Multi-result synthesis and consolidation
    - Intelligent information merging and deduplication
    - Context-aware summarization
    - Structured and coherent output generation
    - Support for various input formats and types
    
    Use Cases:
    - Consolidating multiple research findings
    - Combining results from different analysis approaches
    - Creating comprehensive summaries from various sources
    - Merging outputs from multiple processing steps
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
        name = "SynthesisOperator"
        super().__init__(
            name=name, 
            description=description, 
            system_prompt=system_prompt, 
            **kwargs
        )

    def _build_workflow(self):
        """Build the LangGraph workflow for result synthesis."""
        workflow = StateGraph(SynthesisState)
        
        # Create wrapper function that passes the required parameters
        async def _synthesis_wrapper(state: SynthesisState) -> SynthesisState:
            return await synthesis_node(state, self.llm_provider)
        
        # Add nodes
        workflow.add_node("synthesizer", _synthesis_wrapper)
        
        # Define the workflow edges
        workflow.add_edge(START, "synthesizer")
        workflow.add_edge("synthesizer", END)
        
        return workflow.compile()

    async def arun(self, infos: List[str], context: Optional[Dict[str, Any]] = None) -> OperatorResult:
        """
        Run the synthesis workflow to consolidate multiple infos.
        
        Args:
            infos: List of infos to synthesize
            context: Additional context for synthesis
        """
        self.worklfow = self._build_workflow()
        try:
            if not infos:
                logger.warning("⚠️ No infos provided for synthesis")
                return OperatorResult(
                    base_result="No infos provided for synthesis",
                    metadata={"error": "empty infos"}
                )
            
            logger.info(f"🎯 Starting synthesis for infos: {infos}")
            
            # Initialize state
            initial_state = SynthesisState(
                infos=infos,
                context=context,
                synthesized_result=None,
                error_msg=None,
                messages=[]
            )
            
            # Run the workflow
            final_state = await self.worklfow.ainvoke(initial_state)
            
            if final_state["error_msg"] is None:
                # Prepare result
                synthesized_result = final_state["synthesized_result"]
                
                # Extract the base result from synthesized result
                if synthesized_result:
                    base_result = str(synthesized_result)
                else:
                    base_result = "No synthesis could be generated"
                
                logger.info(f"{self.name} Operator result: {base_result}...")

                result = OperatorResult(
                    base_result=base_result
                )
            else:
                result = OperatorResult(
                    base_result=final_state["error_msg"]
                )
            
            return result
            
        except Exception as e:
            logger.error(f"{self.name} Operator failed: {str(e)}")
            return OperatorResult(
                base_result=f"Result synthesis failed: {str(e)}"
            )