"""Structured logging configuration using structlog."""

import logging
import sys
from typing import Any, Dict

import structlog
from src.config import settings


def setup_logging() -> None:
    """Configure structured logging with structlog."""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer() if settings.environment == "production"
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """Bind context variables to all subsequent log messages.
    
    Args:
        **kwargs: Context key-value pairs
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind_context(*keys: str) -> None:
    """Unbind context variables.
    
    Args:
        *keys: Context keys to unbind
    """
    structlog.contextvars.unbind_contextvars(*keys)


def log_agent_entry(logger: structlog.BoundLogger, agent_name: str, state: Dict[str, Any]) -> None:
    """Log agent entry with state.
    
    Args:
        logger: Structlog logger instance
        agent_name: Name of the agent
        state: Current agent state
    """
    logger.info(
        "agent_entry",
        agent=agent_name,
        user_query=state.get("user_query", ""),
        route_decision=state.get("route_decision"),
    )


def log_agent_exit(
    logger: structlog.BoundLogger,
    agent_name: str,
    state: Dict[str, Any],
    duration: float,
) -> None:
    """Log agent exit with state and duration.
    
    Args:
        logger: Structlog logger instance
        agent_name: Name of the agent
        state: Current agent state
        duration: Execution duration in seconds
    """
    logger.info(
        "agent_exit",
        agent=agent_name,
        duration_seconds=round(duration, 3),
        has_answer=bool(state.get("final_answer")),
        retrieved_docs_count=len(state.get("retrieved_docs", [])),
    )
