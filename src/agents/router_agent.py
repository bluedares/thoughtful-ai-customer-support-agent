"""Router agent for query classification."""

import time
from typing import Dict, Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from src.agents.state import AgentState
from src.config import settings
from src.utils.logger import get_logger, log_agent_entry, log_agent_exit
from src.utils.observability import tracer, state_inspector

logger = get_logger(__name__)


class RouterAgent:
    """Routes queries to appropriate agent based on classification."""

    def __init__(self):
        """Initialize router agent with Claude."""
        self.llm = ChatAnthropic(
            model=settings.claude_model,
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=50,  # Short response needed
            anthropic_api_key=settings.anthropic_api_key,
        )
        logger.info("router_agent_initialized", model=settings.claude_model)

    def __call__(self, state: AgentState) -> AgentState:
        """Execute router agent logic.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with route_decision
        """
        start_time = time.time()
        trace_id = state["metadata"].get("trace_id", "unknown")

        # Observability: Log entry
        tracer.log_agent_entry(trace_id, "router_agent", state)
        state_inspector.snapshot(trace_id, "router_agent", state, "entry")
        log_agent_entry(logger, "router_agent", state)

        try:
            # Classify query
            route_decision = self._classify_query(state["user_query"])
            
            # Update state
            state["route_decision"] = route_decision
            state["metadata"]["agent_path"].append("router_agent")

            logger.info(
                "query_classified",
                trace_id=trace_id,
                query=state["user_query"][:100],
                route=route_decision,
            )

        except Exception as e:
            logger.error(
                "router_agent_error",
                trace_id=trace_id,
                error=str(e),
                exc_info=True,
            )
            # Default to general on error
            state["route_decision"] = "general"
            state["metadata"]["agent_path"].append("router_agent")

        # Observability: Log exit
        duration = time.time() - start_time
        tracer.log_agent_exit(trace_id, "router_agent", state, tokens_used=50)
        state_inspector.snapshot(trace_id, "router_agent", state, "exit")
        log_agent_exit(logger, "router_agent", state, duration)

        return state

    def _classify_query(self, query: str) -> str:
        """Classify query as 'rag' or 'general'.
        
        Args:
            query: User query
            
        Returns:
            Classification: 'rag' or 'general'
        """
        classification_prompt = f"""You are a query classifier for Thoughtful AI support.

Classify if this query is about Thoughtful AI's products (EVA, CAM, PHIL, or general company info) or a general conversation.

Products:
- EVA: Eligibility Verification Agent
- CAM: Claims Processing Agent  
- PHIL: Payment Posting Agent

Query: "{query}"

Respond with ONLY one word: "rag" (if about products) or "general" (if general conversation).

Examples:
- "What is EVA?" -> rag
- "How does CAM work?" -> rag
- "Tell me about PHIL" -> rag
- "What are the benefits?" -> rag
- "Hello" -> general
- "How are you?" -> general
- "What's the weather?" -> general

Classification:"""

        try:
            response = self.llm.invoke([HumanMessage(content=classification_prompt)])
            decision = response.content.strip().lower()

            # Validate response
            if decision not in ["rag", "general"]:
                logger.warning(
                    "invalid_classification",
                    decision=decision,
                    query=query[:100],
                )
                # Default to rag if uncertain (better to retrieve than miss)
                return "rag"

            return decision

        except Exception as e:
            logger.error("classification_error", error=str(e), exc_info=True)
            return "general"  # Safe default


# Create singleton instance
router_agent = RouterAgent()
