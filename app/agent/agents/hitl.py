"""Human-in-the-loop query understanding agent."""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from app.agent.prompts.hitl_prompt import QUERY_EXTRACTION_PROMPT, extraction_prompt
from app.agent.schemas.agent_schema import HITLState, TripRequest
from app.config import settings


AGENT_NAME = "CLARIFICATION_AGENT"
MAX_QUESTIONS_PER_CALL = 3
MAX_HITL_CALLS = 3

llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL_SMALL,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0,
)
structured_llm = llm.with_structured_output(TripRequest)


async def extract_requirements(state: HITLState) -> dict:
    existing = state["trip"] if "trip" in state else None
    user_message = state["user_message"]
    existing_json = (
        existing.model_dump_json() if existing else "No existing trip state."
    )
    trip = await structured_llm.ainvoke(
        [
            ("system", QUERY_EXTRACTION_PROMPT),
            (
                "human",
                extraction_prompt(existing_json, user_message),
            ),
        ]
    )
    return {"trip": trip}


def check_completeness(state: HITLState) -> dict:
    trip = state["trip"]
    missing: list[str] = []

    if not trip.origin:
        missing.append("origin")
    if not trip.destination and not trip.destination_type and not trip.region:
        missing.append("destination_or_preferences")
    if not trip.start_date and not trip.travel_month:
        missing.append("travel_period")
    if not trip.duration_days:
        missing.append("duration_days")
    if not trip.travellers:
        missing.append("travellers")
    if not trip.budget:
        missing.append("budget")

    questions = {
        "origin": "Where will you be travelling from?",
        "destination_or_preferences": (
            "Do you have a destination in mind, or what kind of destination "
            "would you prefer?"
        ),
        "travel_period": "When would you like to travel?",
        "duration_days": "How many days should the trip be?",
        "travellers": "How many adults and children are travelling?",
        "budget": "What is your approximate total trip budget?",
    }
    trip.missing_fields = missing
    clarification_questions = [
        questions[field] for field in missing[:MAX_QUESTIONS_PER_CALL]
    ]
    trip.clarification_questions = clarification_questions
    trip.clarification_question = (
        clarification_questions[0] if clarification_questions else None
    )
    trip.planning_stage = "clarification" if missing else (
        "destination_discovery" if not trip.destination else "research"
    )

    return {
        "trip": trip,
        "status": "needs_clarification" if missing else "ready_for_research",
        "questions": clarification_questions,
    }


async def request_clarification(state: HITLState) -> dict:
    questions = state["questions"]
    trip = state["trip"]
    hitl_calls = state["hitl_calls"] if "hitl_calls" in state else 0

    answer = interrupt(
        {
            "agent": AGENT_NAME,
            "type": "clarification",
            "questions": questions,
            "trip": trip.model_dump(mode="json"),
        }
    )
    return {
        "user_message": str(answer),
        "status": "resuming",
        "hitl_calls": hitl_calls + 1,
    }


def route_after_check(state: HITLState) -> str:
    if state["status"] != "needs_clarification":
        return "complete"

    hitl_calls = state["hitl_calls"] if "hitl_calls" in state else 0
    if hitl_calls >= MAX_HITL_CALLS:
        return "limit"
    return "clarify"


def clarification_limit_reached(state: HITLState) -> dict:
    return {
        "status": "clarification_limit_reached",
        "questions": [],
    }


def build_hitl_agent(next_subgraph=None):
    """Build HITL and optionally hand complete state to the next stage."""
    graph = StateGraph(HITLState)
    graph.add_node("extract_requirements", extract_requirements)
    graph.add_node("check_completeness", check_completeness)
    graph.add_node("request_clarification", request_clarification)
    graph.add_node("clarification_limit_reached", clarification_limit_reached)
    complete_target = END
    if next_subgraph is not None:
        graph.add_node("next_subgraph", next_subgraph)
        complete_target = "next_subgraph"
    graph.add_edge(START, "extract_requirements")
    graph.add_edge("extract_requirements", "check_completeness")
    graph.add_conditional_edges(
        "check_completeness",
        route_after_check,
        {
            "clarify": "request_clarification",
            "complete": complete_target,
            "limit": "clarification_limit_reached",
        },
    )
    graph.add_edge("clarification_limit_reached", END)
    graph.add_edge("request_clarification", "extract_requirements")
    if next_subgraph is not None:
        graph.add_edge("next_subgraph", END)
    return graph.compile(checkpointer=MemorySaver())


hitl_agent = build_hitl_agent()
