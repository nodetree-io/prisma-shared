"""
Cohesion Operator for YOPO System

This module provides a cohesion operator that is responsible for selecting the optimal 
solution from multiple candidate solutions. The CohesionOperator evaluates and compares 
different solutions based on various criteria to determine the best one.

The operator analyzes multiple solutions and uses intelligent decision-making to choose 
the most suitable option based on quality, relevance, and effectiveness metrics.
"""

import json
import os
import asyncio
from typing import Dict, Any, Optional, List, TypedDict, Annotated
import yaml

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from .llm.llm_provider import llm_instance, LLMProvider
from .base_op import BaseOperator, OperatorResult
from ..utils.logging import get_logger

logger = get_logger(name="CohesionOperator")

class CohesionState(TypedDict):
    """State object for the Cohesion workflow"""
    # Input
    original_query: str
    solutions: List[str]
    context: Optional[Dict[str, Any]]

    # Analysis results
    selected_solution: Optional[Dict[str, Any]]
    error_msg: Optional[str]
    
    # Messages for LLM interaction
    messages: Annotated[List[BaseMessage], add_messages]


# Node Functions - Independent of the operator class
async def solution_evaluation_node(state: CohesionState, llm_provider: LLMProvider) -> CohesionState:
    """
    Node 1: Evaluate and compare multiple solutions to select the optimal one.
    """
    logger.info("🔄 Starting solution evaluation node...")
    
    original_query = state["original_query"]
    solutions = state["solutions"]
    context = state.get("context")
    messages = state.get("messages", [])

    logger.info(f"📊 Evaluating {len(solutions)} solution(s)")
    
    try:
        # Prepare the evaluation prompt
        solutions_text = ""
        for i, solution in enumerate(solutions, 1):
            solutions_text += f"\n--- Solution {i} ---\n"
            solutions_text += f"Content: {str(solution)}\n"
        
        evaluation_prompt = f"""
Original Query: {original_query}

Context: {json.dumps(context, indent=2) if context else "None"}

Solutions to Evaluate:
{solutions_text}

Provide your analysis and clearly indicate which solution is the best choice and why.
"""

        messages.append({
            "role": "user",
            "content": evaluation_prompt
        })
        
        logger.info("🚀 Sending evaluation request to LLM provider...")
        # Get LLM response
        response = llm_provider.generate(messages)
        logger.info(f"✅ Received evaluation response (length: {len(response)} chars)")
        
        state.update({
            "selected_solution": response,
            "messages": messages + [AIMessage(content=response)]
        })
        logger.info("✅ Solution evaluation node completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error in solution evaluation node: {str(e)}")
        error_response = f"Evaluation failed: {str(e)}"
        state.update({
            "error_msg": error_response,
            "selected_solution": None,
            "messages": messages + [HumanMessage(content=f"Error: {str(e)}")]
        })
    
    return state

class CohesionOperator(BaseOperator):
    """
    Cohesion Operator for YOPO System
    
    A specialized operator designed for selecting the optimal solution from multiple candidate solutions.
    The CohesionOperator evaluates and compares different solutions based on various criteria including
    relevance, quality, completeness, accuracy, and usefulness to determine the best one.
    
    The operator uses intelligent decision-making to analyze multiple solutions and choose the most
    suitable option based on the original query context and solution quality metrics.
    
    Key Features:
    - Multi-solution evaluation and comparison
    - Intelligent selection based on quality metrics
    - Context-aware decision making
    - Detailed analysis and reasoning for selection
    - Support for various solution formats and types
    
    Use Cases:
    - Selecting the best answer from multiple AI responses
    - Choosing optimal solutions from different approaches
    - Quality-based filtering of candidate results
    - Decision support for multi-option scenarios
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
        name = "CohesionOperator"
        super().__init__(
            name=name, 
            description=description, 
            system_prompt=system_prompt, 
            **kwargs
        )

    def _build_workflow(self):
        """Build the LangGraph workflow for solution evaluation and selection."""
        workflow = StateGraph(CohesionState)
        
        # Create wrapper function that passes the required parameters
        async def _evaluation_wrapper(state: CohesionState) -> CohesionState:
            return await solution_evaluation_node(state, self.llm_provider)
        
        # Add nodes
        workflow.add_node("solution_evaluator", _evaluation_wrapper)
        
        # Define the workflow edges
        workflow.add_edge(START, "solution_evaluator")
        workflow.add_edge("solution_evaluator", END)
        
        return workflow.compile()

    async def arun(self, query: str, solutions: List[str], context: Optional[Dict[str, Any]] = None) -> OperatorResult:
        """
        Run the cohesion workflow to select the optimal solution.
        
        Args:
            query: Original user query
            context: Additional context for evaluation
            solutions: List of candidate solutions to evaluate
        """
        try:
            if not solutions:
                logger.warning("⚠️ No solutions provided for evaluation")
                return OperatorResult(
                    base_result="No solutions provided for evaluation",
                    metadata={"error": "empty_solutions_list"}
                )
            
            logger.info(f"🎯 Starting cohesion evaluation for {len(solutions)} solutions")
            
            # Initialize state
            initial_state = CohesionState(
                original_query=query,
                solutions=solutions,
                context=context,
                evaluation_result="",
                selected_solution=None,
                error_msg=None,
                messages=[]
            )
            
            # Run the workflow
            final_state = await self.worklfow.ainvoke(initial_state)
            
            if final_state["error_msg"] is None:
                # Prepare result
                selected_solution = final_state["selected_solution"]
                
                # Extract the base result from selected solution
                if selected_solution:
                    base_result = str(selected_solution)
                else:
                    base_result = "No solution could be selected"
                
                logger.info(f"{self.name} Operator result: {base_result}")

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
                base_result=f"Solution selection failed: {str(e)}"
            )