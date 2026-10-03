"""Application entry point for the TravelPilot agent."""

from typing import Any

from langgraph.types import Command

from app.agent.agents.hitl import build_hitl_agent


def build_travel_workflow(next_subgraph=None):
    """Compose HITL with a downstream stage that consumes the shared state."""
    return build_hitl_agent(next_subgraph=next_subgraph)


# Keep one checkpointer-backed workflow alive so a later resume can access the
# state saved by the initial invocation.
_default_workflow = build_travel_workflow()


async def application(
    user_message: str | None = None,
    *,
    thread_id: str,
    resume: Any = None,
    next_subgraph=None,
) -> dict[str, Any]:
    """Run TravelPilot once, or resume a paused HITL conversation.

    A new conversation is started with ``user_message``. 
    When HITL pauses,the returned dictionary contains ``__interrupt__``.  
    Pass the user's answer as ``resume`` with the same ``thread_id`` to continue the graph.
    The thread id is the conversation/session key used by the checkpointer.
    """
    if not thread_id:
        raise ValueError("thread_id is required")

    workflow = (
        _default_workflow
        if next_subgraph is None
        else build_travel_workflow(next_subgraph=next_subgraph)
    )
    config = {"configurable": {"thread_id": thread_id}}

    if resume is not None:
        return await workflow.ainvoke(Command(resume=resume), config)

    if user_message is None or not user_message.strip():
        raise ValueError("user_message is required for a new conversation")

    return await workflow.ainvoke({"user_message": user_message}, config)
