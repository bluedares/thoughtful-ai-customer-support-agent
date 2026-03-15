"""Observability infrastructure for agent tracing and metrics."""

import time
import uuid
from typing import Any, Dict, List, Optional
from collections import defaultdict
from datetime import datetime

from prometheus_client import Counter, Histogram, Gauge
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Prometheus Metrics
agent_invocations = Counter(
    "agent_invocations_total",
    "Total number of agent invocations",
    ["agent_name"],
)

agent_duration = Histogram(
    "agent_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_name"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

token_usage = Counter(
    "token_usage_total",
    "Total token usage",
    ["agent_name", "model"],
)

routing_decisions = Counter(
    "routing_decisions_total",
    "Routing decisions made by router agent",
    ["route"],
)

vector_search_duration = Histogram(
    "vector_search_duration_seconds",
    "Vector search duration in seconds",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0],
)

active_traces = Gauge(
    "active_traces",
    "Number of active traces",
)


class AgentTracer:
    """Tracks agent execution flow and state transitions."""

    def __init__(self):
        """Initialize the tracer with empty traces."""
        self.traces: Dict[str, Dict[str, Any]] = {}
        self._lock = None  # For thread safety in production

    def start_trace(self, trace_id: Optional[str] = None) -> str:
        """Start a new trace.
        
        Args:
            trace_id: Optional trace ID, generates UUID if not provided
            
        Returns:
            Trace ID
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        self.traces[trace_id] = {
            "trace_id": trace_id,
            "start_time": time.time(),
            "timestamp": datetime.utcnow().isoformat(),
            "agents": [],
            "state_snapshots": [],
            "metrics": {
                "total_duration": 0,
                "agent_durations": {},
                "token_usage": {},
            },
            "user_query": "",
            "final_answer": "",
            "source": "",
        }

        active_traces.inc()
        logger.info("trace_started", trace_id=trace_id)
        return trace_id

    def log_agent_entry(
        self,
        trace_id: str,
        agent_name: str,
        state: Dict[str, Any],
    ) -> None:
        """Log agent entry with input state.
        
        Args:
            trace_id: Trace identifier
            agent_name: Name of the agent
            state: Current agent state
        """
        if trace_id not in self.traces:
            logger.warning("trace_not_found", trace_id=trace_id, agent=agent_name)
            return

        agent_invocations.labels(agent_name=agent_name).inc()

        agent_info = {
            "name": agent_name,
            "entry_time": time.time(),
            "input_state": self._sanitize_state(state),
        }

        self.traces[trace_id]["agents"].append(agent_info)

        # Capture user query from first agent
        if not self.traces[trace_id]["user_query"] and "user_query" in state:
            self.traces[trace_id]["user_query"] = state["user_query"]

        logger.info(
            "agent_entry",
            trace_id=trace_id,
            agent=agent_name,
            user_query=state.get("user_query", "")[:100],
        )

    def log_agent_exit(
        self,
        trace_id: str,
        agent_name: str,
        state: Dict[str, Any],
        tokens_used: Optional[int] = None,
    ) -> None:
        """Log agent exit with output state and metrics.
        
        Args:
            trace_id: Trace identifier
            agent_name: Name of the agent
            state: Current agent state
            tokens_used: Number of tokens used by this agent
        """
        if trace_id not in self.traces:
            logger.warning("trace_not_found", trace_id=trace_id, agent=agent_name)
            return

        trace = self.traces[trace_id]
        
        # Find the matching agent entry
        agent_entry = None
        for agent in reversed(trace["agents"]):
            if agent["name"] == agent_name and "exit_time" not in agent:
                agent_entry = agent
                break

        if not agent_entry:
            logger.warning("agent_entry_not_found", trace_id=trace_id, agent=agent_name)
            return

        # Calculate duration
        exit_time = time.time()
        duration = exit_time - agent_entry["entry_time"]

        agent_entry["exit_time"] = exit_time
        agent_entry["duration"] = duration
        agent_entry["output_state"] = self._sanitize_state(state)

        # Update metrics
        trace["metrics"]["agent_durations"][agent_name] = duration
        agent_duration.labels(agent_name=agent_name).observe(duration)

        if tokens_used:
            trace["metrics"]["token_usage"][agent_name] = tokens_used
            token_usage.labels(agent_name=agent_name, model="claude-sonnet-4").inc(tokens_used)

        # Capture final answer
        if "final_answer" in state and state["final_answer"]:
            trace["final_answer"] = state["final_answer"]
        
        if "metadata" in state and "source" in state["metadata"]:
            trace["source"] = state["metadata"]["source"]

        logger.info(
            "agent_exit",
            trace_id=trace_id,
            agent=agent_name,
            duration_seconds=round(duration, 3),
            tokens_used=tokens_used,
        )

    def end_trace(self, trace_id: str) -> Dict[str, Any]:
        """End a trace and return trace data.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            Complete trace data
        """
        if trace_id not in self.traces:
            logger.warning("trace_not_found", trace_id=trace_id)
            return {}

        trace = self.traces[trace_id]
        trace["end_time"] = time.time()
        trace["metrics"]["total_duration"] = trace["end_time"] - trace["start_time"]

        active_traces.dec()
        logger.info(
            "trace_ended",
            trace_id=trace_id,
            total_duration=round(trace["metrics"]["total_duration"], 3),
        )

        return trace

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get trace data by ID.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            Trace data or None if not found
        """
        return self.traces.get(trace_id)

    def _sanitize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize state for logging (remove large objects).
        
        Args:
            state: Agent state
            
        Returns:
            Sanitized state
        """
        sanitized = {}
        for key, value in state.items():
            if key == "retrieved_docs":
                # Only keep count and first doc preview
                sanitized[key] = {
                    "count": len(value) if isinstance(value, list) else 0,
                    "preview": str(value[0])[:100] if value else None,
                }
            elif isinstance(value, str) and len(value) > 200:
                sanitized[key] = value[:200] + "..."
            else:
                sanitized[key] = value
        return sanitized


class StateInspector:
    """Inspects and tracks agent state transitions."""

    def __init__(self):
        """Initialize the state inspector."""
        self.snapshots: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def snapshot(
        self,
        trace_id: str,
        agent_name: str,
        state: Dict[str, Any],
        stage: str = "entry",
    ) -> None:
        """Take a snapshot of agent state.
        
        Args:
            trace_id: Trace identifier
            agent_name: Name of the agent
            state: Current agent state
            stage: Stage of execution (entry/exit)
        """
        snapshot = {
            "agent": agent_name,
            "stage": stage,
            "timestamp": time.time(),
            "state": dict(state),  # Deep copy
        }

        self.snapshots[trace_id].append(snapshot)

        logger.debug(
            "state_snapshot",
            trace_id=trace_id,
            agent=agent_name,
            stage=stage,
            state_keys=list(state.keys()),
        )

    def get_snapshots(self, trace_id: str) -> List[Dict[str, Any]]:
        """Get all snapshots for a trace.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            List of state snapshots
        """
        return self.snapshots.get(trace_id, [])

    def compute_diff(
        self,
        trace_id: str,
        agent_name: str,
    ) -> Dict[str, Any]:
        """Compute state diff for an agent.
        
        Args:
            trace_id: Trace identifier
            agent_name: Name of the agent
            
        Returns:
            State differences (added/modified/removed keys)
        """
        snapshots = self.snapshots.get(trace_id, [])
        agent_snapshots = [s for s in snapshots if s["agent"] == agent_name]

        if len(agent_snapshots) < 2:
            return {"added": [], "modified": [], "removed": []}

        entry_state = agent_snapshots[0]["state"]
        exit_state = agent_snapshots[-1]["state"]

        added = [k for k in exit_state if k not in entry_state]
        removed = [k for k in entry_state if k not in exit_state]
        modified = [
            k for k in entry_state
            if k in exit_state and entry_state[k] != exit_state[k]
        ]

        return {
            "added": added,
            "modified": modified,
            "removed": removed,
        }


class MetricsCollector:
    """Collects and aggregates metrics across requests."""

    def __init__(self):
        """Initialize the metrics collector."""
        self.request_count = 0
        self.rag_count = 0
        self.general_count = 0
        self.total_duration = 0.0
        self.total_tokens = 0
        self.success_count = 0
        self.error_count = 0

    def record_request(
        self,
        source: str,
        duration: float,
        tokens: int,
        success: bool,
    ) -> None:
        """Record a request.
        
        Args:
            source: Request source (rag/general)
            duration: Request duration in seconds
            tokens: Total tokens used
            success: Whether request succeeded
        """
        self.request_count += 1

        if source == "rag":
            self.rag_count += 1
            routing_decisions.labels(route="rag").inc()
        elif source == "general":
            self.general_count += 1
            routing_decisions.labels(route="general").inc()

        self.total_duration += duration
        self.total_tokens += tokens

        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics.
        
        Returns:
            Metrics dictionary
        """
        return {
            "total_requests": self.request_count,
            "rag_requests": self.rag_count,
            "general_requests": self.general_count,
            "average_response_time": (
                self.total_duration / self.request_count if self.request_count > 0 else 0
            ),
            "success_rate": (
                self.success_count / self.request_count if self.request_count > 0 else 0
            ),
            "total_tokens_used": self.total_tokens,
        }


# Global instances
tracer = AgentTracer()
state_inspector = StateInspector()
metrics_collector = MetricsCollector()
