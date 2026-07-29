"""Claude-backed meeting analysis.

Uses the Anthropic Python SDK's structured-output parsing (`messages.parse`) so
the model is constrained to the `LlmAnalysis` schema and the response is returned
as a validated Pydantic object — no manual JSON parsing.
"""

from __future__ import annotations

import logging

import anthropic

from ..config import Settings
from ..errors import ContentRefusedError, FeatureUnavailableError, UpstreamError
from ..prompts import SYSTEM_PROMPT, build_user_prompt
from ..schemas import (
    ActionItem,
    AnalyzeRequest,
    Decision,
    Email,
    LlmAnalysis,
    MeetingAnalysis,
)

logger = logging.getLogger(__name__)


class ClaudeService:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: anthropic.AsyncAnthropic | None = None
        if settings.claude_configured:
            self._client = anthropic.AsyncAnthropic(
                api_key=settings.anthropic_api_key,
                timeout=settings.request_timeout_seconds,
            )

    async def analyze(self, req: AnalyzeRequest) -> tuple[MeetingAnalysis, dict[str, int]]:
        if self._client is None:
            raise FeatureUnavailableError(
                "Meeting analysis is unavailable: ANTHROPIC_API_KEY is not configured."
            )

        try:
            response = await self._client.messages.parse(
                model=self._settings.claude_model,
                max_tokens=self._settings.analysis_max_tokens,
                system=SYSTEM_PROMPT,
                output_config={"effort": self._settings.analysis_effort},
                output_format=LlmAnalysis,
                messages=[{"role": "user", "content": build_user_prompt(req)}],
            )
        except anthropic.APIStatusError as exc:  # 4xx/5xx from the API
            logger.warning("Claude API error (%s): %s", exc.status_code, exc.message)
            raise UpstreamError(
                f"The analysis provider returned an error ({exc.status_code})."
            ) from exc
        except anthropic.APIConnectionError as exc:
            logger.warning("Claude connection error: %s", exc)
            raise UpstreamError("Could not reach the analysis provider.") from exc

        if response.stop_reason == "refusal":
            raise ContentRefusedError(
                "The model declined to analyze this transcript."
            )

        parsed = response.parsed_output
        if parsed is None:
            logger.error("Claude returned no parseable structured output")
            raise UpstreamError("The analysis provider returned an unusable response.")

        analysis = _to_public_analysis(parsed)
        usage = _extract_usage(response)
        return analysis, usage


def _to_public_analysis(llm: LlmAnalysis) -> MeetingAnalysis:
    """Map the raw LLM output onto public models, assigning stable action-item IDs."""
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


def _extract_usage(response: object) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    result: dict[str, int] = {}
    for field in ("input_tokens", "output_tokens"):
        value = getattr(usage, field, None)
        if isinstance(value, int):
            result[field] = value
    return result
