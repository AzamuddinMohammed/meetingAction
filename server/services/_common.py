"""Shared analysis helpers used by every provider.

Keeping the LLM→public mapping and the analysis Protocol here lets the Anthropic
and OpenRouter providers stay small and interchangeable.
"""

from __future__ import annotations

from typing import Protocol

from ..schemas import (
    ActionItem,
    AnalyzeRequest,
    Decision,
    Email,
    LlmAnalysis,
    MeetingAnalysis,
)


class AnalysisProvider(Protocol):
    """Any meeting-analysis backend (Anthropic direct, OpenRouter, ...)."""

    async def analyze(
        self, req: AnalyzeRequest
    ) -> tuple[MeetingAnalysis, dict[str, int]]: ...


def to_public_analysis(llm: LlmAnalysis) -> MeetingAnalysis:
    """Map raw LLM output onto public models, assigning stable action-item IDs."""
    action_items = [
        ActionItem(
            id=f"ai-{index}",
            task=item.task,
            owner=item.owner,
            due_date=item.due_date,
            priority=item.priority,
        )
        for index, item in enumerate(llm.action_items, start=1)
    ]
    decisions = [Decision(decision=d.decision, rationale=d.rationale) for d in llm.decisions]
    return MeetingAnalysis(
        summary=llm.summary,
        key_points=llm.key_points,
        decisions=decisions,
        action_items=action_items,
        risks=llm.risks,
        follow_up_email=Email(
            subject=llm.follow_up_email.subject,
            body=llm.follow_up_email.body,
        ),
    )
