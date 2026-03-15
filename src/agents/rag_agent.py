"""RAG agent for product-related queries."""

import time
from typing import Dict, Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from src.agents.state import AgentState
from src.config import settings
from src.utils.logger import get_logger, log_agent_entry, log_agent_exit
from src.utils.observability import tracer, state_inspector

logger = get_logger(__name__)


class RAGAgent:
    """Answers product queries using retrieved context."""

    def __init__(self, vector_store_service):
        """Initialize RAG agent with Claude and vector store.
        
        Args:
            vector_store_service: Vector store service instance
        """
        self.vector_store = vector_store_service
        self.llm = ChatAnthropic(
            model=settings.claude_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            anthropic_api_key=settings.anthropic_api_key,
        )
        logger.info("rag_agent_initialized", model=settings.claude_model)

    def __call__(self, state: AgentState) -> AgentState:
        """Execute RAG agent logic.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with answer and retrieved docs
        """
        start_time = time.time()
        trace_id = state["metadata"].get("trace_id", "unknown")

        # Observability: Log entry
        tracer.log_agent_entry(trace_id, "rag_agent", state)
        state_inspector.snapshot(trace_id, "rag_agent", state, "entry")
        log_agent_entry(logger, "rag_agent", state)

        try:
            # Retrieve relevant documents with similarity scores
            search_start = time.time()
            results_with_scores = self.vector_store.similarity_search_with_score(
                state["user_query"],
                k=settings.top_k_results,
            )
            search_duration = time.time() - search_start

            state["metadata"]["vector_search_duration"] = search_duration

            if not results_with_scores:
                state["final_answer"] = (
                    "I don't have specific information about that in my knowledge base. "
                    "Could you rephrase your question or ask about EVA, CAM, or PHIL?"
                )
                state["retrieved_docs"] = []
                state["metadata"]["agent_path"].append("rag_agent")
                state["metadata"]["source"] = "rag"
                state["metadata"]["match_type"] = "no_match"
                return state

            # Get best match
            best_doc, best_score = results_with_scores[0]
            
            # Convert distance to similarity (ChromaDB uses L2 distance, lower is better)
            # For cosine similarity with normalized vectors: similarity ≈ 1 - (distance²/4)
            similarity = max(0, 1 - (best_score / 2))
            
            # Store all docs for display
            state["retrieved_docs"] = [doc for doc, score in results_with_scores]

            logger.info(
                "documents_retrieved",
                trace_id=trace_id,
                num_docs=len(results_with_scores),
                best_similarity=round(similarity, 3),
                search_duration=round(search_duration, 3),
            )

            # Decision: Exact match or LLM generation
            if similarity >= settings.similarity_threshold:
                # High similarity - return exact answer from dataset
                answer = self._extract_exact_answer(best_doc)
                match_type = "exact_match"
                tokens_used = 0  # No LLM call
                
                logger.info(
                    "exact_match_found",
                    trace_id=trace_id,
                    similarity=round(similarity, 3),
                    threshold=settings.similarity_threshold,
                )
            else:
                # Low similarity - use LLM to generate answer
                answer = self._generate_answer_with_llm(
                    state["user_query"],
                    [doc for doc, score in results_with_scores]
                )
                match_type = "llm_generated"
                tokens_used = 800  # Estimate
                
                logger.info(
                    "llm_generation_used",
                    trace_id=trace_id,
                    similarity=round(similarity, 3),
                    threshold=settings.similarity_threshold,
                )
            
            # Update state
            state["final_answer"] = answer
            state["metadata"]["agent_path"].append("rag_agent")
            state["metadata"]["source"] = "rag"
            state["metadata"]["match_type"] = match_type
            state["metadata"]["best_similarity"] = similarity

            logger.info(
                "answer_generated",
                trace_id=trace_id,
                match_type=match_type,
                answer_length=len(answer),
            )

        except Exception as e:
            logger.error(
                "rag_agent_error",
                trace_id=trace_id,
                error=str(e),
                exc_info=True,
            )
            state["final_answer"] = (
                "I apologize, but I encountered an error retrieving information. "
                "Please try again or rephrase your question."
            )
            state["metadata"]["agent_path"].append("rag_agent")
            state["metadata"]["source"] = "rag"
            state["metadata"]["error"] = str(e)

        # Observability: Log exit
        duration = time.time() - start_time
        tokens_used = state["metadata"].get("tokens_used", 0)
        tracer.log_agent_exit(trace_id, "rag_agent", state, tokens_used=tokens_used)
        state_inspector.snapshot(trace_id, "rag_agent", state, "exit")
        log_agent_exit(logger, "rag_agent", state, duration)

        return state

    def _extract_exact_answer(self, doc) -> str:
        """Extract exact answer from document metadata.
        
        Args:
            doc: Document with metadata containing the answer
            
        Returns:
            Exact answer from dataset
        """
        # The answer is stored in metadata
        if hasattr(doc, 'metadata') and 'answer' in doc.metadata:
            return doc.metadata['answer']
        
        # Fallback: parse from page_content
        content = doc.page_content
        if "Answer:" in content:
            return content.split("Answer:", 1)[1].strip()
        
        return content

    def _generate_answer_with_llm(self, query: str, docs: list) -> str:
        """Generate answer using LLM with retrieved context.
        
        This is only called when similarity is below threshold.
        
        Args:
            query: User query
            docs: Retrieved documents
            
        Returns:
            LLM-generated answer
        """
        if not docs:
            return (
                "I don't have specific information about that in my knowledge base. "
                "Could you rephrase your question or ask about EVA, CAM, or PHIL?"
            )

        # Construct context from documents
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"[Document {i}]\n{doc.page_content}\n")

        context = "\n".join(context_parts)

        prompt = f"""You are a helpful AI assistant for Thoughtful AI, a company that provides AI-powered automation agents for healthcare.

The user's question doesn't exactly match our predefined Q&A, but here's some related context that might help.

Context:
{context}

User Question: {query}

Instructions:
- Try to answer based on the context if it's somewhat relevant
- If the context is not relevant enough, politely say you don't have specific information about that
- Be helpful and suggest asking about EVA, CAM, or PHIL if appropriate
- Keep the answer concise

Answer:"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()

        except Exception as e:
            logger.error("llm_generation_error", error=str(e), exc_info=True)
            return (
                "I apologize, but I encountered an error generating a response. "
                "Please try again."
            )


# Note: RAG agent instance will be created in main.py after vector store is initialized
