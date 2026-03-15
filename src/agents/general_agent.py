"""General conversation agent."""

import time
from typing import Dict, Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from src.agents.state import AgentState
from src.config import settings
from src.utils.logger import get_logger, log_agent_entry, log_agent_exit
from src.utils.observability import tracer, state_inspector

logger = get_logger(__name__)


class GeneralAgent:
    """Handles general conversation queries."""

    def __init__(self):
        """Initialize general agent with Claude."""
        self.llm = ChatAnthropic(
            model=settings.claude_model,
            temperature=0.7,  # Higher temperature for conversational responses
            max_tokens=settings.max_tokens,
            anthropic_api_key=settings.anthropic_api_key,
        )
        logger.info("general_agent_initialized", model=settings.claude_model)

    def __call__(self, state: AgentState) -> AgentState:
        """Execute general agent logic.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with answer
        """
        start_time = time.time()
        trace_id = state["metadata"].get("trace_id", "unknown")

        # Observability: Log entry
        tracer.log_agent_entry(trace_id, "general_agent", state)
        state_inspector.snapshot(trace_id, "general_agent", state, "entry")
        log_agent_entry(logger, "general_agent", state)

        try:
            # Check for simple pattern-based responses first (no LLM needed)
            pattern_response = self._check_simple_patterns(state["user_query"])
            
            if pattern_response:
                answer = pattern_response
                logger.info(
                    "pattern_match_used",
                    trace_id=trace_id,
                    pattern_type="simple_response",
                )
            else:
                # Generate conversational response with LLM
                answer = self._generate_response(state["user_query"])
            
            # Update state
            state["final_answer"] = answer
            state["metadata"]["agent_path"].append("general_agent")
            state["metadata"]["source"] = "general"

            logger.info(
                "response_generated",
                trace_id=trace_id,
                answer_length=len(answer),
            )

        except Exception as e:
            logger.error(
                "general_agent_error",
                trace_id=trace_id,
                error=str(e),
                exc_info=True,
            )
            state["final_answer"] = (
                "I apologize, but I encountered an error. "
                "How else can I help you today?"
            )
            state["metadata"]["agent_path"].append("general_agent")
            state["metadata"]["source"] = "general"
            state["metadata"]["error"] = str(e)

        # Observability: Log exit
        duration = time.time() - start_time
        tracer.log_agent_exit(trace_id, "general_agent", state, tokens_used=500)
        state_inspector.snapshot(trace_id, "general_agent", state, "exit")
        log_agent_exit(logger, "general_agent", state, duration)

        return state

    def _check_simple_patterns(self, query: str) -> str:
        """Check for simple pattern-based responses to avoid LLM calls.
        
        Args:
            query: User query
            
        Returns:
            Pattern-based response or empty string if no match
        """
        query_lower = query.lower().strip()
        
        # Greetings
        if query_lower in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]:
            return "Hello! I'm here to help you with questions about Thoughtful AI's automation agents. How can I assist you today?"
        
        # Thank you
        if any(word in query_lower for word in ["thank", "thanks", "appreciate"]):
            return "You're welcome! Let me know if you have any other questions about Thoughtful AI's agents."
        
        # Personal information questions
        if any(phrase in query_lower for phrase in ["what is my name", "who am i", "do you know me", "my name"]):
            return "I don't have access to your personal information. I'm here to help answer questions about Thoughtful AI's automation agents like EVA, CAM, and PHIL. How can I assist you?"
        
        # How are you
        if query_lower in ["how are you", "how are you?", "how's it going", "how are you doing"]:
            return "I'm doing great, thank you for asking! I'm here to help you with questions about Thoughtful AI's automation agents. What would you like to know?"
        
        # Goodbye
        if query_lower in ["bye", "goodbye", "see you", "see ya", "later"]:
            return "Goodbye! Feel free to come back if you have questions about Thoughtful AI's agents."
        
        # No pattern match
        return ""

    def _generate_response(self, query: str) -> str:
        """Generate conversational response.
        
        Args:
            query: User query
            
        Returns:
            Generated response
        """
        prompt = f"""You are a friendly and helpful AI assistant for Thoughtful AI, a company that provides AI-powered automation agents for healthcare.

The user has asked a general question that isn't specifically about our products (EVA, CAM, PHIL).

User: {query}

Instructions:
- Provide a helpful, friendly response
- Be conversational and warm
- If appropriate, you can mention that you're here to help with questions about Thoughtful AI's automation agents
- Keep responses concise but informative
- Be professional but approachable

Response:"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()

        except Exception as e:
            logger.error("llm_generation_error", error=str(e), exc_info=True)
            return (
                "Hello! I'm here to help you with questions about Thoughtful AI's "
                "automation agents. How can I assist you today?"
            )


# Create singleton instance
general_agent = GeneralAgent()
