"""Pydantic models: the LLM output contract and the public API contract.

Two layers of models:

* `Llm*` models define the exact JSON schema Claude is constrained to produce
  (via structured outputs). They stay small and free of server-side bookkeeping.
* The public API models (`ActionItem`, `MeetingAnalysis`, ...) add server-managed
  fields such as stable IDs and status, and are what the frontend consumes.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Priority = Literal["low", "medium", "high"]
ActionStatus = Literal["open", "in_progress", "done"]


# --------------------------------------------------------------------------- #
# LLM output contract (constrained via structured outputs)
# --------------------------------------------------------------------------- #
class LlmActionItem(BaseModel):
    task: str = Field(description="The concrete action to be taken.")
    owner: str | None = Field(
        default=None,
        description="Person responsible, if named in the meeting. Null if unassigned.",
    )
    due_date: str | None = Field(
        default=None,
        description="Due date in ISO-8601 (YYYY-MM-DD) if stated or clearly implied, else null.",
    )
    priority: Priority = Field(
        default="medium",
        description="Relative urgency inferred from the discussion.",
    )


class LlmDecision(BaseModel):
    decision: str = Field(description="A decision that was made in the meeting.")
    rationale: str | None = Field(
        default=None, description="Why the decision was made, if discussed."
    )


class LlmEmail(BaseModel):
    subject: str = Field(description="Subject line for the follow-up email.")
    body: str = Field(
        description="Plain-text follow-up email body summarizing outcomes and next steps."
    )


class LlmAnalysis(BaseModel):
    """The exact shape Claude returns. Keep field order stable for prompt caching."""

    summary: str = Field(description="A concise 3-6 sentence executive summary.")
    key_points: list[str] = Field(
        description="The most important discussion points, as short bullets."
    )
    decisions: list[LlmDecision] = Field(
        description="Concrete decisions made. Empty list if none."
    )
    action_items: list[LlmActionItem] = Field(
        description="Follow-up tasks. Empty list if none."
    )
    risks: list[str] = Field(
        description="Open questions, risks, or blockers raised. Empty list if none."
    )
    follow_up_email: LlmEmail = Field(
        description="A ready-to-send follow-up email to attendees."
    )


# --------------------------------------------------------------------------- #
# Public API models
# --------------------------------------------------------------------------- #
class ActionItem(BaseModel):
    id: str
    task: str
    owner: str | None = None
    due_date: str | None = None
    priority: Priority = "medium"
    status: ActionStatus = "open"


class Decision(BaseModel):
    decision: str
    rationale: str | None = None


class Email(BaseModel):
    subject: str
    body: str


class MeetingAnalysis(BaseModel):
    summary: str
    key_points: list[str]
    decisions: list[Decision]
    action_items: list[ActionItem]
    risks: list[str]
    follow_up_email: Email


class AnalyzeOptions(BaseModel):
    include_email: bool = True


class AnalyzeRequest(BaseModel):
    transcript: str = Field(min_length=1)
    meeting_title: str | None = None
    attendees: list[str] = Field(default_factory=list)
    meeting_date: str | None = None
    options: AnalyzeOptions = Field(default_factory=AnalyzeOptions)


class AnalyzeResponse(BaseModel):
    analysis: MeetingAnalysis
    model: str
    usage: dict[str, int] = Field(default_factory=dict)


class TranscribeResponse(BaseModel):
    transcript: str
    duration_seconds: float | None = None


# --- Export models ---
class ExportItem(BaseModel):
    task: str
    owner: str | None = None
    due_date: str | None = None
    priority: Priority = "medium"


class ExportRequest(BaseModel):
    meeting_title: str | None = None
    action_items: list[ExportItem] = Field(min_length=1)


class ExportedRecord(BaseModel):
    task: str
    external_id: str
    url: str | None = None


class ExportResponse(BaseModel):
    target: Literal["jira", "notion"]
    created: list[ExportedRecord]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    features: dict[str, bool]
