"""Schemas shared by the TravelPilot HITL agent."""

from datetime import date
from typing import Any, Literal, NotRequired, Required, TypedDict

from pydantic import BaseModel, Field


class Travellers(BaseModel):
    adults: int = Field(default=1, ge=1)
    children: int = Field(default=0, ge=0)


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class BudgetRequest(BaseModel):
    amount: int = Field(ge=0)
    currency: str = "INR"
    includes_intercity_transport: bool | None = None
    hard_limit: bool = True


class TripRequest(BaseModel):
    original_query: str

    origin: str | None = None
    destination: str | None = None
    destination_type: str | None = None
    region: str | None = None

    start_date: date | None = None
    end_date: date | None = None
    travel_month: int | None = Field(default=None, ge=1, le=12)
    duration_days: int | None = Field(default=None, ge=1)

    travellers: Travellers | None = None
    budget: BudgetRequest | None = None

    interests: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    transport_preferences: list[str] = Field(default_factory=list)

    origin_coordinates: Coordinates | None = None
    destination_coordinates: Coordinates | None = None

    missing_fields: list[str] = Field(default_factory=list)
    clarification_question: str | None = None
    clarification_questions: list[str] = Field(default_factory=list)
    planning_stage: Literal[
        "clarification",
        "destination_discovery",
        "research",
        "complete",
    ] = "clarification"


class HITLState(TypedDict, total=False):
    user_message: Required[str]
    trip: NotRequired[TripRequest]
    status: NotRequired[str]
    questions: NotRequired[list[str]]
    hitl_calls: NotRequired[int]
    workflow_data: NotRequired[dict[str, Any]]
